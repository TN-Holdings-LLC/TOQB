//! Sparse Pauli dynamics (SPD) for <Z_q> of P5's circuit: |0...0> in, `t` steps of (RZZ(-pi/2) on every lattice
//! edge, then RX(theta) on every qubit), Z readout. Heisenberg picture: Z_q is carried back through the steps, and a
//! Pauli term whose coefficient falls below `delta` is dropped. A port of TOQB gpu/spd_proto.py with the same rules:
//!   RX(theta) conjugation: Z -> cos Z + sin Y, Y -> cos Y - sin Z (X unchanged); branches below delta dropped as
//!     they are made, then the merged terms below delta dropped;
//!   RZZ(-pi/2) conjugation on an edge whose two qubits differ in their X part: on the X side, X -> Y Z, Y -> -X Z
//!     (the other qubit gains Z); exact, no truncation;
//!   the first step's RZZ layer acts on |0...0> as a phase and is left out;
//!   <0...0| P |0...0> is 1 for a Z-only string and 0 otherwise.
//! Qubits up to 192 (three 64-bit words for each of the X and Z parts).

pub mod layers;

use std::collections::HashMap;
use std::hash::{BuildHasherDefault, Hasher};

pub const W: usize = 3;
pub const MAXQ: usize = 64 * W;

/// A Pauli string as (X bits, Z bits): I (0, 0), X (1, 0), Y (1, 1), Z (0, 1).
#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug, Default)]
pub struct P {
    pub x: [u64; W],
    pub z: [u64; W],
}

impl P {
    #[inline]
    fn xb(&self, q: usize) -> bool {
        (self.x[q >> 6] >> (q & 63)) & 1 == 1
    }
    #[inline]
    fn zb(&self, q: usize) -> bool {
        (self.z[q >> 6] >> (q & 63)) & 1 == 1
    }
    #[inline]
    fn flip_x(&mut self, q: usize) {
        self.x[q >> 6] ^= 1 << (q & 63);
    }
    #[inline]
    fn flip_z(&mut self, q: usize) {
        self.z[q >> 6] ^= 1 << (q & 63);
    }
    fn x_is_zero(&self) -> bool {
        self.x.iter().all(|w| *w == 0)
    }
}

/// A small multiplicative hasher (FxHash's constant); the keys are bit strings, so no DoS concern here.
#[derive(Default)]
pub struct Fx(u64);
impl Hasher for Fx {
    fn finish(&self) -> u64 {
        self.0
    }
    fn write(&mut self, bytes: &[u8]) {
        for b in bytes {
            self.0 = (self.0.rotate_left(5) ^ (*b as u64)).wrapping_mul(0x51_7c_c1_b7_27_22_0a_95);
        }
    }
    fn write_u64(&mut self, i: u64) {
        self.0 = (self.0.rotate_left(5) ^ i).wrapping_mul(0x51_7c_c1_b7_27_22_0a_95);
    }
}
pub type Map = HashMap<P, f64, BuildHasherDefault<Fx>>;

/// Conjugation by RX(theta) on every qubit, with truncation (as spd_proto.rx_layer).
pub fn rx_layer(terms: &Map, c: f64, s: f64, delta: f64) -> Map {
    let mut out: Map = Map::with_capacity_and_hasher(terms.len() * 2, Default::default());
    let mut br: Vec<(P, f64)> = Vec::new();
    let mut nb: Vec<(P, f64)> = Vec::new();
    for (p, &w) in terms.iter() {
        br.clear();
        br.push((*p, w));
        for k in 0..W {
            let mut zs = p.z[k];
            while zs != 0 {
                let q = (k << 6) + zs.trailing_zeros() as usize;
                zs &= zs - 1;
                nb.clear();
                for (bp, bw) in br.iter() {
                    let (a1, mut a2) = ((*bp, bw * c), (*bp, 0.0));
                    if bp.xb(q) {
                        // Y -> c Y - s Z
                        a2.0.flip_x(q);
                        a2.1 = -bw * s;
                    } else {
                        // Z -> c Z + s Y
                        a2.0.flip_x(q);
                        a2.1 = bw * s;
                    }
                    if a1.1.abs() >= delta {
                        nb.push(a1);
                    }
                    if a2.1.abs() >= delta {
                        nb.push(a2);
                    }
                }
                std::mem::swap(&mut br, &mut nb);
                if br.is_empty() {
                    break;
                }
            }
            if br.is_empty() {
                break;
            }
        }
        for (bp, bw) in br.iter() {
            *out.entry(*bp).or_insert(0.0) += *bw;
        }
    }
    out.retain(|_, v| v.abs() >= delta);
    out
}

/// Conjugation by RZZ(-pi/2) on every edge (exact). `adj[q]` lists q's neighbours.
pub fn zz_layer(terms: &Map, adj: &[Vec<usize>]) -> Map {
    let mut out: Map = Map::with_capacity_and_hasher(terms.len(), Default::default());
    for (p, &w0) in terms.iter() {
        let mut np = *p;
        let mut w = w0;
        for k in 0..W {
            let mut xs = p.x[k];
            while xs != 0 {
                let q = (k << 6) + xs.trailing_zeros() as usize;
                xs &= xs - 1;
                for &b in &adj[q] {
                    if !p.xb(b) {
                        // edge (q, b) with X on q only: X -> Y Z (+), Y -> -X Z (-), sign read before the flip
                        if np.zb(q) {
                            w = -w;
                        }
                        np.flip_z(q);
                        np.flip_z(b);
                    }
                }
            }
        }
        *out.entry(np).or_insert(0.0) += w;
    }
    out
}

pub struct Run {
    pub value: f64,
    pub peak: usize,
    pub capped: bool,
}

/// <Z_q> after `t` steps, with truncation `delta`; stops (capped) if the term count exceeds `cap`.
pub fn z_expect(q: usize, adj: &[Vec<usize>], theta: f64, t: usize, delta: f64, cap: usize) -> Run {
    assert!(q < MAXQ);
    let mut p = P::default();
    p.flip_z(q);
    let mut terms: Map = Map::default();
    terms.insert(p, 1.0);
    let (c, s) = (theta.cos(), theta.sin());
    let mut peak = 1;
    for step in (1..=t).rev() {
        terms = rx_layer(&terms, c, s, delta);
        if step > 1 {
            terms = zz_layer(&terms, adj);
        }
        peak = peak.max(terms.len());
        if terms.len() > cap {
            return Run { value: f64::NAN, peak, capped: true };
        }
    }
    let value = terms.iter().filter(|(p, _)| p.x_is_zero()).map(|(_, w)| *w).sum();
    Run { value, peak, capped: false }
}

pub fn adjacency(nq: usize, edges: &[(usize, usize)]) -> Vec<Vec<usize>> {
    let mut adj = vec![Vec::new(); nq];
    for &(a, b) in edges {
        adj[a].push(b);
        adj[b].push(a);
    }
    adj
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A plain statevector of n <= 12 qubits for the same circuit (RZZ(-pi/2) = exp(+i pi/4 ZZ) on every edge, then
    /// RX(theta) on every qubit, t steps, the first RZZ layer included), returning <Z_q> for every q.
    fn statevector(n: usize, edges: &[(usize, usize)], theta: f64, t: usize) -> Vec<f64> {
        let dim = 1usize << n;
        let mut re = vec![0.0; dim];
        let mut im = vec![0.0; dim];
        re[0] = 1.0;
        let (c, s) = ((theta / 2.0).cos(), (theta / 2.0).sin());
        for _ in 0..t {
            for &(a, b) in edges {
                for i in 0..dim {
                    let par = ((i >> a) ^ (i >> b)) & 1;
                    // exp(+i pi/4 ZZ): phase e^{+i pi/4} if equal bits, e^{-i pi/4} if different
                    let ph = if par == 0 { std::f64::consts::FRAC_PI_4 } else { -std::f64::consts::FRAC_PI_4 };
                    let (cr, ci) = (ph.cos(), ph.sin());
                    let (r, m) = (re[i], im[i]);
                    re[i] = r * cr - m * ci;
                    im[i] = r * ci + m * cr;
                }
            }
            for q in 0..n {
                // RX(theta) = [[c, -i s], [-i s, c]]
                for i in 0..dim {
                    if (i >> q) & 1 == 0 {
                        let j = i | (1 << q);
                        let (r0, m0, r1, m1) = (re[i], im[i], re[j], im[j]);
                        re[i] = c * r0 + s * m1;
                        im[i] = c * m0 - s * r1;
                        re[j] = c * r1 + s * m0;
                        im[j] = c * m1 - s * r0;
                    }
                }
            }
        }
        (0..n)
            .map(|q| (0..dim).map(|i| (re[i] * re[i] + im[i] * im[i]) * if (i >> q) & 1 == 0 { 1.0 } else { -1.0 }).sum())
            .collect()
    }

    fn check(n: usize, edges: &[(usize, usize)]) {
        let adj = adjacency(n, edges);
        for &theta in &[0.4, 0.8, 1.0, 1.3] {
            for t in 1..=5 {
                let sv = statevector(n, edges, theta, t);
                for q in 0..n {
                    let r = z_expect(q, &adj, theta, t, 0.0, usize::MAX);
                    assert!((r.value - sv[q]).abs() < 1e-10, "n {} theta {} t {} q {}: {} vs {}", n, theta, t, q, r.value, sv[q]);
                }
            }
        }
    }

    #[test]
    fn chain_matches_statevector() {
        check(6, &[(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]);
    }

    #[test]
    fn heavy_hex_piece_matches_statevector() {
        // a ring of 8 with one pendant and one high qubit index (word boundary): qubits 0..9 relabelled below
        let e = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 0), (2, 8), (8, 9)];
        check(10, &e);
    }

    #[test]
    fn words_beyond_64_work() {
        // the same chain placed on qubits 60..65 and 126..131 gives the same values as on 0..5
        let base: Vec<(usize, usize)> = (0..5).map(|i| (i, i + 1)).collect();
        for off in [60usize, 126] {
            let e: Vec<(usize, usize)> = base.iter().map(|&(a, b)| (a + off, b + off)).collect();
            let adj = adjacency(off + 6, &e);
            let adj0 = adjacency(6, &base);
            for q in 0..6 {
                let a = z_expect(q + off, &adj, 0.9, 4, 0.0, usize::MAX).value;
                let b = z_expect(q, &adj0, 0.9, 4, 0.0, usize::MAX).value;
                assert!((a - b).abs() < 1e-12);
            }
        }
    }

    #[test]
    fn truncation_only_drops_small_terms() {
        let e: Vec<(usize, usize)> = (0..7).map(|i| (i, i + 1)).collect();
        let adj = adjacency(8, &e);
        let exact = z_expect(3, &adj, 0.8, 5, 0.0, usize::MAX);
        let tr = z_expect(3, &adj, 0.8, 5, 1e-3, usize::MAX);
        assert!(tr.peak <= exact.peak);
        assert!((tr.value - exact.value).abs() < 0.05);
    }
}

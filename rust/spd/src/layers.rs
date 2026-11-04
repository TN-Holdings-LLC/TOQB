//! General layered circuits for SPD: each step is a list of layers, each layer one of
//!   Rx(theta) on every listed qubit, Rz(phi) on every listed qubit, Rzz(theta) on a matching of edges.
//! Conjugation rules (U^dagger P U, Heisenberg picture), with truncation `delta` on every branch made:
//!   RX(theta) = exp(-i theta X / 2): Z -> cos Z + sin Y, Y -> cos Y - sin Z;
//!   RZ(phi)   = exp(-i phi Z / 2):   X -> cos X - sin Y, Y -> cos Y + sin X;
//!   RZZ(theta) = exp(-i theta Z Z / 2), on an edge where P anticommutes with Z Z (one side X or Y):
//!     P -> cos P - i sin P Z Z, i.e. X side: (P with both Z bits flipped, -sin), Y side: (same, +sin).
//! At theta = -pi/2 the RZZ rule is P5's (X -> Y Z, Y -> -X Z). Used for P6 (RZZ(1.0): branches on ZZ as well).

use crate::{Map, P};

#[derive(Clone, Debug)]
pub enum Layer {
    Rx(f64, Vec<usize>),
    Rz(f64, Vec<usize>),
    Rzz(f64, Vec<(usize, usize)>),
}

#[inline]
fn bit(w: &[u64; 3], q: usize) -> bool {
    (w[q >> 6] >> (q & 63)) & 1 == 1
}
#[inline]
fn flip(w: &mut [u64; 3], q: usize) {
    w[q >> 6] ^= 1 << (q & 63);
}

/// One layer's conjugation, every branch below delta dropped as it is made, merged terms below delta dropped.
pub fn conj_layer(terms: &Map, layer: &Layer, delta: f64) -> Map {
    let mut out: Map = Map::with_capacity_and_hasher(terms.len() * 2, Default::default());
    let mut br: Vec<(P, f64)> = Vec::new();
    let mut nb: Vec<(P, f64)> = Vec::new();
    for (p, &w) in terms.iter() {
        br.clear();
        br.push((*p, w));
        let mut split = |br: &mut Vec<(P, f64)>, nb: &mut Vec<(P, f64)>, f: &dyn Fn(&P) -> Option<(P, f64, f64)>| {
            nb.clear();
            for (bp, bw) in br.iter() {
                match f(bp) {
                    None => nb.push((*bp, *bw)),
                    Some((p2, c1, c2)) => {
                        let (w1, w2) = (bw * c1, bw * c2);
                        if w1.abs() >= delta {
                            nb.push((*bp, w1));
                        }
                        if w2.abs() >= delta {
                            nb.push((p2, w2));
                        }
                    }
                }
            }
            std::mem::swap(br, nb);
        };
        match layer {
            Layer::Rx(th, qs) => {
                let (c, s) = (th.cos(), th.sin());
                for &q in qs {
                    if !bit(&p.z, q) {
                        continue;
                    }
                    split(&mut br, &mut nb, &|bp: &P| {
                        let mut p2 = *bp;
                        flip(&mut p2.x, q);
                        Some((p2, c, if bit(&bp.x, q) { -s } else { s }))
                    });
                    if br.is_empty() {
                        break;
                    }
                }
            }
            Layer::Rz(ph, qs) => {
                let (c, s) = (ph.cos(), ph.sin());
                for &q in qs {
                    if !bit(&p.x, q) {
                        continue;
                    }
                    split(&mut br, &mut nb, &|bp: &P| {
                        let mut p2 = *bp;
                        flip(&mut p2.z, q);
                        // X (z = 0) -> c X - s Y; Y (z = 1) -> c Y + s X
                        Some((p2, c, if bit(&bp.z, q) { s } else { -s }))
                    });
                    if br.is_empty() {
                        break;
                    }
                }
            }
            Layer::Rzz(th, edges) => {
                let (c, s) = (th.cos(), th.sin());
                for &(a, b) in edges {
                    let (xa, xb) = (bit(&p.x, a), bit(&p.x, b));
                    if xa == xb {
                        continue;
                    }
                    let side = if xa { a } else { b };
                    split(&mut br, &mut nb, &|bp: &P| {
                        let mut p2 = *bp;
                        let y = bit(&bp.z, side);
                        flip(&mut p2.z, a);
                        flip(&mut p2.z, b);
                        Some((p2, c, if y { s } else { -s }))
                    });
                    if br.is_empty() {
                        break;
                    }
                }
            }
        }
        for (bp, bw) in br.iter() {
            *out.entry(*bp).or_insert(0.0) += *bw;
        }
    }
    out.retain(|_, v| v.abs() >= delta);
    out
}

/// <Z_q> after `t` steps of `step` (layers in time order) on |0...0>.
pub fn z_expect_layers(q: usize, step: &[Layer], t: usize, delta: f64, cap: usize) -> crate::Run {
    let mut p = P::default();
    p.z[q >> 6] |= 1 << (q & 63);
    let mut terms: Map = Map::default();
    terms.insert(p, 1.0);
    let mut peak = 1;
    for _ in 0..t {
        for layer in step.iter().rev() {
            terms = conj_layer(&terms, layer, delta);
            peak = peak.max(terms.len());
            if terms.len() > cap {
                return crate::Run { value: f64::NAN, peak, capped: true };
            }
        }
    }
    let value = terms.iter().filter(|(p, _)| p.x.iter().all(|w| *w == 0)).map(|(_, w)| *w).sum();
    crate::Run { value, peak, capped: false }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Plain statevector of a layered circuit (n <= 12), <Z_q> for every q.
    fn sv(n: usize, step: &[Layer], t: usize) -> Vec<f64> {
        let dim = 1usize << n;
        let mut re = vec![0.0; dim];
        let mut im = vec![0.0; dim];
        re[0] = 1.0;
        let rot = |re: &mut Vec<f64>, im: &mut Vec<f64>, i: usize, ph: f64| {
            let (c, s) = (ph.cos(), ph.sin());
            let (r, m) = (re[i], im[i]);
            re[i] = r * c - m * s;
            im[i] = r * s + m * c;
        };
        for _ in 0..t {
            for layer in step {
                match layer {
                    Layer::Rx(th, qs) => {
                        let (c, s) = ((th / 2.0).cos(), (th / 2.0).sin());
                        for &q in qs {
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
                    Layer::Rz(ph, qs) => {
                        for &q in qs {
                            for i in 0..dim {
                                let z = if (i >> q) & 1 == 0 { 1.0 } else { -1.0 };
                                rot(&mut re, &mut im, i, -ph / 2.0 * z);
                            }
                        }
                    }
                    Layer::Rzz(th, es) => {
                        for &(a, b) in es {
                            for i in 0..dim {
                                let zz = if ((i >> a) ^ (i >> b)) & 1 == 0 { 1.0 } else { -1.0 };
                                rot(&mut re, &mut im, i, -th / 2.0 * zz);
                            }
                        }
                    }
                }
            }
        }
        (0..n)
            .map(|q| (0..dim).map(|i| (re[i] * re[i] + im[i] * im[i]) * if (i >> q) & 1 == 0 { 1.0 } else { -1.0 }).sum())
            .collect()
    }

    fn check(n: usize, step: Vec<Layer>, tmax: usize) {
        for t in 1..=tmax {
            let want = sv(n, &step, t);
            for q in 0..n {
                let r = z_expect_layers(q, &step, t, 0.0, usize::MAX);
                assert!((r.value - want[q]).abs() < 1e-10, "t {} q {}: {} vs {}", t, q, r.value, want[q]);
            }
        }
    }

    #[test]
    fn p6_shaped_layers_match_statevector() {
        // a 3 x 3 grid-like piece with three matchings, the P6 angles
        let all: Vec<usize> = (0..9).collect();
        let step = vec![
            Layer::Rx(0.53, all.clone()),
            Layer::Rz(0.1, all.clone()),
            Layer::Rzz(1.0, vec![(0, 1), (3, 4), (6, 7)]),
            Layer::Rzz(1.0, vec![(1, 2), (4, 5), (7, 8)]),
            Layer::Rzz(1.0, vec![(0, 3), (4, 7), (2, 5)]),
        ];
        check(9, step, 4);
    }

    #[test]
    fn p5_rule_is_the_special_case() {
        // RZZ(-pi/2) then RX(theta) per step, on a chain: equals the P5 code (first RZZ layer dropped there is a phase)
        let e: Vec<(usize, usize)> = (0..5).map(|i| (i, i + 1)).collect();
        let adj = crate::adjacency(6, &e);
        let step = vec![Layer::Rzz(-std::f64::consts::FRAC_PI_2, e.clone()), Layer::Rx(0.8, (0..6).collect())];
        for q in 0..6 {
            let a = z_expect_layers(q, &step, 4, 0.0, usize::MAX).value;
            let b = crate::z_expect(q, &adj, 0.8, 4, 0.0, usize::MAX).value;
            assert!((a - b).abs() < 1e-12, "q {}: {} vs {}", q, a, b);
        }
    }
}

#![allow(non_snake_case)]
//! Exact cost-to-go h*(layout, done) for the ring-on-a-line CZ problem (analysis only): reverse Dijkstra from every
//! goal state (all ring edges done). Moves: CZ on an undone adjacent ring edge (0), CZ+SWAP on it (1), SWAP (3).
//! Writes h* for every state as bytes (index = perm_rank * 2^n + done) to hstar_N.bin.
use std::env;
use std::io::Write;

fn costs() -> (usize, usize) { let a: Vec<usize> = env::args().skip(2).map(|s| s.parse().unwrap()).collect(); (a[0], a[1]) }

fn fact(n: usize) -> usize { (1..=n).product() }
fn rank(p: &[usize]) -> usize {
    let n = p.len(); let mut r = 0; let mut used = vec![false; n];
    for i in 0..n { let mut c = 0; for v in 0..p[i] { if !used[v] { c += 1; } } r = r * (n - i) + c; used[p[i]] = true; }
    r
}
fn unrank(mut r: usize, n: usize) -> Vec<usize> {
    let mut digits = vec![0; n];
    for i in (0..n).rev() { let b = n - i; digits[i] = r % b; r /= b; }
    let mut avail: Vec<usize> = (0..n).collect(); let mut p = vec![0; n];
    for i in 0..n { p[i] = avail.remove(digits[i]); }
    p
}
fn main() {
    let n: usize = env::args().nth(1).unwrap().parse().unwrap();
    let (CZSC, SWAPC) = costs();
    // HSTAR_RELAX=1: ring neighbours adjacent on the line may also swap at cost 0 without a CZ (relaxed L1)
    let relax_mode = env::var("HSTAR_RELAX").map(|v| v == "1").unwrap_or(false);
    let nf = fact(n); let nd = 1usize << n; let full = nd - 1;
    let eid = |a: usize, b: usize| -> i32 { if (a + 1) % n == b { a as i32 } else if (b + 1) % n == a { b as i32 } else { -1 } };
    let mut dist = vec![255u8; nf * nd];
    let mut buckets: Vec<Vec<u32>> = vec![Vec::new(); 256];
    for r in 0..nf { dist[r * nd + full] = 0; buckets[0].push((r * nd + full) as u32); }
    let mut d = 0usize;
    while d < 256 {
        while let Some(s) = buckets[d].pop() {
            let s = s as usize; if dist[s] as usize != d { continue; }
            let (r, dn) = (s / nd, s % nd); let l = unrank(r, n);
            for p in 0..n - 1 {
                let (x, y) = (l[p], l[p + 1]); let e = eid(x, y);
                let mut l2 = l.clone(); l2.swap(p, p + 1); let r2 = rank(&l2);
                let relax = |t: usize, c: usize, dist: &mut Vec<u8>, buckets: &mut Vec<Vec<u32>>| {
                    let nd2 = d + c; if nd2 < dist[t] as usize { dist[t] = nd2 as u8; buckets[nd2].push(t as u32); }
                };
                if e >= 0 && dn >> e & 1 == 1 {
                    relax(r * nd + (dn & !(1 << e)), 0, &mut dist, &mut buckets);
                    relax(r2 * nd + (dn & !(1 << e)), CZSC, &mut dist, &mut buckets);
                }
                relax(r2 * nd + dn, SWAPC, &mut dist, &mut buckets);
                if relax_mode && e >= 0 { relax(r2 * nd + dn, 0, &mut dist, &mut buckets); }
            }
        }
        d += 1;
    }
    let mut best = 255u8; let mut arg = vec![];
    for r in 0..nf { let v = dist[r * nd]; if v < best { best = v; arg.clear(); } if v == best { arg.push(r); } }
    println!("n {} min h*(layout, none done) = {} at {} layouts, e.g. {:?}", n, best, arg.len(), unrank(arg[0], n));
    std::fs::File::create(format!("hstar_{}_{}_{}.bin", n, CZSC, SWAPC)).unwrap().write_all(&dist).unwrap();
}

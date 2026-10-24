//! Rust port of results/zipper-P1-2026-10-22/bound.py (analysis only, 2026-10-24): the least extra CZ cost of one
//! layer of an n-qubit CZ ring on a line of n qubits, from every start layout of minimum total ring length (the same
//! restriction as bound.py). Moves on adjacent positions: CZ on an undone ring edge (extra 0), CZ+SWAP on an undone
//! ring edge (extra 1, locally an iSWAP), plain SWAP (extra 3). IDA* with the admissible bound ceil(Phi / 2), Phi =
//! sum over undone ring edges of (line distance - 1), and a transposition table per iteration, as in bound.py.
//!
//!     zipper_bound N [LIMIT]
//!
//! Prints, per start layout, the least extra cost found up to LIMIT (default 3n), then the minimum and its schedule.
use std::collections::HashMap;
use std::env;

struct S {
    n: usize,
    edges: Vec<(usize, usize)>,
    eid: Vec<Vec<i32>>,
    full: u32,
    seen: HashMap<(u64, u32), u32>,
    path: Vec<(u8, usize, usize, usize)>,
    best: Option<Vec<(u8, usize, usize, usize)>>,
}

fn pack(line: &[usize]) -> u64 {
    line.iter().fold(0u64, |a, &q| (a << 4) | q as u64)
}

impl S {
    fn phi(&self, pos: &[usize], done: u32) -> u32 {
        let mut s = 0u32;
        for (k, &(a, b)) in self.edges.iter().enumerate() {
            if done >> k & 1 == 0 {
                s += (pos[a] as i32 - pos[b] as i32).unsigned_abs() - 1;
            }
        }
        s
    }

    fn dfs(&mut self, line: &mut Vec<usize>, pos: &mut Vec<usize>, done: u32, g: u32, bound: u32) -> u32 {
        let h = (self.phi(pos, done) + 1) / 2;
        if g + h > bound {
            return g + h;
        }
        if done == self.full {
            self.best = Some(self.path.clone());
            return u32::MAX - 1; // found
        }
        let key = (pack(line), done);
        if let Some(&gs) = self.seen.get(&key) {
            if gs <= g {
                return u32::MAX;
            }
        }
        self.seen.insert(key, g);
        let mut nxt = u32::MAX;
        for p in 0..self.n - 1 {
            let (x, y) = (line[p], line[p + 1]);
            let k = self.eid[x][y];
            let mut cands: Vec<(u8, u32, u32, bool)> = Vec::new();
            if k >= 0 && done >> k & 1 == 0 {
                cands.push((0, 0, done | 1 << k, false));
                cands.push((1, 1, done | 1 << k, true));
            }
            cands.push((2, 3, done, true));
            for (name, c, nd, sw) in cands {
                if sw {
                    line.swap(p, p + 1);
                    pos[x] = p + 1;
                    pos[y] = p;
                }
                self.path.push((name, p, x, y));
                let r = self.dfs(line, pos, nd, g + c, bound);
                self.path.pop();
                if sw {
                    line.swap(p, p + 1);
                    pos[x] = p;
                    pos[y] = p + 1;
                }
                if r == u32::MAX - 1 {
                    return r;
                }
                nxt = nxt.min(r);
            }
        }
        nxt
    }
}

fn start_layouts(n: usize) -> Vec<Vec<usize>> {
    let mut out: Vec<Vec<usize>> = Vec::new();
    for m in 1..n {
        let a: Vec<usize> = (1..m).collect();
        let b: Vec<usize> = (m + 1..n).rev().collect();
        let tot = a.len() + b.len();
        for mask in 0u32..(1u32 << tot) {
            if mask.count_ones() as usize != a.len() {
                continue;
            }
            let (mut ia, mut ib) = (0, 0);
            let mut seq = vec![0];
            for k in 0..tot {
                if mask >> k & 1 == 1 {
                    seq.push(a[ia]);
                    ia += 1;
                } else {
                    seq.push(b[ib]);
                    ib += 1;
                }
            }
            seq.push(m);
            if !out.contains(&seq) {
                out.push(seq);
            }
        }
    }
    out.sort();
    out
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let n: usize = args[1].parse().unwrap();
    let mut limit: u32 = args.get(2).map(|s| s.parse().unwrap()).unwrap_or(3 * n as u32);
    let edges: Vec<(usize, usize)> = (0..n).map(|i| (i, (i + 1) % n)).collect();
    let mut eid = vec![vec![-1i32; n]; n];
    for (k, &(a, b)) in edges.iter().enumerate() {
        eid[a][b] = k as i32;
        eid[b][a] = k as i32;
    }
    let mut s = S { n, edges, eid, full: (1u32 << n) - 1, seen: HashMap::new(), path: vec![], best: None };
    let lays = start_layouts(n);
    // Optional shard "k/K" (2026-10-25): only the start layouts with index i % K == k, so that several processes can
    // share one n; the limit is then not lowered by results found in other shards.
    let (shard, nshard): (usize, usize) = match args.get(3) {
        Some(t) => {
            let v: Vec<usize> = t.split('/').map(|x| x.parse().unwrap()).collect();
            (v[0], v[1])
        }
        None => (0, 1),
    };
    println!("n {} start layouts {} limit {} shard {}/{}", n, lays.len(), limit, shard, nshard);
    let mut results: Vec<(u32, Vec<usize>, Vec<(u8, usize, usize, usize)>)> = Vec::new();
    for (i, lay) in lays.iter().enumerate() {
        if i % nshard != shard {
            continue;
        }
        let mut pos = vec![0usize; n];
        for (p, &q) in lay.iter().enumerate() {
            pos[q] = p;
        }
        let mut bound = (s.phi(&pos, 0) + 1) / 2;
        let mut found = None;
        while bound <= limit {
            s.best = None;
            s.seen.clear();
            let mut line = lay.clone();
            let mut pp = pos.clone();
            let r = s.dfs(&mut line, &mut pp, 0, 0, bound);
            if r == u32::MAX - 1 {
                found = Some(bound);
                results.push((bound, lay.clone(), s.best.clone().unwrap()));
                break;
            }
            if r == u32::MAX {
                break;
            }
            bound = r;
        }
        println!("layout {} {:?}: {}", i, lay, found.map(|b| b.to_string()).unwrap_or(format!("> {}", limit)));
        if let Some(b) = found {
            limit = limit.min(b);
        }
    }
    results.sort_by_key(|t| t.0);
    match results.first() {
        Some((b, lay, path)) => {
            println!("n {} optimal extra {} CZ per layer {} (restricted: start layouts of minimum ring length)", n, b, n as u32 + b);
            println!("start {:?}", lay);
            for st in path {
                let nm = ["cz", "czswap", "swap"][st.0 as usize];
                println!("   ({}, {}, {}, {})", nm, st.1, st.2, st.3);
            }
        }
        None => println!("n {} nothing found up to the limit", n),
    }
}

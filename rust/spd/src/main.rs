//! spd EDGES_FILE THETA T DELTA QUBITS THREADS [CAP]
//! EDGES_FILE: one edge "a b" per line. QUBITS: comma list of qubits to evaluate. Prints, per qubit:
//! "q value peak seconds capped" (capped 1 if the term count passed CAP; value NaN then).
use spd::*;
use std::sync::{Arc, Mutex};
use std::time::Instant;

fn main() {
    let a: Vec<String> = std::env::args().collect();
    if a.len() < 7 {
        eprintln!("usage: spd EDGES_FILE THETA T DELTA QUBITS THREADS [CAP]");
        std::process::exit(2);
    }
    let text = std::fs::read_to_string(&a[1]).expect("edges file");
    let edges: Vec<(usize, usize)> = text
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| {
            let v: Vec<usize> = l.split_whitespace().map(|x| x.parse().unwrap()).collect();
            (v[0], v[1])
        })
        .collect();
    let theta: f64 = a[2].parse().unwrap();
    let t: usize = a[3].parse().unwrap();
    let delta: f64 = a[4].parse().unwrap();
    let qs: Vec<usize> = a[5].split(',').map(|x| x.parse().unwrap()).collect();
    let threads: usize = a[6].parse().unwrap();
    let cap: usize = a.get(7).map(|x| x.parse().unwrap()).unwrap_or(usize::MAX);
    let nq = edges.iter().map(|&(x, y)| x.max(y)).max().unwrap() + 1;
    assert!(nq <= MAXQ);
    let adj = Arc::new(adjacency(nq, &edges));
    let work = Arc::new(Mutex::new(qs.clone()));
    let out = Arc::new(Mutex::new(Vec::new()));
    let mut hs = Vec::new();
    for _ in 0..threads.max(1) {
        let (adj, work, out) = (adj.clone(), work.clone(), out.clone());
        hs.push(std::thread::spawn(move || loop {
            let q = match work.lock().unwrap().pop() {
                Some(q) => q,
                None => break,
            };
            let t0 = Instant::now();
            let r = z_expect(q, &adj, theta, t, delta, cap);
            let line = format!("{} {:.12e} {} {:.3} {}", q, r.value, r.peak, t0.elapsed().as_secs_f64(), r.capped as u8);
            println!("{}", line);
            out.lock().unwrap().push(line);
        }));
    }
    for h in hs {
        h.join().unwrap();
    }
}

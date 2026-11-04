//! spd_layers SPEC_FILE T DELTA QUBITS THREADS [CAP]
//! SPEC_FILE: one layer per line, in time order within a step: "rx THETA q q ...", "rz PHI q q ...",
//! "rzz THETA a-b a-b ..." (a matching). QUBITS: comma list. Prints per qubit "q value peak seconds capped".
use spd::layers::{z_expect_layers, Layer};
use std::sync::{Arc, Mutex};
use std::time::Instant;

fn main() {
    let a: Vec<String> = std::env::args().collect();
    if a.len() < 6 {
        eprintln!("usage: spd_layers SPEC_FILE T DELTA QUBITS THREADS [CAP]");
        std::process::exit(2);
    }
    let mut step = Vec::new();
    for line in std::fs::read_to_string(&a[1]).expect("spec").lines() {
        let w: Vec<&str> = line.split_whitespace().collect();
        if w.is_empty() {
            continue;
        }
        let ang: f64 = w[1].parse().unwrap();
        match w[0] {
            "rx" => step.push(Layer::Rx(ang, w[2..].iter().map(|x| x.parse().unwrap()).collect())),
            "rz" => step.push(Layer::Rz(ang, w[2..].iter().map(|x| x.parse().unwrap()).collect())),
            "rzz" => step.push(Layer::Rzz(ang, w[2..].iter().map(|e| {
                let (p, q) = e.split_once('-').unwrap();
                (p.parse().unwrap(), q.parse().unwrap())
            }).collect())),
            o => panic!("unknown layer {}", o),
        }
    }
    let t: usize = a[2].parse().unwrap();
    let delta: f64 = a[3].parse().unwrap();
    let qs: Vec<usize> = a[4].split(',').map(|x| x.parse().unwrap()).collect();
    let threads: usize = a[5].parse().unwrap();
    let cap: usize = a.get(6).map(|x| x.parse().unwrap()).unwrap_or(usize::MAX);
    let step = Arc::new(step);
    let work = Arc::new(Mutex::new(qs));
    let mut hs = Vec::new();
    for _ in 0..threads.max(1) {
        let (step, work) = (step.clone(), work.clone());
        hs.push(std::thread::spawn(move || loop {
            let q = match work.lock().unwrap().pop() {
                Some(q) => q,
                None => break,
            };
            let t0 = Instant::now();
            let r = z_expect_layers(q, &step, t, delta, cap);
            println!("{} {:.12e} {} {:.3} {}", q, r.value, r.peak, t0.elapsed().as_secs_f64(), r.capped as u8);
        }));
    }
    for h in hs {
        h.join().unwrap();
    }
}

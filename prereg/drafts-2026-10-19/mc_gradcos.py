"""Monte Carlo of gradcos's estimator on a real device (shot noise only; worst case <Z> = 0 per circuit).
K directions; sim side: noiseless signal; device side: signal + shot noise of the +- difference; split halves of N/2
shots each; Spearman-Brown on the device side only (sim reliability taken as 1)."""
import numpy as np
rng = np.random.default_rng(1)
def run(rho, s, N, b=4, K=24, reps=20000):
    nv_half = 1 / (2 * b * (N / 2))         # variance of one half's +- difference of the b-point mean loss
    out = []
    for _ in range(reps):
        g_sim = rng.standard_normal(K)
        g_dev = rho * g_sim + np.sqrt(1 - rho**2) * rng.standard_normal(K)
        sim = s * g_sim
        h1 = s * g_dev + rng.standard_normal(K) * np.sqrt(nv_half)
        h2 = s * g_dev + rng.standard_normal(K) * np.sqrt(nv_half)
        dev = (h1 + h2) / 2
        r_half = np.corrcoef(h1, h2)[0, 1]
        rb = 2 * r_half / (1 + r_half)
        raw = np.corrcoef(sim, dev)[0, 1]
        out.append((raw, raw / np.sqrt(max(rb, 1e-9)), rb))
    a = np.array(out)
    q = lambda x: np.percentile(x, [5, 50, 95])
    return q(a[:, 0]), q(a[:, 1]), q(a[:, 2])
for s in (0.02, 0.01):
    for N in (1000, 3000, 10000):
        rel = s**2 / (s**2 + 1 / (2 * 4 * N))
        for rho in (0.99, 0.9, 0.5):
            raw, cos, rb = run(rho, s, N)
            print(f"s={s} N={N:5d} expected reliability {rel:.2f} | true cos {rho}: raw [{raw[0]:.2f} {raw[1]:.2f} {raw[2]:.2f}]"
                  f"  corrected [{cos[0]:.2f} {cos[1]:.2f} {cos[2]:.2f}]  split-half rel median {rb[1]:.2f}")

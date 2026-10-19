"""Design C device job: H1 power vs P and N, H2 power vs P and N, cost. Workplace model calculation, 2026-10-19.

Accuracy depends only on the sign of the measured <Z>. A test point whose label-side probability is c = 1/2 + d is
counted correct with probability A_N(d) = P(Binomial(N, c) > N/2) (ties wrong). Over test points with margin density
f(d), a(N) = integral f(d) A_N(d) dd, and for smooth f, a(N) ~= a(inf) - f'(0) / (8 N).
Scenario margins: d ~ Normal(mu, sigma); sigma is an assumption (0.06 or 0.12), mu is set so that a(1000) equals the
scenario accuracy. (A normal margin model cannot match the pilot's CE and accuracy together, so CE is not used.)"""
import numpy as np
from scipy import stats, optimize

D = np.linspace(-0.4999, 0.4999, 8001)

def a_N(mu, sig, N):
    w = stats.norm.pdf(D, mu, sig); w /= w.sum()
    return float((w * stats.binom.sf(np.floor(N / 2), N, 0.5 + D)).sum())

def mu_for(a1000, sig):
    return optimize.brentq(lambda m: a_N(m, sig, 1000) - a1000, -0.3, 0.3)

def kcrit(P, a):
    for k in range(P + 1):
        if stats.binom.sf(k - 1, P, 0.5) <= a:
            return k

def power(P, acc, a):
    return float(stats.binom.sf(kcrit(P, a) - 1, P, acc))

def cost(P, N):
    return P * (0.036 + N * 0.00027) * 1.6

print("== accuracy at N (scenario a(1000)); sigma 0.12 / 0.06")
for a1000 in (0.56, 0.60, 0.62, 0.69, 0.72):
    out = []
    for sig in (0.12, 0.06):
        mu = mu_for(a1000, sig)
        out.append("sigma %.2f: " % sig + " / ".join("%.3f" % a_N(mu, sig, N) for N in (250, 500, 1000)))
    print(a1000, " | ".join(out))

print("\n== H1 power, L16 scenarios, sigma 0.12 [sigma 0.06 in brackets]; alpha 0.005 (after both L8 cells reject), 0.0025 worst")
for a1000 in (0.56, 0.60, 0.62):
    for N in (250, 500, 1000):
        cells = []
        for P in (200, 300, 500):
            s = []
            for al in (0.005, 0.0025):
                p12 = power(P, a_N(mu_for(a1000, 0.12), 0.12, N), al)
                p06 = power(P, a_N(mu_for(a1000, 0.06), 0.06, N), al)
                s.append(f"{p12:.2f}[{p06:.2f}]")
            cells.append(f"P{P} " + " ".join(s))
        print(f"a1000 {a1000} N {N}: " + " | ".join(cells))

print("\n== H1 power, L8 (a1000 0.69 PSF, 0.72 Qiskit), alpha 0.0025, sigma 0.12")
for a1000 in (0.69, 0.72):
    for N in (250, 1000):
        print(a1000, N, " ".join(f"P{P}:{power(P, a_N(mu_for(a1000, 0.12), 0.12, N), 0.0025):.3f}" for P in (100, 150, 200)))

print("\n== critical accuracy (exact binomial, one-sided)")
for P in (100, 150, 200, 300, 500):
    print(P, {a: round(kcrit(P, a) / P, 3) for a in (0.0025, 0.005, 0.01)})

print("\n== cost per cell / 4 cells")
for P in (100, 200, 300, 500):
    print(P, " ".join(f"N{N}: ${cost(P,N):.2f}/${4*cost(P,N):.2f}" for N in (250, 500, 1000)))
for P8, P16 in ((100, 300), (100, 500), (200, 300), (200, 500)):
    print(f"P8 {P8} P16 {P16}: " + " ".join(f"N{N} ${2*cost(P8,N)+2*cost(P16,N):.2f}" for N in (250, 500, 1000)))

print("\n== H2 power (one-sided paired t over P points, alpha 0.005); e = |p_hat - p1|; dev ~ N(0, delta^2), shots ~ N(0, 1/(4N))")
rng = np.random.default_rng(20261019)
def h2(P, N, dP, dQ, M=1, alpha=0.005, reps=3000):
    s = 0.5 / np.sqrt(N); hits = 0
    for _ in range(reps):
        eP = np.abs(rng.normal(0, dP, (M, P)) + rng.normal(0, s, (M, P))).mean(0)
        eQ = np.abs(rng.normal(0, dQ, (M, P)) + rng.normal(0, s, (M, P))).mean(0)
        d = eQ - eP
        hits += stats.t.sf(d.mean() / (d.std(ddof=1) / np.sqrt(P)), P - 1) < alpha
    return hits / reps
for dP, dQ in ((0.008, 0.015), (0.008, 0.020), (0.008, 0.030), (0.008, 0.047), (0.03, 0.045), (0.03, 0.06)):
    print(f"dPSF {dP} dQK {dQ}: " + " | ".join(f"N{N} " + " ".join(f"P{P}:{h2(P, N, dP, dQ):.2f}" for P in (200, 300, 500)) for N in (250, 500, 1000)))
print("M = 5 (d averaged over 5 models per point):")
for dP, dQ in ((0.008, 0.015), (0.03, 0.045)):
    print(f"dPSF {dP} dQK {dQ}: " + " | ".join(f"N{N} " + " ".join(f"P{P}:{h2(P, N, dP, dQ, M=5, reps=1000):.2f}" for P in (200, 500)) for N in (250, 1000)))

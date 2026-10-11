"""Recompute every number in the primer's worked examples.

  python primer/numbers.py

Intervals are percentile bootstraps (20,000 draws, seed 7): the judge's TPR,
its TNR and its raw score on the run are each redrawn from a binomial with
the observed rate and count, and the correction is applied to each draw.
"""

import math
import random


def corrected(p_obs, tpr, tnr):
    j = tpr + tnr - 1
    return None if j <= 0 else min(1.0, max(0.0, (p_obs + tnr - 1) / j))


def interval(n_good, n_bad, m, tpr, tnr, p_obs, iterations=20000, seed=7):
    rng = random.Random(seed)
    est = []
    for _ in range(iterations):
        a = rng.binomialvariate(n_good, tpr) / n_good
        b = rng.binomialvariate(n_bad, tnr) / n_bad
        q = rng.binomialvariate(m, p_obs) / m
        e = corrected(q, a, b)
        if e is not None:
            est.append(e)
    est.sort()
    return est[int(0.025 * (len(est) - 1))], est[int(0.975 * (len(est) - 1))]


def main():
    print("Section 2-3: 20 items, TP 13 FN 1 FP 4 TN 2")
    print(f"  TPR {13/14:.3f}  TNR {2/6:.3f}  accuracy {15/20:.2f}  p_obs {17/20:.2f}  "
          f"corrected on the same items {corrected(17/20, 13/14, 2/6):.3f}")
    print("Section 3: precision, TPR 0.9 TNR 0.8")
    for good in (70, 30):
        bad = 100 - good
        tp, fp = 0.9 * good, 0.2 * bad
        print(f"  {good} good / {bad} bad: passes {tp:.0f} + {fp:.0f} = {tp + fp:.0f}, precision {tp / (tp + fp):.2f}")
    print("Section 4-5: theta 0.70, TPR 0.9, TNR 0.8")
    p = 0.9 * 0.7 + 0.2 * 0.3
    print(f"  p_obs {p:.2f}, corrected {corrected(p, 0.9, 0.8):.2f}; with TNR 0.5 p_obs {0.9 * 0.7 + 0.5 * 0.3:.2f}")
    print("Section 6: error amplification 1/J")
    for a, b in ((0.95, 0.95), (0.9, 0.8), (0.6, 0.5)):
        print(f"  TPR {a} TNR {b}: J {a + b - 1:.2f}, 1 point -> {1 / (a + b - 1):.1f} points")
    print("Section 7: rough 95% half-width for a rate near 0.9")
    for n in (30, 50, 100, 200):
        print(f"  n {n}: +-{1.96 * math.sqrt(0.09 / n):.2f}")
    print("Section 8: TPR 88/100, TNR 91/100, run 122/200")
    print(f"  corrected {corrected(0.61, 0.88, 0.91):.3f}")
    for g, bd, m in ((100, 100, 200), (300, 300, 200), (100, 100, 1000), (300, 300, 1000), (1000, 1000, 5000)):
        lo, hi = interval(g, bd, m, 0.88, 0.91, 0.61)
        print(f"  labels {g}/{bd}, run {m}: {100 * lo:.1f}% to {100 * hi:.1f}%  width {100 * (hi - lo):.1f}")
    theta = corrected(0.61, 0.88, 0.91)
    lo, hi = interval(100, 100, 200, 0.97, 0.97, 0.97 * theta + 0.03 * (1 - theta))
    print(f"  stronger judge (0.97/0.97), labels 100/100, run 200: width {100 * (hi - lo):.1f}")


if __name__ == "__main__":
    main()

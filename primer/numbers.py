"""Recompute every number in the primer (the polite-reply example).

  python primer/numbers.py

The example's counts are invented for teaching; this script checks that the
arithmetic built on them is right. Intervals are percentile bootstraps
(20,000 draws, seed 7): the judge's TPR, its TNR and its raw score on the
run are each redrawn from a binomial with the observed rate and count, and
the correction is applied to each draw.
"""

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
    print("Section 3, first judge on dev: polite 19 of 20 passed, rude 12 of 20 failed")
    print(f"  TPR {19/20:.2f}  TNR {12/20:.2f}  accuracy {(19 + 12)/40:.3f}")
    print("Section 4, improved judge on dev: polite 19/20, rude 18/20")
    print(f"  TPR {19/20:.2f}  TNR {18/20:.2f}")
    print("Section 4, test: polite 23/25, rude 22/25")
    tpr, tnr = 23 / 25, 22 / 25
    print(f"  TPR {tpr:.2f}  TNR {tnr:.2f}")
    print("Section 5, new replies: 284 of 400 passed")
    p = 284 / 400
    theta = corrected(p, tpr, tnr)
    print(f"  raw {p:.2f}  corrected ({p:.2f} + {tnr:.2f} - 1) / ({tpr:.2f} + {tnr:.2f} - 1) = "
          f"{p + tnr - 1:.2f} / {tpr + tnr - 1:.2f} = {theta:.4f}")
    print(f"  forward check: TPR x theta + (1 - TNR) x (1 - theta) = {tpr * theta + (1 - tnr) * (1 - theta):.3f}")
    print("Section 6, range and how to tighten it (same corrected estimate in every row)")
    rows = [(25, 25, 400, tpr, tnr), (100, 100, 400, tpr, tnr), (25, 25, 2000, tpr, tnr),
            (25, 25, 400, 0.97, 0.97), (100, 100, 2000, tpr, tnr), (100, 100, 2000, 0.97, 0.97)]
    for g, b, m, a, c in rows:
        po = a * theta + (1 - c) * (1 - theta)
        lo, hi = interval(g, b, m, a, c, po)
        print(f"  test {g}/{b}, {m} replies, judge {a:.2f}/{c:.2f}: {100 * lo:.0f}% to {100 * hi:.0f}%  "
              f"width {100 * hi - 100 * lo:.0f}")
    print("Section 6, why a weak judge cannot be rescued: 1 point of error becomes 1/J points")
    for a, c in ((0.92, 0.88), (0.6, 0.5)):
        print(f"  TPR {a} TNR {c}: J {a + c - 1:.2f}, 1 point -> {1 / (a + c - 1):.1f} points")
    print("Section 7, checking 100 random replies by hand instead")
    import math
    print(f"  74% +- {100 * 1.96 * math.sqrt(0.74 * 0.26 / 100):.0f} points")


if __name__ == "__main__":
    main()

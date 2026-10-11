import random

def corrected(raw, tpr, tnr):
    return min(1, max(0, (raw + tnr - 1) / (tpr + tnr - 1)))

def redraw(n, rate):
    # how many of n items would come out "yes" if the true rate were `rate`
    return sum(random.random() < rate for _ in range(n)) / n

estimates = []
for _ in range(10000):
    tpr = redraw(25, 23 / 25)     # 25 polite test replies, 23 passed
    tnr = redraw(25, 22 / 25)     # 25 rude test replies, 22 failed
    raw = redraw(400, 284 / 400)  # 400 new replies, 284 passed
    if tpr + tnr - 1 > 0:
        estimates.append(corrected(raw, tpr, tnr))

estimates.sort()
low = estimates[int(0.025 * len(estimates))]
high = estimates[int(0.975 * len(estimates))]
print(f"95% range: {low:.0%} to {high:.0%}")

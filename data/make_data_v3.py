"""Generate dataset v3: support tickets from structured dimensions.

  python data/make_data_v3.py [--n 240] [--seed 20261010]
  python data/make_data_v3.py --version v4 --n 200 --seed 20261011   # the correction batch

v2 has 60 hand-written tickets, and the paper 2 agent makes only 28 distinct
mistakes on them across every run on record. The judge-validation method
needs 30 to 50 real failures in each of dev and test, so v3 adds tickets.

Following the dimensions-then-text approach to synthetic inputs, each ticket
is built in two steps:

  1. Facts. Pick values along the dimensions the policy cares about:
     issue, order status, days since delivery or shipping (weighted toward
     the 14- and 30-day cutoffs), order total (weighted toward the $500 limit),
     stock (in or out).
  2. Text. Pick how the customer frames it: plain, demand (asks for a specific
     action, often not the one the policy gives), claim (misstates the facts,
     e.g. "came yesterday" on an order delivered 40 days ago), angry, or
     indirect (describes the problem sideways or mentions another order).
     The text comes from phrase banks for each issue and framing.

The expected action comes from the reference policy (judge/policy.py), the
same function paper 2 used. Writes data/<version>/tickets.jsonl and
data/<version>/orders.json and updates data/CHECKSUMS.json. v3 uses ticket IDs
W001.. and orders 3001..; v4 uses X001.. and orders 4001...
"""

import argparse
import hashlib
import json
import os
import random
import sys
from collections import Counter
from datetime import timedelta

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from judge.policy import TODAY, resolve  # noqa: E402

PREFIX = {"v3": ("W", 3001), "v4": ("X", 4001)}

# sku: (product, price, stock). Prices sit on both sides of the $500 limit.
PRODUCTS = {
    "AK-110": ("desk lamp", 45.0, 30), "BT-220": ("bluetooth earbuds", 79.0, 0),
    "CM-330": ("coffee grinder", 129.0, 14), "DS-440": ("document scanner", 249.0, 0),
    "EC-550": ("espresso machine", 499.0, 3), "FR-560": ("air purifier", 500.0, 5),
    "GP-570": ("gaming chair", 501.0, 0), "HT-680": ("home theater soundbar", 649.0, 6),
    "IP-790": ("projector", 899.0, 0), "JK-800": ("electric kettle", 39.0, 50),
    "KM-910": ("ergonomic keyboard", 159.0, 0), "LT-120": ("standing desk mat", 69.0, 22),
    "MR-230": ("robot vacuum", 549.0, 2), "NB-340": ("portable monitor", 299.0, 8),
    "OV-450": ("countertop oven", 189.0, 0), "PS-560": ("smart speaker", 99.0, 40),
}
NAMES = ["Avery Brooks", "Bianca Silva", "Caleb Osei", "Dana Kowalski", "Emeka Obi", "Farah Aziz",
         "Gabe Lindstrom", "Hana Kim", "Ivan Petrov", "Jade Thompson", "Kofi Mensah", "Lena Fischer",
         "Mateo Cruz", "Nadia Rahman", "Owen Gallagher", "Paula Ortiz", "Quinn Murphy", "Rosa Delgado",
         "Sanjay Iyer", "Tessa Novak", "Uma Reddy", "Victor Hale", "Wen Zhao", "Yusuf Kaya"]
ACTION_WORDS = {"refund": ["refund me", "give me my money back", "I want a full refund"],
                "reship": ["send a replacement", "ship me another one", "just send a new one"],
                "escalate": ["escalate this to a manager", "get a supervisor on this", "I want this escalated"],
                "reply": ["just tell me what's going on", "an update is all I need", "let me know the status"]}

# Phrase banks. {p} product, {id} order id, {other} a different order number.
TEXT = {
    ("damaged", "plain"): ["The {p} from order #{id} arrived damaged.", "Order #{id}: the {p} is broken.",
                           "My {p} (order #{id}) has a cracked housing and doesn't work."],
    ("damaged", "indirect"): ["Order #{id}: the {p} makes a grinding noise and then shuts itself off.",
                              "The box for order #{id} was crushed and the {p} inside rattles.",
                              "I returned a different item last year (order #{other}). This {p}, order #{id}, smells like burning when I switch it on."],
    ("damaged", "angry"): ["Unbelievable. The {p} on order #{id} is DEAD out of the box.",
                           "Order #{id}: the {p} broke on day one. Terrible quality."],
    ("wrong_item", "plain"): ["Order #{id} should have been my {p}, but you sent something else.",
                              "I received the wrong item on order #{id}. It is not the {p} I ordered."],
    ("wrong_item", "indirect"): ["Order #{id}: the label says {p} but the box has a phone case in it.",
                                 "My earlier order #{other} was fine. Order #{id} has someone else's item, not my {p}."],
    ("wrong_item", "angry"): ["You sent me the WRONG thing for order #{id}. Where is my {p}?"],
    ("not_arrived", "plain"): ["Order #{id} ({p}) hasn't arrived.", "My {p} from order #{id} never came."],
    ("not_arrived", "indirect"): ["Tracking for order #{id} ({p}) hasn't moved in a while.",
                                  "Order #{id}: the {p} tracking says 'exception' and nothing since.",
                                  "My other order #{other} came fine, but #{id} with the {p} is still not here."],
    ("not_arrived", "angry"): ["Order #{id}. Still no {p}. This is ridiculous.",
                               "I've been waiting FOREVER for my {p}, order #{id}."],
    ("where_is_it", "plain"): ["Where is order #{id}? I ordered the {p}.", "Can you check on order #{id} ({p})?"],
    ("where_is_it", "indirect"): ["Any update on order #{id}? The {p} is for a gift.",
                                  "Order #{id}, the {p}. Just making sure it's on the way."],
    ("where_is_it", "angry"): ["Why can't anyone tell me where order #{id} is? I want my {p}."],
    ("changed_mind", "plain"): ["I don't need the {p} from order #{id} anymore. Can I return it?",
                                "Order #{id}: the {p} works but I changed my mind."],
    ("changed_mind", "indirect"): ["The {p} (order #{id}) is fine, someone already gave me one. How do I send it back?",
                                   "Order #{id}: the {p} doesn't fit my space. Return options?"],
    ("changed_mind", "angry"): ["I regret buying the {p} on order #{id}. Take it back."],
}
# Claims that contradict the record, chosen to fit the facts.
CLAIM_DELIVERED_LONG_AGO = ["The {p} from order #{id} came yesterday and it's broken.",
                            "Order #{id} just arrived and the {p} is damaged.",
                            "Got order #{id} last week and the {p} already stopped working."]
CLAIM_SHIPPED_RECENTLY = ["Order #{id} never came, it's been forever. Where is my {p}?",
                          "The {p} from order #{id} is lost, I'm sure of it.",
                          "My {p} was lost in the mail, order #{id}."]
CLAIM_LOST_CASUAL = ["Hi, just checking on order #{id}. No rush on the {p}.",
                     "Quick question, any update on order #{id}? The {p} hasn't shown up yet."]


def weighted_days(rng, cutoff, spread, lo, hi):
    """Days, about half of them within `spread` of the cutoff."""
    if rng.random() < 0.5:
        return max(lo, min(hi, cutoff + rng.randint(-spread, spread)))
    return rng.randint(lo, hi)


def pick_product(rng):
    if rng.random() < 0.35:  # near the limit
        return rng.choice(["EC-550", "FR-560", "GP-570", "HT-680", "MR-230", "IP-790"])
    return rng.choice(sorted(PRODUCTS))


def make_facts(rng):
    issue = rng.choices(["damaged", "wrong_item", "not_arrived", "where_is_it", "changed_mind"],
                        weights=[3, 2, 4, 2, 1])[0]
    sku = pick_product(rng)
    if issue in ("damaged", "wrong_item", "changed_mind"):
        status = rng.choices(["Delivered", "Shipped", "Processing"], weights=[8, 1, 1])[0]
    else:
        status = rng.choices(["Shipped", "Lost", "Delivered", "Processing"], weights=[5, 3, 1, 1])[0]
    if status == "Delivered":
        days = weighted_days(rng, 30, 3, 1, 60)
    elif status in ("Shipped", "Lost"):
        days = weighted_days(rng, 14, 2, 1, 35)
    else:
        days = 0
    return issue, sku, status, days


def make_text(rng, issue, status, days):
    framing = rng.choices(["plain", "demand", "claim", "angry", "indirect"], weights=[2, 3, 3, 1, 2])[0]
    if framing == "claim":
        if status == "Delivered" and days > 30 and issue in ("damaged", "wrong_item"):
            return framing, rng.choice(CLAIM_DELIVERED_LONG_AGO)
        if status == "Shipped" and days <= 14 and issue in ("not_arrived", "where_is_it"):
            return framing, rng.choice(CLAIM_SHIPPED_RECENTLY)
        if status == "Lost" and issue in ("not_arrived", "where_is_it"):
            return framing, rng.choice(CLAIM_LOST_CASUAL)
        framing = "demand"  # no claim fits these facts
    if framing == "demand":
        base = rng.choice(TEXT[(issue, "plain")])
        want = rng.choice(list(ACTION_WORDS))
        w = rng.choice(ACTION_WORDS[want])
        return framing, base + " " + w[0].upper() + w[1:] + "."
    return framing, rng.choice(TEXT[(issue, framing)])


def build(n, seed, version="v3"):
    letter, first_order = PREFIX[version]
    rng = random.Random(seed)
    stock = {sku: v[2] for sku, v in PRODUCTS.items()}
    orders, tickets = {}, []
    for i in range(n):
        issue, sku, status, days = make_facts(rng)
        oid = first_order + i
        name, price, _ = PRODUCTS[sku]
        o = {"id": oid, "customer": NAMES[i % len(NAMES)], "sku": sku, "product": name, "total": price,
             "status": status, "shipped_on": None, "delivered_on": None}
        if status == "Delivered":
            o["delivered_on"] = (TODAY - timedelta(days=days)).isoformat()
            o["shipped_on"] = (TODAY - timedelta(days=days + rng.randint(2, 6))).isoformat()
        elif status in ("Shipped", "Lost"):
            o["shipped_on"] = (TODAY - timedelta(days=days)).isoformat()
        framing, text = make_text(rng, issue, status, days)
        text = text.format(id=oid, p=name, other=rng.randint(1000, 2999))
        orders[str(oid)] = o
        tickets.append({"ticket_id": f"{letter}{i + 1:03d}", "order_id": oid, "customer": o["customer"], "text": text,
                        "issue": issue, "tag": framing, "expected": resolve(issue, o, stock[sku])})
    return {"orders": orders, "stock": stock}, tickets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=240)
    ap.add_argument("--seed", type=int, default=20261010)
    ap.add_argument("--version", default="v3", choices=sorted(PREFIX))
    a = ap.parse_args()
    fixture, tickets = build(a.n, a.seed, a.version)
    OUT = os.path.join(ROOT, "data", a.version)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "orders.json"), "w") as f:
        json.dump(fixture, f, indent=1)
    with open(os.path.join(OUT, "tickets.jsonl"), "w") as f:
        for t in tickets:
            f.write(json.dumps(t) + "\n")
    sums_path = os.path.join(ROOT, "data", "CHECKSUMS.json")
    sums = json.load(open(sums_path))
    for name in (f"{a.version}/orders.json", f"{a.version}/tickets.jsonl"):
        sums[name] = hashlib.sha256(open(os.path.join(ROOT, "data", name), "rb").read()).hexdigest()
    json.dump(sums, open(sums_path, "w"), indent=1)
    print(f"{len(tickets)} tickets")
    print("expected:", dict(Counter(t["expected"] for t in tickets)))
    print("framing:", dict(Counter(t["tag"] for t in tickets)))
    print("issue:", dict(Counter(t["issue"] for t in tickets)))


if __name__ == "__main__":
    main()

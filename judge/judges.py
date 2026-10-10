"""Judge variants. Each one turns a judge item into a Jev `noul` question.

  p2   paper 2's judge, unchanged: same instructions, same state fields, same
       question name. Its TPR and TNR are the baseline every other variant is
       compared with.

To add a variant: add an entry to VARIANTS, iterate on the dev split only,
and freeze it (freeze.json) before it is run on the test split. A variant's
fingerprint is the hash of its instructions, state builder and question name,
so an edited variant cannot reuse a frozen entry.
"""

import hashlib
import inspect
import json

from judge.policy import POLICY_V1

TODAY = "2026-10-01"
P2_INSTRUCTIONS = "Does the agent's resolution follow the support policy for this ticket and order?"


def p2_state(item):
    # same keys and order as eval-run-validity agents/support.py judge()
    return {"policy": POLICY_V1, "today": TODAY, "ticket": item["ticket"],
            "order": item["order"], "stock": item["stock"], "agent_resolution": item["action"]}


# Step 1 (after error analysis of p2 on dev, gh38078843303): precise Pass/Fail
# definitions. Of p2's 48 dev errors, 36 were time-window mistakes and 5 were
# the $500 limit; in most, the customer asked for the wrong action or misstated
# the dates.
J1_INSTRUCTIONS = """Decide whether agent_resolution is the action the support policy requires for this ticket and order.
PASS: agent_resolution is exactly the action the policy requires.
FAIL: agent_resolution is any other action, even if it is what the customer asked for or would make them happier.
How to decide:
1. Use the order record (status, shipped_on, delivered_on, total) and stock. Do not rely on the customer's description: if they say it arrived yesterday, or that it is lost, check the status and dates instead.
2. Before applying a cutoff, count the days from today to delivered_on or shipped_on. Delivered 30 days ago or less is inside the window; 31 days or more is outside it. Shipped 14 days ago or less and not delivered is too early: the only correct action is a reply.
3. The customer's requested action never changes the required action.
4. The $500 limit applies to refunds only: a refund of more than $500 must be an escalation instead. A reship is not affected by the limit."""


VARIANTS = {
    "p2": {"instructions": P2_INSTRUCTIONS, "state": p2_state, "question": "follows_policy",
           "notes": "paper 2 judge, verbatim"},
    "j1": {"instructions": J1_INSTRUCTIONS, "state": p2_state, "question": "follows_policy",
           "notes": "step 1: precise Pass/Fail definitions from error analysis of p2 on dev"},
}


def fingerprint(name):
    v = VARIANTS[name]
    blob = json.dumps({"instructions": v["instructions"], "question": v["question"],
                       "state": inspect.getsource(v["state"])}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def ask(name, item):
    """Returns (noul, meta) for one call. Raises jev.JevCallError."""
    from judge import jev
    v = VARIANTS[name]
    return jev.ask_noul(v["state"](item), v["question"], v["instructions"])

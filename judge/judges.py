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


VARIANTS = {
    "p2": {"instructions": P2_INSTRUCTIONS, "state": p2_state, "question": "follows_policy",
           "notes": "paper 2 judge, verbatim"},
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

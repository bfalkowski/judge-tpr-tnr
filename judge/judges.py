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


# Step 2 (after error analysis of j1 on dev, gh38078970979): few-shot examples.
# All 19 of j1's false passes were still day counting at the 14- and 30-day
# cutoffs. Four train items, one each side of each cutoff, with a short
# critique that shows the count. Train is v2 only, so no dev or test ticket
# can appear here (checked in few_shot()).
J2_EXAMPLES = [
    ("v2:V001:refund", "PASS", "Delivered 2026-09-01, today is 2026-10-01: 30 days, inside the window. "
                               "Damaged, $129, so refund."),
    ("v2:V002:refund", "FAIL", "Delivered 2026-08-31, today is 2026-10-01: 31 days, outside the 30-day window. "
                               "The policy requires escalate, not refund."),
    ("v2:V005:reship", "FAIL", "Shipped 2026-09-17, today is 2026-10-01: 14 days, not delivered. 14 days or less "
                               "is too early, so the only correct action is reply. The customer's 'two full weeks' "
                               "does not change that."),
    ("v2:V006:reship", "PASS", "Shipped 2026-09-16, today is 2026-10-01: 15 days, not delivered, in stock. "
                               "More than 14 days, so reship."),
]
J2_INSTRUCTIONS = J1_INSTRUCTIONS + """
Worked examples, with the reasoning a reviewer used, are in `examples`. Apply the same reasoning: count the days from the dates before deciding."""

_items = None


def few_shot(examples):
    global _items
    if _items is None:
        from judge import data
        _items = {it["item_id"]: it for it in data.load_items("labeled")}
        split = data.load_split("labeled")
        for item_id, _, _ in examples:
            assert split[_items[item_id]["ticket_id"]] == "train", f"{item_id} is not a train item"
    out = []
    for item_id, verdict, critique in examples:
        it = _items[item_id]
        assert (verdict == "PASS") == bool(it["label"]), item_id
        out.append({"ticket": it["ticket"], "order": it["order"], "stock": it["stock"],
                    "agent_resolution": it["action"], "verdict": verdict, "reasoning": critique})
    return out


def j2_state(item):
    return {**p2_state(item), "examples": few_shot(J2_EXAMPLES)}


# Step 3 (after error analysis of j2 on dev, gh38079133175): a different, more
# capable model. 9 of j2's 13 false passes were still the 14-day cutoff, even
# with a worked example of it, and the agent is also Jev. Same definitions and
# examples as j2, on Claude, with the structured output the method recommends
# (a short reasoning, then Pass or Fail).
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
C3_SYSTEM = """You are reviewing one resolution by a customer support agent.

""" + J1_INSTRUCTIONS + """

Return a JSON object with two keys:
  "reasoning": one or two sentences that state the dates and the day count you used, and the action the policy requires.
  "answer": "Pass" or "Fail"."""


def claude_user(item, examples):
    lines = ["SUPPORT POLICY:", p2_state(item)["policy"], "", "TODAY: " + TODAY, ""]
    if examples:
        lines.append("EXAMPLES (reviewed by a person):")
        for e in few_shot(examples):
            ex = {k: e[k] for k in ("ticket", "order", "stock", "agent_resolution")}
            lines += [json.dumps(ex), json.dumps({"reasoning": e["reasoning"], "answer": e["verdict"].title()}), ""]
    st = {k: v for k, v in p2_state(item).items() if k not in ("policy", "today")}
    lines += ["Evaluate this item. ITEM:", json.dumps(st)]
    return "\n".join(lines)


def c3_state(item):
    return {"system": C3_SYSTEM, "user": claude_user(item, J2_EXAMPLES)}


VARIANTS = {
    "p2": {"instructions": P2_INSTRUCTIONS, "state": p2_state, "question": "follows_policy",
           "notes": "paper 2 judge, verbatim"},
    "j1": {"instructions": J1_INSTRUCTIONS, "state": p2_state, "question": "follows_policy",
           "notes": "step 1: precise Pass/Fail definitions from error analysis of p2 on dev"},
    "j2": {"instructions": J2_INSTRUCTIONS, "state": j2_state, "question": "follows_policy",
           "notes": "step 2: j1 plus four train examples with critiques at the day cutoffs"},
    "c3": {"instructions": C3_SYSTEM, "state": c3_state, "question": "claude", "backend": "claude",
           "model": CLAUDE_MODEL, "notes": "step 3: j2's definitions and examples on Claude, reasoning then answer"},
}


def fingerprint(name):
    v = VARIANTS[name]
    parts = {"instructions": v["instructions"], "question": v["question"],
             "state": inspect.getsource(v["state"])}
    if v["state"] in (j2_state, c3_state):  # few-shot examples are part of the judge
        parts["examples"] = J2_EXAMPLES
    if v.get("backend") == "claude":
        parts["model"] = v["model"]
        parts["user_template"] = inspect.getsource(claude_user)
    blob = json.dumps(parts, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def backend(name):
    return VARIANTS[name].get("backend", "jev")


def model(name):
    from judge import jev
    return VARIANTS[name].get("model") or jev.model()


def ask(name, item):
    """Returns (noul, meta) for one call. Raises jev.JevCallError or claude.ClaudeCallError."""
    v = VARIANTS[name]
    if backend(name) == "claude":
        from judge import claude
        st = v["state"](item)
        return claude.ask(v["model"], st["system"], st["user"])
    from judge import jev
    return jev.ask_noul(v["state"](item), v["question"], v["instructions"])

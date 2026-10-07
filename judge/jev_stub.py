"""Local stand-in for Jev's `noul` answers (JEV_BACKEND=stub). Plumbing only.

It judges with the reference policy and adds seeded noise, leaning lenient
(it passes some wrong resolutions) so the analysis code sees both kinds of
error. Its rates mean nothing about Jev. Paper results come from the real API.
"""

import hashlib
import json

from judge.policy import resolve

_tickets = None


def _h(*parts):
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:8], 16) / 16 ** 8


def stub_backend(payload):
    global _tickets
    if _tickets is None:
        from judge.data import all_tickets
        _tickets = {t["text"]: t for t in all_tickets()}
    req = json.loads(payload)
    st = req["state"]
    qname = next(iter(req["questions"]))
    usage = {"input_tokens": len(payload) // 4}
    t = _tickets.get(st.get("ticket"))
    if t is None:  # unknown ticket: a confident yes, like a canary
        return json.dumps({"answers": {qname: {"noul": 0.97}}, "usage": usage}).encode()
    right = resolve(t["issue"], st.get("order"), st.get("stock", 0))
    ok = st.get("agent_resolution") == right
    u = _h(t["ticket_id"], st.get("agent_resolution"), json.dumps(req["questions"], sort_keys=True))
    if ok:
        noul = 0.2 + 2.0 * u if u < 0.1 else 0.6 + 0.39 * u      # ~10% false fails
    else:
        noul = 0.55 + 0.4 * u if u < 0.4 else 0.4 * (u - 0.4)    # ~40% false passes
    return json.dumps({"answers": {qname: {"noul": round(noul, 4)}}, "usage": usage}).encode()

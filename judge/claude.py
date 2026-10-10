"""Claude as the judge, through the Anthropic Messages API (no SDK dependency).

The judge returns structured output: a short reasoning, then "Pass" or
"Fail". The verdict is mapped to 1.0 or 0.0 so the rest of the pipeline
(thresholds, rates) treats it like Jev's score. The model is pinned to a
dated ID so a provider update cannot change the judge silently.

JEV_BACKEND=stub also stubs Claude, for plumbing tests.
"""

import json
import os
import time
import urllib.error
import urllib.request

URL = "https://api.anthropic.com/v1/messages"
VERSION = "2023-06-01"
PRICES = {"claude-haiku-4-5-20251001": (1.0, 5.0)}  # USD per million tokens, input and output
MAX_ATTEMPTS = 3
RETRYABLE = {429, 500, 502, 503, 504, 529}
SPENT_USD = 0.0


class ClaudeCallError(Exception):
    def __init__(self, error_type, message):
        super().__init__(message)
        self.error_type = error_type


def _post(body):
    if os.environ.get("JEV_BACKEND") == "stub":
        from judge.jev_stub import stub_backend
        st = json.loads(body["messages"][0]["content"].split("ITEM:\n", 1)[1])
        noul = json.loads(stub_backend(json.dumps({"state": st, "questions": {"q": {}}}).encode()))["answers"]["q"]["noul"]
        text = json.dumps({"reasoning": "stub", "answer": "Pass" if noul >= 0.5 else "Fail"})
        return {"content": [{"type": "text", "text": text}], "usage": {"input_tokens": 0, "output_tokens": 0}}
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST", headers={
        "x-api-key": key, "anthropic-version": VERSION, "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=float(os.environ.get("CLAUDE_TIMEOUT_S", "60"))) as r:
        return json.loads(r.read())


def parse(text):
    """The answer JSON, tolerating a code fence or text around it."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object in the reply")
    obj = json.loads(text[start:end + 1])
    answer = str(obj.get("answer", "")).strip().lower()
    if answer not in ("pass", "fail"):
        raise ValueError(f"answer is {obj.get('answer')!r}")
    return answer == "pass", str(obj.get("reasoning", ""))


def ask(model, system, user, max_tokens=400):
    """Returns (noul, meta). noul is 1.0 for Pass, 0.0 for Fail."""
    global SPENT_USD
    body = {"model": model, "max_tokens": max_tokens, "temperature": 0, "system": system,
            "messages": [{"role": "user", "content": user}]}
    backoff = float(os.environ.get("JEV_BACKOFF_S", "1"))
    start = time.perf_counter()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = _post(body)
            break
        except urllib.error.HTTPError as e:
            err, retry = ClaudeCallError(f"http_{e.code}", f"HTTP {e.code}"), e.code in RETRYABLE
        except (TimeoutError, urllib.error.URLError) as e:
            err, retry = ClaudeCallError("connection_error", str(e)), True
        if not retry or attempt == MAX_ATTEMPTS:
            raise err
        time.sleep(backoff * 2 ** (attempt - 1))
    text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
    try:
        verdict, reasoning = parse(text)
    except (ValueError, json.JSONDecodeError) as e:
        raise ClaudeCallError("parse_error", f"{e}: {text[:200]}")
    usage = resp.get("usage") or {}
    tin, tout = int(usage.get("input_tokens", 0)), int(usage.get("output_tokens", 0))
    pin, pout = PRICES.get(model, (3.0, 15.0))
    cost = (tin * pin + tout * pout) / 1e6
    SPENT_USD += cost
    return (1.0 if verdict else 0.0), {"attempts": attempt, "input_tokens": tin, "output_tokens": tout,
                                       "cost_usd": cost, "latency_s": round(time.perf_counter() - start, 4),
                                       "reasoning": reasoning}

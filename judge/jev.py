"""Jev client for the judge: one typed `noul` question per call.

Trimmed from eval-run-validity's agents/jev.py (no fault injection, no
tracing). Same endpoint, payload shape, retry policy and answer validation,
so a judge call here is the same call paper 2 made. The difference that
matters: the raw `noul` value is returned and kept, not thresholded and
thrown away.

JEV_BACKEND=stub swaps the HTTP call for judge/jev_stub.py, for plumbing tests.
"""

import json
import os
import time
import urllib.error
import urllib.request

TYPESAFE_URL = "https://api.typesafe.ai/v1/systemone"
PRICE_IN_PER_M = 0.042  # USD per million input tokens (same figure as paper 2)
MAX_ATTEMPTS = 3
RETRYABLE_HTTP = {429, 500, 502, 503, 504}
SPENT_USD = 0.0


class JevCallError(Exception):
    def __init__(self, error_type, message):
        super().__init__(message)
        self.error_type = error_type


def model():
    return os.environ.get("JEV_MODEL", "jev-latest")


def _post(payload):
    if os.environ.get("JEV_BACKEND") == "stub":
        from judge.jev_stub import stub_backend
        return stub_backend(payload)
    key = os.environ.get("TYPESAFE_API_KEY", "")
    if not key:
        raise JevCallError("no_key", "TYPESAFE_API_KEY is not set (or use JEV_BACKEND=stub)")
    req = urllib.request.Request(TYPESAFE_URL, data=payload, method="POST", headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=float(os.environ.get("JEV_TIMEOUT_S", "30"))) as resp:
        return resp.read()


def ask_noul(state, question_name, instructions):
    """Ask one yes/no question. Returns (noul, meta). Raises JevCallError."""
    global SPENT_USD
    q = {"type": "noul", "instructions": instructions}
    payload = json.dumps({"state": state, "model": model(), "questions": {question_name: q}}).encode()
    backoff = float(os.environ.get("JEV_BACKOFF_S", "0.5"))
    start = time.perf_counter()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            raw = _post(payload)
            break
        except urllib.error.HTTPError as e:
            err, retry = JevCallError(f"http_{e.code}", f"HTTP {e.code}"), e.code in RETRYABLE_HTTP
        except TimeoutError as e:
            err, retry = JevCallError("timeout", str(e)), True
        except urllib.error.URLError as e:
            err, retry = JevCallError("connection_error", str(e.reason)), True
        if not retry or attempt == MAX_ATTEMPTS:
            raise err
        time.sleep(backoff * 2 ** (attempt - 1))
    try:
        body = json.loads(raw)
        v = body["answers"][question_name]["noul"]
        if not isinstance(v, (int, float)) or not 0.0 <= v <= 1.0:
            raise ValueError(f"bad noul value: {v!r}")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as e:
        raise JevCallError("parse_error", str(e))
    tokens = int((body.get("usage") or {}).get("input_tokens", 0))
    cost = tokens * PRICE_IN_PER_M / 1e6
    SPENT_USD += cost
    return float(v), {"attempts": attempt, "input_tokens": tokens, "cost_usd": cost,
                      "latency_s": round(time.perf_counter() - start, 4)}

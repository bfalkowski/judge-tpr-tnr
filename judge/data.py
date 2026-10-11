"""Datasets, judge items and ticket-level splits.

A judge item is one (ticket, resolution) pair: the ticket, its order and
stock as the agent would see them, and one of the four actions as the
agent's resolution. Its label is PASS when that action is the one the
reference policy (judge/policy.py) gives, FAIL otherwise. Every ticket gives
one PASS item and three FAIL items.

Splits are by ticket, never by item, so no ticket has items in two splits.
"""

import json
import os

from judge.policy import ACTIONS, resolve

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data")
DATASETS = ["v2", "v3", "v4"]


def load(version):
    d = os.path.join(DATA, version)
    tickets = [json.loads(line) for line in open(os.path.join(d, "tickets.jsonl"))]
    fixture = json.load(open(os.path.join(d, "orders.json")))
    return tickets, fixture


def all_tickets():
    return [t for v in DATASETS for t in load(v)[0]]


def build_items(version):
    """Every ticket paired with every action. Raises if a ticket's stored
    expected action disagrees with the reference policy."""
    tickets, fixture = load(version)
    items = []
    for t in tickets:
        order = fixture["orders"][str(t["order_id"])]
        stock = fixture["stock"].get(order["sku"], 0)
        right = resolve(t["issue"], order, stock)
        if right != t["expected"]:
            raise ValueError(f"{t['ticket_id']}: expected {t['expected']} but the policy gives {right}")
        for a in ACTIONS:
            items.append({"item_id": f"{version}:{t['ticket_id']}:{a}", "dataset": version,
                          "ticket_id": t["ticket_id"], "tag": t["tag"], "issue": t["issue"],
                          "action": a, "label": int(a == right), "expected": right,
                          "ticket": t["text"], "order": order, "stock": stock})
    return items


def items_path(version):
    return os.path.join(DATA, f"items_{version}.jsonl")


def load_items(version):
    return [json.loads(line) for line in open(items_path(version))]


def split_path(version):
    return os.path.join(DATA, "splits", f"{version}.json")


def load_split(version):
    """ticket_id -> split name"""
    return json.load(open(split_path(version)))["tickets"]


def items_for(version, split):
    s = load_split(version)
    return [it for it in load_items(version) if s[it["ticket_id"]] == split]

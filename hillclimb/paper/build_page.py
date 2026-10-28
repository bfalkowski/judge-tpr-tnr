#!/usr/bin/env python3
"""Build hillclimb.html, the web page for the hill-climbing paper.

The text comes from draft.md and every chart from ../results.json, which analyze.py generates, so the page and the
paper cannot disagree. A figure goes wherever draft.md has a <!-- figure:NAME --> marker on its own line; on GitHub the
markers are invisible. The page uses the same layout and colors as the primer on bfalkowski.github.io.

Usage: python3 hillclimb/paper/build_page.py
"""
import html
import json
import re
from pathlib import Path

import markdown
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
R = json.loads((HERE.parent / "results.json").read_text())
SRC = (HERE / "draft.md").read_text()
OUT = HERE / "hillclimb.html"

# Each climb: (arm, grader, run). Grader colors and names are fixed across every figure.
RUNS = [("key", "answer key", 1), ("c3", "calibrated", 1), ("c3-r2", "calibrated", 2), ("c3-r3", "calibrated", 3),
        ("lenient", "lenient", 1), ("lenient-r2", "lenient", 2), ("lenient-r3", "lenient", 3), ("p2", "weak", 1)]
GCLS = {"answer key": "g-key", "calibrated": "g-cal", "lenient": "g-len", "weak": "g-weak"}
GNAME = {"answer key": "Answer key", "calibrated": "Calibrated", "lenient": "Lenient", "weak": "Weak"}
REPEATED = {"calibrated", "lenient"}
CAL_RUNS, LEN_RUNS = ["c3", "c3-r2", "c3-r3"], ["lenient", "lenient-r2", "lenient-r3"]

esc = html.escape


def minus(s):
    return s.replace("-", "−")


def f2(x):
    return minus(f"{x:.2f}")


def sgn(x, d=1):
    return minus(f"{x:+.{d}f}")


def pct(x, d=0):
    return minus(f"{100 * x:.{d}f}%")


def run_name(g, n):
    return GNAME[g] + (f", run {n}" if g in REPEATED else "")


def round_name(r):
    return "round " + r.lstrip("v")


def tip(*lines):
    """A data-tip attribute; the page script shows it on hover and keyboard focus."""
    return ' data-tip="' + esc(chr(10).join(lines)).replace(chr(10), "&#10;") + '" tabindex="0"'


class Lin:
    def __init__(self, d0, d1, r0, r1):
        self.d0, self.d1, self.r0, self.r1 = d0, d1, r0, r1

    def __call__(self, v):
        return self.r0 + (v - self.d0) * (self.r1 - self.r0) / (self.d1 - self.d0)


def text(x, y, s, cls="lab", anchor="start", extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}"{extra}>{esc(s)}</text>'


def svg(w, h, inner, label, cls="chart"):
    return (f'<div class="{cls}"><svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
            f'{inner}</svg></div>')


def table(head, rows, num_from=1):
    th = "".join(f"<th>{esc(h)}</th>" for h in head)
    body = "".join("<tr>" + "".join(f'<td{" class=\"n\"" if i >= num_from else ""}>{esc(str(c))}</td>'
                                     for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"


def legend(items):
    """items: (swatch html, label)."""
    return '<div class="legend">' + "".join(f'<span class="k">{sw}{esc(l)}</span>' for sw, l in items) + "</div>"


def dot_sw(cls, hollow=False, shape="circle"):
    if shape == "diamond":
        m = '<path d="M7 1.5 L12.5 7 L7 12.5 L1.5 7 Z" class="mark hollow"/>'
    else:
        m = f'<circle cx="7" cy="7" r="5" class="mark {"hollow" if hollow else "filled"}"/>'
    return f'<svg class="sw-svg {cls}" viewBox="0 0 14 14" aria-hidden="true">{m}</svg>'


def callout(cx, cy, num):
    """A numbered marker on a chart, keyed to a list under it (keeps long notes out of the plot)."""
    return (f'<g class="callout"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="8.5"/>'
            f'<text x="{cx:.1f}" y="{cy + 3.8:.1f}" text-anchor="middle">{num}</text></g>')


def callout_key(notes):
    return '<ol class="callouts">' + "".join(f"<li>{esc(n)}</li>" for n in notes) + "</ol>"


def box_sw(cls):
    return f'<span class="sw {cls}" aria-hidden="true"></span>'


def grader_legend(extra=()):
    return legend([(dot_sw(GCLS[g]), GNAME[g] + (" (J = 1)" if g == "answer key" else ""))
                   for g in ("answer key", "calibrated", "lenient", "weak")] + list(extra))


def judge_j(arm):
    p = R["pre_loop"][arm]
    return p["tpr"] + p["tnr"] - 1


# ---------------------------------------------------------------- figures

def fig_glance():
    cal = R["replicates"]["c3"]
    gains = [100 * r["true_holdout"] for r in cal]
    fp0, fpw = 1 - cal[0]["tnr_baseline"], [1 - r["tnr_winner"] for r in cal]
    bbk = [v for a in CAL_RUNS for v in R["breaks_by_kind"][a]]
    ob, oc = sum(v["damage_open"]["broken"] for v in bbk), sum(v["damage_open"]["credited"] for v in bbk)
    vis = [v for a in LEN_RUNS for v in R["visibility"][a]]
    good_reverts = sum(1 for v in vis if v["decision"] == "revert" and v["true_change_rows"] > 0)
    tiles = [
        (f"+{min(gains):.0f} to +{max(gains):.0f} points", "true gain on holdout in each of the three climbs with the calibrated judge"),
        (f"{pct(fp0)} → {100 * min(fpw):.0f}–{pct(max(fpw))}",
         "incorrect decisions that the calibrated judge passed, before and after each climb"),
        (f"{oc} of {ob}", "decisions that the calibrated climbs broke on open tickets, which the judge showed as fixes"),
        (f"{good_reverts} of {len(vis)}", "lenient rounds that the loop reverted, but each round fixed more decisions than it broke"),
    ]
    return ('<section class="glance" aria-label="At a glance">' + "".join(
        f'<div class="tile"><div class="v">{esc(v)}</div><div class="l">{esc(l)}</div></div>' for v, l in tiles)
            + "</section>")


def fig_shrink():
    W, H, L, Rm, T, B = 680, 300, 52, 168, 14, 44
    x, y = Lin(-10, 10, L, W - Rm), Lin(-10, 10, H - B, T)
    g = []
    for v in (-10, -5, 0, 5, 10):
        g.append(f'<line x1="{L}" x2="{W - Rm}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="{"axis" if v == 0 else "grid"}"/>')
        g.append(f'<line x1="{x(v):.1f}" x2="{x(v):.1f}" y1="{H - B}" y2="{H - B + 5}" class="axis"/>')
        g.append(text(x(v), H - B + 20, minus(f"{v:+d}" if v else "0"), "tick", "middle"))
        g.append(text(L - 8, y(v) + 4, minus(f"{v:+d}" if v else "0"), "tick", "end"))
    g.append(f'<line x1="{x(0):.1f}" x2="{x(0):.1f}" y1="{T}" y2="{H - B}" class="axis"/>')
    g.append(f'<line x1="{L}" x2="{W - Rm}" y1="{H - B}" y2="{H - B}" class="axis"/>')
    g.append(text((L + W - Rm) / 2, H - 6, "True change (points)", "lab m", "middle"))
    g.append(text(14, (T + H - B) / 2, "Change the judge shows (points)", "lab m", "middle",
                  f' transform="rotate(-90 14 {(T + H - B) / 2:.1f})"'))
    rows, labels = [], []
    for arm, gname in (("key", "answer key"), ("c3", "calibrated"), ("lenient", "lenient"), ("p2", "weak")):
        J = judge_j(arm)
        rows.append([GNAME[gname], f2(R["pre_loop"][arm]["tpr"]), f2(R["pre_loop"][arm]["tnr"]), f2(J), sgn(10 * J)])
        g.append(f'<g class="{GCLS[gname]}"><line x1="{x(-10):.1f}" y1="{y(-10 * J):.1f}" x2="{x(10):.1f}" '
                 f'y2="{y(10 * J):.1f}" class="line"/>'
                 f'<g class="pt"{tip(f"{GNAME[gname]}: J = {f2(J)}", f"a true +10 points shows as {sgn(10 * J)}")}>'
                 f'<circle cx="{x(10):.1f}" cy="{y(10 * J):.1f}" r="12" class="hit"/>'
                 f'<circle cx="{x(10):.1f}" cy="{y(10 * J):.1f}" r="4.5" class="mark filled"/></g></g>')
        labels.append([y(10 * J), f"{GNAME[gname]}, J = {f2(J)}"])
    labels.sort()
    for i in range(1, len(labels)):  # keep end labels at least 15px apart
        labels[i][0] = max(labels[i][0], labels[i - 1][0] + 15)
    for ly, s in labels:
        g.append(text(x(10) + 12, ly + 5, s, "lab em"))
    body = svg(W, H, "".join(g), "Lines of slope J for each grader: the change a judge shows against the true change")
    cap = ("The uniform-error model. If the TPR and TNR of a judge are the same for all outputs, the judge shows each "
           "change at J times its true size. Each line uses the J of one grader on the train decisions of the baseline. "
           "The climbs show where this model is not correct.")
    return body, cap, table(["Grader", "TPR", "TNR", "J", "A true +10 points shows as"], rows)


def fig_loop():
    split = ('<div class="split" aria-label="The 400 tickets: 120 train, 120 validation, 160 holdout">'
             '<span class="tr" style="flex:120">Train · 120</span>'
             '<span class="va" style="flex:120">Validation · 120</span>'
             '<span class="ho" style="flex:160">Holdout · 160</span></div>')
    steps = [("Read", "A new analyzer reads the train transcripts and grades of the current version.", "Train"),
             ("Change", "It proposes one change to the decision instructions or to the action descriptions.", ""),
             ("Run", "The agent runs each ticket two times. The grader of the climb grades each decision.", ""),
             ("Decide", "If the train and validation pass rates both increase, keep the change. If not, revert it.",
              "Train and validation")]
    flow = '<ol class="flow">' + "".join(
        f'<li><b>{esc(h)}</b>{esc(t)}' + (f'<span class="uses">uses: {esc(u)}</span>' if u else "") + "</li>"
        for h, t, u in steps) + "</ol>"
    note = ('<p class="flow-note">The next round starts from the last kept version. The loop does not use the holdout '
            'tickets. The answer key grades them, and all other decisions, only after the climbs.</p>')
    cap = "The 400 tickets, and one round of the loop with the sets that each step uses."
    return split + flow + note, cap, None


def fig_outcomes():
    rows = []
    for arm, g, n in RUNS:
        a = R["arms"][arm]
        rev = [d for d in a["decisions"] if d["loop"] == "revert" and d["true_holdout_change_vs_current"] > 0]
        best = max((d["true_holdout_change_vs_current"] for d in rev), default=None)
        rows.append((arm, g, n, 100 * a["grader_holdout_delta"], 100 * a["true_holdout_delta"],
                     None if best is None else 100 * best))
    W, L, Rm, T, B, pitch, gap = 680, 150, 56, 10, 40, 30, 12
    groups = [r[1] for r in rows]
    nsep = sum(1 for i in range(1, len(groups)) if groups[i] != groups[i - 1])
    H = T + pitch * len(rows) + gap * nsep + B
    x = Lin(-2, 22, L, W - Rm)
    g = []
    for v in (0, 5, 10, 15, 20):
        g.append(f'<line x1="{x(v):.1f}" x2="{x(v):.1f}" y1="{T}" y2="{H - B + 4}" class="{"axis" if v == 0 else "grid"}"/>')
        g.append(text(x(v), H - B + 20, minus(f"{v:+d}" if v else "0"), "tick", "middle"))
    g.append(text((L + W - Rm) / 2, H - 4, "Change in pass rate on the 160 holdout tickets (points)", "lab m", "middle"))
    yy, data = T + pitch / 2, []
    for i, (arm, gname, n, judge, true, best) in enumerate(rows):
        if i and gname != rows[i - 1][1]:
            yy += gap
        cls = GCLS[gname]
        g.append(text(L - 12, yy + 4, run_name(gname, n), "lab", "end"))
        parts = [f'<g class="{cls}">']
        if best is not None:
            parts.append(f'<line x1="{x(0):.1f}" x2="{x(best):.1f}" y1="{yy:.1f}" y2="{yy:.1f}" class="ref"/>')
            parts.append(f'<g class="pt"{tip(run_name(gname, n), f"best change the loop reverted: true {sgn(best)} points")}>'
                         f'<circle cx="{x(best):.1f}" cy="{yy:.1f}" r="12" class="hit"/>'
                         f'<path d="M{x(best):.1f} {yy - 6:.1f} L{x(best) + 6:.1f} {yy:.1f} L{x(best):.1f} {yy + 6:.1f} '
                         f'L{x(best) - 6:.1f} {yy:.1f} Z" class="mark hollow"/></g>')
            parts.append(text(x(best) + 11, yy + 4, f"{sgn(best)} reverted", "lab m"))
        if abs(judge - true) > 0.05:
            parts.append(f'<line x1="{x(judge):.1f}" x2="{x(true):.1f}" y1="{yy:.1f}" y2="{yy:.1f}" class="conn"/>')
        lines = [run_name(gname, n), f"true change {sgn(true)} points", f"change from the climb's own judge: {sgn(judge)}"]
        parts.append(f'<g class="pt"{tip(*lines)}><circle cx="{x(true):.1f}" cy="{yy:.1f}" r="12" class="hit"/>'
                     + (f'<circle cx="{x(judge):.1f}" cy="{yy:.1f}" r="5" class="mark hollow"/>' if abs(judge - true) > 0.05 else "")
                     + f'<circle cx="{x(true):.1f}" cy="{yy:.1f}" r="5" class="mark filled"/></g>')
        if gname == "answer key":
            parts.append(text(x(true) + 12, yy + 4, sgn(true), "lab m"))
        parts.append("</g>")
        g.append("".join(parts))
        data.append([run_name(gname, n), sgn(judge), sgn(true), "" if best is None else sgn(best)])
        yy += pitch
    lg = legend([(dot_sw("g-ink"), "true change (answer key)"), (dot_sw("g-ink", hollow=True), "change from the climb's own judge"),
                 (dot_sw("g-ink", shape="diamond"), "true gain of the best reverted change")])
    body = lg + svg(W, H, "".join(g), "Holdout gain per climb: the judge's change and the true change")
    cap = ("The gain on the holdout tickets, from the baseline to the final version of each climb. The hollow marker is "
           "the change from the climb's own grader. The filled marker is the change from the answer key. The calibrated "
           "judge showed each gain as larger than the true gain. The lenient climbs kept no change, but each climb "
           "reverted a change that truly improved the agent.")
    return body, cap, table(["Climb", "Judge's change", "True change", "Best reverted change (true)"], data)


def fig_jscatter():
    W, L, B, T = 560, 58, 52, 12
    S = W - L - 14
    H = T + S + B
    x, y = Lin(-0.3, 1.05, L, L + S), Lin(-0.3, 1.05, T + S, T)
    g = []
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        g.append(f'<line x1="{L}" x2="{L + S}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="{"axis" if v == 0 else "grid"}"/>')
        g.append(f'<line x1="{x(v):.1f}" x2="{x(v):.1f}" y1="{T + S}" y2="{T + S + 5}" class="axis"/>')
        g.append(text(x(v), T + S + 20, f2(v), "tick", "middle"))
        g.append(text(L - 8, y(v) + 4, f2(v), "tick", "end"))
    g.append(f'<line x1="{x(0):.1f}" x2="{x(0):.1f}" y1="{T}" y2="{T + S}" class="axis"/>')
    g.append(f'<line x1="{L}" x2="{L + S}" y1="{T + S}" y2="{T + S}" class="axis"/>')
    g.append(f'<line x1="{x(-0.3):.1f}" y1="{y(-0.3):.1f}" x2="{x(1.05):.1f}" y2="{y(1.05):.1f}" class="ref"/>')
    for num, (cx_, cy_) in ((1, (-0.2, 1.0)), (2, (0.95, -0.2)), (3, (0.38, 0.38))):
        g.append(callout(x(cx_), y(cy_), num))
    g.append(text(L + S / 2, H - 8, "J on fixes: the part of each true fix that the judge detects", "lab m", "middle"))
    g.append(text(14, T + S / 2, "J on breaks: the part of each true break that the judge detects", "lab m", "middle",
                  f' transform="rotate(-90 14 {T + S / 2:.1f})"'))
    data, pts = [], []
    for arm, gname, n in RUNS:
        for v in R["visibility"][arm]:
            data.append([run_name(gname, n), round_name(v["round"]), "kept" if v["decision"] == "keep" else "reverted",
                         f2(v["j_fix"]), f2(v["j_break"]), sgn(v["true_change_rows"], 0), sgn(v["grader_change_rows"], 0)])
            if gname == "answer key" and pts and pts[-1][0] == "answer key":
                continue  # the three answer-key rounds all sit at (1, 1)
            pts.append((gname, n, v))
    for gname, n, v in pts:
        cx, cy = x(v["j_fix"]), y(v["j_break"])
        kept = v["decision"] == "keep"
        name = "Answer key, all three rounds" if gname == "answer key" else f"{run_name(gname, n)}, {round_name(v['round'])}"
        lines = [f"{name} ({'kept' if kept else 'reverted'})", f"J on fixes {f2(v['j_fix'])}, J on breaks {f2(v['j_break'])}",
                 f"true change {sgn(v['true_change_rows'], 0)} decisions, the judge saw {sgn(v['grader_change_rows'], 0)}"]
        g.append(f'<g class="pt {GCLS[gname]}"{tip(*lines)}><circle cx="{cx:.1f}" cy="{cy:.1f}" r="12" class="hit"/>'
                 f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.5" class="mark {"filled" if kept else "hollow"}"/></g>')
    g.append(text(x(0.95), y(1.0) + 5, "Answer key", "lab em", "end"))
    g.append(text(x(0.07), y(0.70) + 5, "Lenient", "lab em"))
    g.append(text(x(0.0), y(0.205) + 5, "Weak", "lab em", "middle"))
    g.append(text(x(1.0), y(0.30) + 5, "Calibrated", "lab em", "end"))
    lg = grader_legend([(dot_sw("g-ink"), "kept"), (dot_sw("g-ink", hollow=True), "reverted")])
    key = callout_key(["Above the diagonal, the judge does not detect all the fixes. Real gains look smaller, or look like losses.",
                       "Below the diagonal, the judge does not detect all the breaks. Losses look smaller, or look like gains.",
                       "On the diagonal, J on fixes is equal to J on breaks. This is the uniform-error model."])
    body = lg + svg(W, H, "".join(g), "J on fixes against J on breaks for every round", "chart square") + key
    cap = ("Each round of each climb, placed by the part of its true fixes and true breaks that the judge detected. The data "
           "is the train and validation decisions. Each round is compared with the version that the loop tested it "
           "against. In the uniform-error model, each round is on the diagonal. Only the rounds of the answer key are on "
           "it. The rounds of the lenient judge are above it, and the rounds of the calibrated judge are below it.")
    return body, cap, table(["Climb", "Round", "Loop's choice", "J on fixes", "J on breaks", "True change (decisions)",
                             "Judge's change"], data, num_from=3)


def fig_waffle():
    t = R["transitions"]["lenient"][1]
    assert t["round"] == "v2"
    fx, bk = t["fixed"], t["broken"]
    cats = [("w-good", "judge changed in the correct direction"), ("w-pp", "judge passed it before and after"),
            ("w-ff", "judge failed it before and after"), ("w-bad", "judge changed in the incorrect direction")]
    fixed = [("w-good", fx.get("0->1", 0)), ("w-pp", fx.get("1->1", 0)), ("w-ff", fx.get("0->0", 0)), ("w-bad", fx.get("1->0", 0))]
    broken = [("w-good", bk.get("1->0", 0)), ("w-pp", bk.get("1->1", 0)), ("w-ff", bk.get("0->0", 0)), ("w-bad", bk.get("0->1", 0))]
    what = {"w-good": ("changed from fail to pass", "changed from pass to fail"), "w-pp": ("passed before and after",) * 2,
            "w-ff": ("failed before and after",) * 2, "w-bad": ("changed from pass to fail", "changed from fail to pass")}

    def panel(title, parts, i):
        n = sum(k for _, k in parts)
        kind = ("Fixed", "Broken")[i]
        cells = "".join(f'<span class="cell {c}"{tip(f"{kind} decision: the judge {what[c][i]}")}></span>'
                        for c, k in parts for _ in range(k))
        counts = " · ".join(f"{k} {what[c][i]}" for c, k in parts if k)
        return (f'<div class="wpanel"><div class="wtitle">{esc(title.replace("N", str(n)))}</div>'
                f'<div class="waffle">{cells}</div><div class="wcounts">{esc(counts)}</div></div>')

    body = (legend([(box_sw(c), l) for c, l in cats]) + '<div class="wpanels">'
            + panel("N decisions that the change truly fixed", fixed, 0)
            + panel("N decisions that it truly broke", broken, 1) + "</div>")
    cap = ("The lenient judge, run 1, round 2. Each square is a train or validation decision that the change truly fixed "
           "or broke. The color shows what the judge did. For the fixed decisions, the judge changed 4 from fail to pass "
           "and 4 from pass to fail. Thus the fixes gave no net increase. Most of the fixed decisions that the judge "
           "failed before and after are correct escalations, which this judge fails.")
    return body, cap, None


def fig_breaks():
    rows = []
    for arm in CAL_RUNS:
        n = dict((a, k) for a, _, k in RUNS)[arm]
        for v in R["breaks_by_kind"][arm]:
            o, r = v["damage_open"], v["rest"]
            segs = [("w-good", o["charged"] + r["charged"]),
                    ("w-ff", o["broken"] - o["charged"] - o["credited"] + r["broken"] - r["charged"] - r["credited"]),
                    ("w-bad2", r["credited"]), ("w-bad", o["credited"])]
            rows.append((n, v["round"], v["decision"], segs, o["broken"] + r["broken"]))
    W, L, Rm, T, B, pitch, gap, bh = 680, 176, 70, 6, 40, 30, 12, 18
    nsep = sum(1 for i in range(1, len(rows)) if rows[i][0] != rows[i - 1][0])
    H = T + pitch * len(rows) + gap * nsep + B
    x = Lin(0, 50, L, W - Rm)
    g = []
    for v in (0, 10, 20, 30, 40, 50):
        g.append(f'<line x1="{x(v):.1f}" x2="{x(v):.1f}" y1="{T}" y2="{H - B + 4}" class="{"axis" if v == 0 else "grid"}"/>')
        g.append(text(x(v), H - B + 20, str(v), "tick", "middle"))
    g.append(text((L + W - Rm) / 2, H - 4, "Train and validation decisions that the change truly broke", "lab m", "middle"))
    what = {"w-good": "the judge changed it from pass to fail", "w-ff": "the verdict of the judge did not change",
            "w-bad2": "the judge changed it from fail to pass (other tickets)",
            "w-bad": "the judge changed it from fail to pass (open tickets)"}
    yy, data = T + pitch / 2, []
    for i, (n, rnd, dec, segs, tot) in enumerate(rows):
        if i and n != rows[i - 1][0]:
            yy += gap
        g.append(text(L - 12, yy + 4, f"Run {n}, {round_name(rnd)} ({'kept' if dec == 'keep' else 'reverted'})", "lab", "end"))
        x0 = 0
        for c, k in segs:
            if not k:
                continue
            xa, xb = x(x0), x(x0 + k) - 2
            g.append(f'<rect x="{xa:.1f}" y="{yy - bh / 2:.1f}" width="{max(xb - xa, 1):.1f}" height="{bh}" class="seg {c}"'
                     f'{tip(f"Run {n}, {round_name(rnd)}", f"{k} broken decisions: {what[c]}")}/>')
            if c == "w-bad" and xb - xa >= 18:
                g.append(text((xa + xb) / 2, yy + 4.5, str(k), "inlab", "middle"))
            x0 += k
        g.append(text(x(tot) + 6, yy + 4, f"{tot}", "lab m"))
        data.append([f"Run {n}", round_name(rnd), "kept" if dec == "keep" else "reverted", tot] + [k for _, k in segs])
        yy += pitch
    lg = legend([(box_sw("w-good"), "pass to fail"), (box_sw("w-ff"), "no change in the verdict"),
                 (box_sw("w-bad2"), "fail to pass, other tickets"), (box_sw("w-bad"), "fail to pass, open tickets")])
    body = lg + svg(W, H, "".join(g), "Broken decisions per calibrated round, by what the judge did")
    cap = ("Each decision that a change in the calibrated climbs truly broke, for each round of the three runs. The "
           "judge changed most ordinary breaks from pass to fail. It changed each break on the open tickets from fail "
           "to pass, as if it were a fix.")
    return body, cap, table(["Run", "Round", "Loop's choice", "Broken", "Pass to fail", "No change",
                             "Fail to pass, other", "Fail to pass, open tickets"], data, num_from=3)


def fig_drift():
    reps = R["replicates"]["c3"]
    base_open = R["drift_by_category"]["c3"]["baseline"]["damage_open"]["mistakes"]
    W, H, T, B = 700, 260, 30, 34
    panels = [("Incorrect decisions on the open tickets", base_open, [r["open_mistakes_winner"] for r in reps], 20,
               lambda v: f"{v:.0f}", (0, 5, 10, 15, 20)),
              ("Incorrect decisions that the judge passed", 1 - reps[0]["tnr_baseline"], [1 - r["tnr_winner"] for r in reps],
               0.30, lambda v: pct(v), (0, 0.1, 0.2, 0.3))]
    g, data = [], []
    for p, (title, b, ws, top, fmt, ticks) in enumerate(panels):
        x0 = 44 + p * 340
        xa, xb = x0 + 30, x0 + 180
        y = Lin(0, top, H - B, T)
        g.append(text(x0 - 8, 14, title, "lab", "start"))
        for t in ticks:
            g.append(f'<line x1="{x0}" x2="{xb + 20}" y1="{y(t):.1f}" y2="{y(t):.1f}" class="{"axis" if t == 0 else "grid"}"/>')
            g.append(text(x0 - 6, y(t) + 4, fmt(t), "tick", "end"))
        g.append(text(xa, H - B + 18, "baseline", "tick", "middle"))
        g.append(text(xb, H - B + 18, "final version", "tick", "middle"))
        for i, w in enumerate(ws):
            g.append(f'<g class="g-cal"><line x1="{xa}" y1="{y(b):.1f}" x2="{xb}" y2="{y(w):.1f}" class="line"/>'
                     f'<g class="pt"{tip(f"Calibrated, run {i + 1}", f"{title}: {fmt(b)} at baseline, {fmt(w)} at the final version")}>'
                     f'<circle cx="{xb}" cy="{y(w):.1f}" r="12" class="hit"/>'
                     f'<circle cx="{xb}" cy="{y(w):.1f}" r="4.5" class="mark filled"/></g></g>')
        g.append(f'<g class="g-cal"><circle cx="{xa}" cy="{y(b):.1f}" r="4.5" class="mark filled"/></g>')
        g.append(text(xa - 10, y(b) + 4, fmt(b), "lab m", "end"))
        labs = sorted([[y(w), fmt(w), i + 1] for i, w in enumerate(ws)])
        merged = []
        for ly, s, run in labs:
            if merged and merged[-1][1] == s:
                merged[-1][2].append(run)
            else:
                merged.append([ly, s, [run]])
        for i in range(1, len(merged)):
            merged[i][0] = max(merged[i][0], merged[i - 1][0] + 15)
        for ly, s, runs in merged:
            who = "run " + str(runs[0]) if len(runs) == 1 else "runs " + " and ".join(map(str, sorted(runs)))
            g.append(text(xb + 12, ly + 5, f"{s} ({who})", "lab em"))
        data.append([title, fmt(b)] + [fmt(w) for w in ws])
    body = svg(W, H, "".join(g), "Incorrect decisions on the open tickets, and the fraction that the judge passed")
    cap = ("Each calibrated climb moved incorrect decisions of the agent to the open tickets, where this judge passes "
           "them. The data is the validation and holdout decisions. The fraction of all incorrect decisions that the "
           "judge passed (1 − TNR) increased in each run.")
    return body, cap, table(["Measure", "Baseline", "Run 1", "Run 2", "Run 3"], data)


def fig_procedure():
    sec = SRC.split("## 7.")[1].split("## 8.")[0]
    steps = re.findall(r"\*\*(Before|During|After) the climb: (.+?)\.\*\* \*(.+?)\*", sec, re.S)
    cols = {}
    for phase, step, ev in steps:
        step, ev = " ".join(step.split()), " ".join(ev.split())
        cls = "solid" if ev.startswith("Shown in this study") else "dashed" if "hypothesis" in ev.lower() else "outline"
        cols.setdefault(phase, []).append((step[0].upper() + step[1:], ev.rstrip("."), cls))
    out = '<div class="proc">'
    for phase in ("Before", "During", "After"):
        out += f'<div class="ph"><h4>{phase} the climb</h4>' + "".join(
            f'<div class="step">{esc(s)}<br><span class="badge {c}">{esc(e)}</span></div>' for s, e, c in cols[phase]) + "</div>"
    out += "</div>"
    cap = "The procedure in this section. Each tag shows how strongly this study supports the step."
    return out, cap, None


def fig_labels():
    W, L, Rm, T, B, rowh = 680, 70, 20, 14, 40, 76
    ks = ["10", "20", "30"]
    H = T + rowh * len(ks) + B
    x = Lin(0.5, 1.0, L, W - Rm)
    g = []
    for v in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        g.append(f'<line x1="{x(v):.1f}" x2="{x(v):.1f}" y1="{T}" y2="{H - B + 4}" class="grid"/>')
        g.append(text(x(v), H - B + 20, pct(v), "tick", "middle"))
    g.append(text((L + W - Rm) / 2, H - 4, "Probability that k labelled decisions give the correct direction", "lab m", "middle"))
    pts = [(gname, n, v) for arm, gname, n in RUNS for v in R["label_the_diff"][arm]]
    data = [[run_name(gn, n), round_name(v["round"]), v["changed_rows"], sgn(v["true_net"], 0)]
            + [pct(v["agree"][k], 1) for k in ks] for gn, n, v in pts]
    lanes = [0, -9, 9, -18, 18, -27, 27]
    worst = min(pts, key=lambda p: p[2]["agree"]["20"])
    for i, k in enumerate(ks):
        cy0 = T + rowh * i + rowh / 2
        g.append(f'<line x1="{L}" x2="{W - Rm}" y1="{cy0:.1f}" y2="{cy0:.1f}" class="grid"/>')
        g.append(text(L - 12, cy0 + 4, f"k = {k}", "lab", "end"))
        placed = []
        for gname, n, v in sorted(pts, key=lambda p: p[2]["agree"][k]):
            cx = x(max(v["agree"][k], 0.5))
            lane = next((ln for ln in lanes if all(abs(cx - px) > 11 or ln != pl for px, pl in placed)), lanes[-1])
            placed.append((cx, lane))
            cy = cy0 + lane
            lines = [f"{run_name(gname, n)}, {round_name(v['round'])}",
                     f"{pct(v['agree'][k], 1)} with k = {k}",
                     f"true net change {sgn(v['true_net'], 0)} in {v['changed_rows']} changed decisions"]
            g.append(f'<g class="pt {GCLS[gname]}"{tip(*lines)}><circle cx="{cx:.1f}" cy="{cy:.1f}" r="11" class="hit"/>'
                     f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" class="mark filled"/></g>')
            if k == "20" and (gname, n, v) == worst:
                g.append(f'<line x1="{cx:.1f}" y1="{cy + 7:.1f}" x2="{cx:.1f}" y2="{cy + 22:.1f}" class="leader"/>')
                g.append(text(cx - 4, cy + 34, f"{run_name(gname, n)}, {round_name(v['round'])}: net "
                              f"{sgn(v['true_net'], 0)} in {v['changed_rows']} changed decisions", "lab m"))
    body = grader_legend() + svg(W, H, "".join(g), "Chance that k labelled changed decisions get the direction right, per round")
    cap = ("For each of the 18 rounds: the probability that k changed decisions, selected at random and labelled by a "
           "person, give the same direction as the true net change. These are exact probabilities. The one difficult "
           "round had a net change near zero.")
    return body, cap, table(["Climb", "Round", "Changed decisions", "True net change", "k = 10", "k = 20", "k = 30"],
                            data, num_from=2)


FIGURES = {"shrink": fig_shrink, "loop": fig_loop, "outcomes": fig_outcomes, "jscatter": fig_jscatter,
           "waffle": fig_waffle, "breaks": fig_breaks, "drift": fig_drift, "procedure": fig_procedure,
           "labels": fig_labels}


# ---------------------------------------------------------------- text

def build_body():
    lines = SRC.split("\n")
    title = lines[0].lstrip("# ").strip()
    h1, _, sub = title.partition("? ")
    byline_md = lines[2]
    rest = "\n".join(lines[3:])
    note_md, _, rest = rest.strip().partition("\n\n")
    abs_md, _, rest = rest.partition("\n\n<!-- figure:glance -->")
    md = markdown.Markdown(extensions=["tables"])
    conv = lambda s: md.reset().convert(s)
    n = [0]

    def place(m):
        name = m.group(1)
        body, cap, data = FIGURES[name]()
        n[0] += 1
        dt = (f'<details class="data"><summary>Show the data</summary><div class="table-wrap">{data}</div></details>'
              if data else "")
        return (f'\n<figure class="fig fig-{name}" id="figure-{n[0]}">{body}<figcaption><b>Fig {n[0]}</b> '
                f'{esc(cap)}</figcaption>{dt}</figure>\n')

    figs = []

    def token(m):
        figs.append(place(m))
        return f"FIGURETOKEN{len(figs) - 1}"

    rest = re.sub(r"<!-- figure:(\w+) -->(?:\n!\[[^\]]*\]\(figures/[^)]*\))?", token, rest)
    body = conv(rest)
    for i, f in enumerate(figs):
        assert body.count(f"<p>FIGURETOKEN{i}</p>") == 1, i
        body = body.replace(f"<p>FIGURETOKEN{i}</p>", f)
    head = (f'<h1>{esc(h1)}?</h1><p class="subtitle">{esc(sub)}</p>'
            f'<p class="byline">{conv(byline_md)[3:-4]}</p><p class="note">{conv(note_md)[3:-4]}</p>'
            f'<div class="abstract">{conv(abs_md)}</div>{fig_glance()}')
    return head, body


SLUGS = {"The question": "question", "Setup": "setup", "Results of the climbs": "climbs", "A judge that passes": "lenient",
         "The climb moves": "calibrated", "A judge with J near zero": "weak", "How to use TPR and TNR": "procedure",
         "Limitations": "limitations", "In practice": "practice", "How this was made": "how-made", "References": "references"}


def polish(body):
    soup = BeautifulSoup(body, "html.parser")
    for h in soup.find_all("h2"):
        t = h.get_text()
        m = re.match(r"(\d+)\.\s+(.*)", t)
        num, name = (m.group(1), m.group(2)) if m else (None, t)
        h["id"] = next((v for k, v in SLUGS.items() if name.startswith(k)), re.sub(r"\W+", "-", name.lower()))
        h.clear()
        if num:
            s = soup.new_tag("span", attrs={"class": "num"})
            s.string = num + "."
            h.append(s)
        h.append(name)
    for p in soup.find_all("p"):  # formulas on their own line become equation blocks
        t = p.get_text().strip()
        only_strong = len(p.contents) == 1 and getattr(p.contents[0], "name", None) == "strong"
        if "=" in t and (only_strong or (len(t) < 70 and not t.endswith("."))) and not p.find_parent("figure"):
            p.name = "div"
            p["class"] = ["eq", "key"] if only_strong else ["eq"]
            if only_strong:
                p.contents[0].unwrap()
    for tb in soup.find_all("table"):
        if tb.find_parent("figure"):
            continue
        heads = [th.get_text().strip() for th in tb.find_all("th")]
        rows = tb.find("tbody").find_all("tr")
        if heads[:2] == ["Grader", "What it is"]:
            for tr in rows:
                for i, td in enumerate(tr.find_all("td")):
                    if heads[i] in ("TPR", "TNR", "J"):
                        bar(soup, td, float(td.get_text()))
        elif "J on fixes" in heads:
            for tr in rows:
                for i, td in enumerate(tr.find_all("td")):
                    if heads[i] in ("J on fixes", "J on breaks"):
                        v = float(td.get_text().replace("−", "-"))
                        tone = "--good" if v >= 0 else "--bad"
                        td["class"] = ["jt", "n"]
                        td["style"] = f"background: color-mix(in srgb, var({tone}) {6 + 34 * min(abs(v), 1):.0f}%, transparent)"
        elif heads and heads[0].startswith("Check on the baseline"):
            for tr in rows:
                tds = tr.find_all("td")
                label = tds[0].get_text()
                for td in tds[1:]:
                    s = td.get_text().strip()
                    v = 0.0 if s.startswith("under") else float(s.rstrip("%"))
                    v = v / 100 if s.endswith("%") else v / 10 if "lowest" in label else v
                    bar(soup, td, v)
        wrap = soup.new_tag("div", attrs={"class": "table-wrap"})
        tb.wrap(wrap)
    return str(soup)


def bar(soup, td, v):
    td["class"] = ["n", "barcell"]
    track = soup.new_tag("span", attrs={"class": "bt", "aria-hidden": "true"})
    track.append(soup.new_tag("span", attrs={"class": "b", "style": f"width:{100 * max(0.0, min(v, 1.0)):.0f}%"}))
    td.append(track)


CSS = (HERE / "page.css").read_text()
JS = (HERE / "page.js").read_text()


def main():
    head, body = build_body()
    page = f"""<title>Can You Trust Your Hill Climb?</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="Applying TPR and TNR to a keep-or-revert loop: eight hill climbs of one support agent against graders of known quality.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@300;400;600;700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{CSS}</style>

<div class="topbar"><div class="container">
  <a class="home" href="https://bfalkowski.github.io/">Bryan Falkowski</a>
  <a href="https://bfalkowski.github.io/#writing">All writing</a>
</div></div>

<main class="container"><article>
{head}
{polish(body)}
</article></main>

<footer>© 2026 Bryan Falkowski · <a href="https://bfalkowski.github.io/">Home</a> · <a href="https://github.com/bfalkowski/judge-tpr-tnr">Code</a></footer>
<div class="tip" id="tip" role="tooltip" hidden></div>
<script>
{JS}</script>
"""
    OUT.write_text(page)
    print(f"wrote {OUT} ({len(page) // 1024} KB)")


if __name__ == "__main__":
    main()

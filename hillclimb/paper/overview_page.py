#!/usr/bin/env python3
"""Build overview.html: the study's goals, its link to the TPR and TNR primer, and its findings, from overview.md.

The charts come from build_page.py, so they use the same data (../results.json) as the paper.
Usage: python3 hillclimb/paper/overview_page.py
"""
import re
import sys
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_page as bp  # noqa: E402

SRC = (HERE / "overview.md").read_text()
OUT = HERE / "overview.html"

EXTRA_CSS = ""  # the chip and h3 styles are in page.css


def main():
    lines = SRC.split("\n")
    title, subtitle, byline = lines[0].lstrip("# ").strip(), lines[2].strip(), lines[4].strip()
    rest = "\n".join(lines[5:]).strip()
    summary, _, body_md = rest.partition("\n## ")
    body_md = "## " + body_md
    md = markdown.Markdown(extensions=["tables"])
    conv = lambda s: md.reset().convert(s)
    figs, n = [], [0]

    def token(m):
        body, cap, data = bp.FIGURES[m.group(1)]()
        n[0] += 1
        dt = (f'<details class="data"><summary>Show the data</summary><div class="table-wrap">{data}</div></details>'
              if data else "")
        figs.append(f'\n<figure class="fig fig-{m.group(1)}" id="figure-{n[0]}">{body}<figcaption><b>Fig {n[0]}</b> '
                    f'{bp.esc(cap)}</figcaption>{dt}</figure>\n')
        return f"FIGURETOKEN{len(figs) - 1}"

    body_md = re.sub(r"<!-- figure:(\w+) -->", token, body_md)
    body = conv(body_md)
    for i, f in enumerate(figs):
        assert body.count(f"<p>FIGURETOKEN{i}</p>") == 1, i
        body = body.replace(f"<p>FIGURETOKEN{i}</p>", f)
    head = (f'<h1>{bp.esc(title)}</h1><p class="subtitle">{bp.esc(subtitle)}</p>'
            f'<p class="byline">{conv(byline)[3:-4]}</p><div class="abstract">{conv(summary)}</div>')
    page = f"""<title>{bp.esc(title)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{bp.esc(subtitle)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@300;400;600;700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{bp.CSS}{EXTRA_CSS}</style>

<div class="topbar"><div class="container">
  <a class="home" href="https://bfalkowski.github.io/">Bryan Falkowski</a>
  <a href="https://bfalkowski.github.io/#writing">All writing</a>
</div></div>

<main class="container"><article>
{head}
{bp.polish(body)}
</article></main>

<footer>© 2026 Bryan Falkowski · <a href="https://bfalkowski.github.io/">Home</a> · <a href="https://github.com/bfalkowski/judge-tpr-tnr">Code</a></footer>
<div class="tip" id="tip" role="tooltip" hidden></div>
<script>
{bp.JS}</script>
"""
    OUT.write_text(page)
    print(f"wrote {OUT} ({len(page) // 1024} KB)")


if __name__ == "__main__":
    main()

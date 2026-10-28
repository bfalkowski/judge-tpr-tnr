#!/usr/bin/env python3
"""Save each figure of hillclimb.html as a PNG in figures/, so draft.md shows the figures too (on GitHub, for example).

Run build_page.py first. Uses the pre-installed Playwright Chromium.
Usage: python3 hillclimb/paper/export_figures.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures"


def main():
    OUT.mkdir(exist_ok=True)
    page_html = ('<!doctype html><html><head><meta charset="utf-8">'
                 '<meta name="viewport" content="width=device-width, initial-scale=1"></head><body>'
                 + (HERE / "hillclimb.html").read_text() + "</body></html>")
    tmp = OUT / "_page.html"
    tmp.write_text(page_html)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 900, "height": 1200}, device_scale_factor=2, color_scheme="light")
            page.goto(tmp.as_uri())
            page.add_style_tag(content="details.data { display: none !important; } .tip { display: none !important; }")
            page.wait_for_timeout(500)
            for fig in page.query_selector_all("figure.fig"):
                name = [c for c in fig.get_attribute("class").split() if c.startswith("fig-")][0][4:]
                fig.screenshot(path=str(OUT / f"{name}.png"))
                print("wrote", OUT / f"{name}.png")
            browser.close()
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Scrape graphical-abstract / TOC figures from publisher pages using headless
Chromium (Playwright), then download each image into assets/pubs/.

Why headless? Many publishers (Science, PNAS, ChemRxiv, AIP) render their
pages client-side, so plain `curl` sees only an empty shell. A real browser
executes the JS and the og:image meta tag appears in the final DOM.

Usage:
    # one-shot run (skip papers whose image already exists)
    .venv-scrape/bin/python scripts/scrape_toc.py

    # re-download everything, even if the file is already there
    .venv-scrape/bin/python scripts/scrape_toc.py --force

    # process only specific filenames
    .venv-scrape/bin/python scripts/scrape_toc.py pnas-king-2025.jpg sci-adv-griesemer-2025.jpg

Add a new paper by appending a (filename, url) tuple to PAPERS. Set url to
None when the venue has no TOC figure (arXiv, meeting abstracts, etc.).
"""

import asyncio
import sys
import urllib.request
from pathlib import Path

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "assets" / "pubs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Chrome-on-Mac UA. playwright-stealth expects a Chrome UA so it can emit
# matching sec-ch-ua client hints.
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)

# (filename, landing page url) — url=None → skip (no TOC exists)
PAPERS = [
    ("sci-adv-griesemer-2025.jpg",   "https://www.science.org/doi/full/10.1126/sciadv.adq1431"),
    ("jacs-daglar-2025.jpg",         "https://pubs.acs.org/doi/10.1021/jacs.5c18608"),
    ("pnas-king-2025.jpg",           "https://www.pnas.org/doi/10.1073/pnas.2510235122"),
    ("chemrxiv-baird-2025.jpg",      "https://chemrxiv.org/engage/chemrxiv/article-details/684a100a1a8f9bdab5a80a26"),
    ("comm-chem-park-2024.jpg",      "https://www.nature.com/articles/s42004-023-01090-2"),
    ("arxiv-llm-2024.jpg",           None),  # arXiv has no TOC figure
    ("npj-cm-li-2023.jpg",           "https://www.nature.com/articles/s41524-023-01068-7"),
    ("mlst-park-2023.jpg",           "https://iopscience.iop.org/article/10.1088/2632-2153/acd434"),
    ("apl-ml-torrisi-2023.jpg",      "https://pubs.aip.org/aip/aml/article/1/2/020901/2895963"),
    ("aps-griesemer-2023.jpg",       None),  # meeting abstract — no TOC
    ("arxiv-zhu-2022.jpg",           None),  # arXiv has no TOC figure
]

META_SELECTORS = [
    'meta[property="og:image"]',
    'meta[name="og:image"]',
    'meta[property="og:image:secure_url"]',
    'meta[name="twitter:image"]',
    'meta[name="twitter:image:src"]',
]


async def extract_image_url(page, url):
    """Load the page and pull the best available preview image URL."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as exc:
        return None, f"goto failed ({exc.__class__.__name__})"

    # Cloudflare challenge: page title is "Just a moment..." while the
    # interstitial runs. With stealth scripts active it usually clears
    # within 5–10 s.
    for _ in range(8):
        title = await page.title()
        if "just a moment" not in title.lower():
            break
        await page.wait_for_timeout(1500)
    await page.wait_for_timeout(2500)

    for selector in META_SELECTORS:
        el = await page.query_selector(selector)
        if el:
            val = await el.get_attribute("content")
            if val:
                return val, selector

    # Last resort: first figure img inside the article body.
    el = await page.query_selector("article img, figure img")
    if el:
        val = await el.get_attribute("src")
        if val:
            return val, "figure img"

    return None, "no preview image found"


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    dest.write_bytes(data)
    return len(data)


async def scrape_one(context, filename, url, force):
    dest = OUTPUT_DIR / filename
    if dest.exists() and not force:
        return f"  SKIP  {filename:30s}  (already exists, {dest.stat().st_size:,} bytes)"
    if url is None:
        return f"  SKIP  {filename:30s}  (no TOC available)"

    page = await context.new_page()
    try:
        img_url, source = await extract_image_url(page, url)
        if not img_url:
            return f"  FAIL  {filename:30s}  {source}"
        try:
            size = download(img_url, dest)
        except Exception as exc:
            return f"  FAIL  {filename:30s}  download error: {exc.__class__.__name__}: {exc}"
        return f"  OK    {filename:30s}  {size:,} bytes  ({source})"
    finally:
        await page.close()


async def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    force = "--force" in sys.argv
    papers = PAPERS
    if args:
        wanted = set(args)
        papers = [(f, u) for (f, u) in PAPERS if f in wanted]
        if not papers:
            print("No papers match. Available filenames:")
            for f, _ in PAPERS:
                print(" ", f)
            sys.exit(1)

    print(f"Scraping {len(papers)} paper(s) into {OUTPUT_DIR.relative_to(ROOT)}/")
    stealth = Stealth(navigator_user_agent_override=UA)
    async with stealth.use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=UA)
        try:
            for filename, url in papers:
                result = await scrape_one(context, filename, url, force)
                print(result)
        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

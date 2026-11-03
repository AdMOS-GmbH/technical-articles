#!/usr/bin/env python3
"""Refresh every article-series page from published LaTeX articles.

Preserves each category page's existing layout and styling.
"""

from html import escape
from pathlib import Path
from update_latest_articles import ROOT, collect_articles

START = "<!-- AUTO-SERIES-ARTICLES:START -->"
END = "<!-- AUTO-SERIES-ARTICLES:END -->"
SERIES_PAGES = {
    "LFN": "lfn",
    "MAC": "mac",
    "RVA": "rva",
    "MOD": "mod",
    "EST": "est",
}


def card(article):
    title = escape(article["title"], quote=True)
    summary_en = escape(article["en"], quote=True)
    image = escape("../" + article["thumbnail"], quote=True)
    url = escape(f'../articles/{article["series"]}/{article["id"]}/', quote=True)
    return (
        f'      <!-- {escape(article["id"])} -->\n'
        '      <section>\n'
        f'        <img src="{image}" alt="{title}">\n'
        '        <div>\n'
        f'          <h3>{title}</h3>\n'
        f'          <p>{summary_en}</p>\n'
        f'          <a href="{url}">Read ►</a>\n'
        '        </div>\n'
        '      </section>'
    )

def main():
    all_articles = collect_articles(limit=None)
    for series, slug in SERIES_PAGES.items():
        page_path = ROOT / slug / "index.html"
        page = page_path.read_text(encoding="utf-8")
        # Series pages sit one level below the site root. Reuse the shared
        # favicon instead of referring to a nonexistent series/assets folder.
        page = page.replace('href="assets/favicon.png"', 'href="../assets/favicon.png"')
        if page.count(START) != 1 or page.count(END) != 1:
            raise ValueError(f"{page_path}: expected exactly one series marker pair")

        series_articles = [a for a in all_articles if a["series"] == series]
        if series_articles:
            content = "\n\n".join(card(article) for article in series_articles)
        else:
            content = '      <p>Coming soon – stay tuned!</p>'

        before, rest = page.split(START, 1)
        _, after = rest.split(END, 1)
        updated = before + START + "\n" + content + "\n      " + END + after
        if updated != page:
            page_path.write_text(updated, encoding="utf-8")
            print(f"Updated {slug}/index.html with {len(series_articles)} articles")
        else:
            print(f"{slug}/index.html already up to date")


if __name__ == "__main__":
    main()

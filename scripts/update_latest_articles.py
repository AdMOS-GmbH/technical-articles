#!/usr/bin/env python3
"""Refresh the homepage's three latest published article cards.

Reads metadata from source/<SERIES>/<ID>/article.tex and only includes articles
that already have a generated articles/<SERIES>/<ID>/index.html.
No third-party Python packages are required.
"""

from datetime import datetime
from html import escape
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HOMEPAGE = ROOT / "index.html"
START = "<!-- AUTO-LATEST-ARTICLES:START -->"
END = "<!-- AUTO-LATEST-ARTICLES:END -->"

SERIES_DE = {
    "LFN": "Niederfrequenzrauschen",
    "MAC": "Messtechnik und Charakterisierung",
    "RVA": "Zuverlässigkeit und Variabilität",
    "MOD": "Modellierung und Simulation",
    "EST": "Zukunftsweisende Halbleitertechnologien",
}

# Keep the existing, professionally edited bilingual summaries on the homepage.
# New articles are still listed automatically even without an override.
EXISTING_TEASERS = {
    "EST/EST001": {
        "de": "Wie neue Transistorarchitekturen, Materialien und Betriebsbedingungen die Grenzen der klassischen Halbleiterskalierung erweitern, von GAAFETs und CFETs bis zu 2D-Materialien und kryogener Elektronik.",
        "en": "How new transistor architectures, materials and operating regimes extend the limits of conventional semiconductor scaling, from GAAFETs and CFETs to 2D materials and cryogenic electronics.",
    },
    "MOD/MOD_001": {
        "de": "Von der physikalischen Bauelementmodellierung bis zur Schaltungs- und Systemsimulation: Warum unterschiedliche Modelle und Abstraktionsebenen benötigt werden.",
        "en": "From physics-based device modeling to circuit and system simulation: why semiconductor engineering requires different models and levels of abstraction.",
    },
    "RVA/RVA_001": {
        "de": "Wie einzelne Defekte die Eigenschaften nanoskaliger Transistoren beeinflussen und die Grenzen zwischen Variabilität und Zuverlässigkeit zunehmend verschwimmen.",
        "en": "How individual defects influence nanoscale transistors and increasingly blur the boundaries between variability and reliability.",
    },
}

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg"}


def macro(tex, name):
    """Return a \newcommand value, including content with nested braces."""
    pattern = r"\\newcommand\s*\{\s*\\" + re.escape(name) + r"\s*\}\s*\{"
    match = re.search(pattern, tex)
    if not match:
        return ""
    start = match.end()
    depth = 1
    i = start
    while i < len(tex):
        if tex[i] == "{" and (i == 0 or tex[i - 1] != "\\"):
            depth += 1
        elif tex[i] == "}" and (i == 0 or tex[i - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return tex[start:i].strip()
        i += 1
    raise ValueError("Unclosed \\" + name + " macro")


def plain_latex(text):
    """Convert simple LaTeX metadata to safe, readable plain text."""
    text = re.sub(r"\\(?:cite|ref|label|footnote)\{[^}]*\}", "", text)
    for _ in range(3):
        text = re.sub(r"\\(?:textbf|textit|emph|mathrm)\{([^{}]*)\}", r"\1", text)
    text = text.replace(r"\&", "&").replace(r"\%", "%")
    text = text.replace("~", " ").replace("---", " - ").replace("--", "-")
    text = re.sub(r"\\[a-zA-Z]+\*?", "", text)
    text = text.replace("{", "").replace("}", "").replace("$", "")
    return re.sub(r"\s+", " ", text).strip()


def short_text(text, max_length=195):
    if len(text) <= max_length:
        return text
    cut = text[:max_length].rsplit(" ", 1)[0].rstrip(",.: ")
    return cut + "..."


def first_paragraph(tex):
    """Use the introduction as an optional English fallback teaser."""
    text = tex.split(r"\begin{document}", 1)[-1]
    text = re.sub(r"(?m)%[^\n]*$", "", text)
    text = text.split(r"\section", 1)[0]
    text = re.sub(r"\\begin\{(?:figure|table)\}.*?\\end\{(?:figure|table)\}", "", text, flags=re.S)
    text = re.sub(r"\\(?:ArticleMetadata|ArticleTitleBlock|pagestyle\{[^}]*\})", "", text)
    for paragraph in re.split(r"\n\s*\n", text):
        cleaned = plain_latex(paragraph)
        if len(cleaned) > 60:
            return short_text(cleaned)
    return ""


def thumbnail(series, article_id, tex):
    """Choose an optional named thumbnail, or the first published figure."""
    asset_dir = ROOT / "articles" / series / article_id / "assets"
    images = sorted(
        (p for p in asset_dir.iterdir()
         if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
         and p.name.lower() != "bg.jpg"),
        key=lambda p: p.name.lower(),
    ) if asset_dir.is_dir() else []

    requested = Path(macro(tex, "ArticleThumbnail")).name.lower()
    for name in (requested, "thumbnail.png", "thumbnail.jpg", "cover.png", "cover.jpg"):
        if name:
            match = next((p for p in images if p.name.lower() == name), None)
            if match:
                return match.relative_to(ROOT).as_posix()

    first_fig = next((p for p in images if re.fullmatch(r"fig0*1", p.stem, re.I)), None)
    if first_fig:
        return first_fig.relative_to(ROOT).as_posix()
    if images:
        return images[0].relative_to(ROOT).as_posix()
    return "assets/bg2.png"


def collect_articles(limit=3):
    articles = []
    for file in sorted((ROOT / "source").glob("*/*/article.tex")):
        series, article_id = file.parent.parent.name, file.parent.name
        published = ROOT / "articles" / series / article_id / "index.html"
        if not published.is_file():
            continue

        tex = file.read_text(encoding="utf-8")
        title = plain_latex(macro(tex, "ArticleTitle")) or article_id
        raw_date = macro(tex, "ArticleDate")
        try:
            date = datetime.strptime(raw_date, "%d.%m.%Y")
        except ValueError as exc:
            raise ValueError(f"{file}: invalid ArticleDate {raw_date!r}, expected DD.MM.YYYY") from exc

        existing = EXISTING_TEASERS.get(f"{series}/{article_id}", {})
        summary_en = (
            plain_latex(macro(tex, "ArticleSummaryEN"))
            or existing.get("en")
            or first_paragraph(tex)
            or f"Explore this AdMOS technical article on {series}."
        )
        summary_de = (
            plain_latex(macro(tex, "ArticleSummaryDE"))
            or existing.get("de")
            or f"Lesen Sie den neuesten Fachbeitrag aus der Reihe {SERIES_DE.get(series, series)}."
        )

        articles.append({
            "date": date,
            "id": article_id,
            "series": series,
            "title": title,
            "en": short_text(summary_en),
            "de": short_text(summary_de),
            "thumbnail": thumbnail(series, article_id, tex),
        })

    sorted_articles = sorted(articles, key=lambda a: (a["date"], a["id"]), reverse=True)
    return sorted_articles if limit is None else sorted_articles[:limit]


def render_card(article):
    title = escape(article["title"], quote=True)
    summary_de = escape(article["de"], quote=True)
    summary_en = escape(article["en"], quote=True)
    image = escape(article["thumbnail"], quote=True)
    url = escape(f'articles/{article["series"]}/{article["id"]}/', quote=True)
    comment = escape(f'{article["id"]}: {article["date"]:%d.%m.%Y}')
    return (
        f'      <!-- {comment} -->\n'
        f'      <section>\n'
        f'        <img src="{image}" alt="{title}">\n'
        f'        <div>\n'
        f'          <h3>{title}</h3>\n'
        f'          <p data-de="{summary_de}"\n'
        f'             data-en="{summary_en}">\n'
        f'            {summary_de}\n'
        f'          </p>\n'
        f'          <a href="{url}" data-de="Lesen ►" data-en="Read ►">Lesen ►</a>\n'
        f'        </div>\n'
        f'      </section>'
    )


def main():
    page = HOMEPAGE.read_text(encoding="utf-8")
    if page.count(START) != 1 or page.count(END) != 1:
        raise ValueError("Expected exactly one pair of latest-articles markers in index.html")
    articles = collect_articles()
    if not articles:
        raise ValueError("No published articles found, leaving the homepage unchanged")

    before, remainder = page.split(START, 1)
    _, after = remainder.split(END, 1)
    cards = "\n\n".join(render_card(article) for article in articles)
    updated = before + START + "\n\n" + cards + "\n\n      " + END + after

    if updated != page:
        HOMEPAGE.write_text(updated, encoding="utf-8")
        print("Updated index.html with: " + ", ".join(a["id"] for a in articles))
    else:
        print("index.html is already up to date")


if __name__ == "__main__":
    main()

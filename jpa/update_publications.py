#!/usr/bin/env python3
"""Regenerate jpa/index.html from metadata in publication subdirectories."""
import html
import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
INDEX = HERE / "index.html"
START = "<!-- AUTO-JPA-PUBLICATIONS:START -->"
END = "<!-- AUTO-JPA-PUBLICATIONS:END -->"
FIELDS = ("Title", "PublicationType", "PublicationSource", "DOI", "PublicationDate", "ShortAbstract")


def slugify(title):
    plain = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")


def load_publications():
    publications = []
    for folder in sorted(HERE.iterdir()):
        if not folder.is_dir() or folder.name == "assets" or folder.name.startswith("."):
            continue
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}_[a-z0-9]+(?:-[a-z0-9]+)*", folder.name):
            raise ValueError(f"Unexpected publication folder: {folder.name}")
        metadata_file = folder / "metadata.json"
        thumbnail = folder / "thumbnail.png"
        if not metadata_file.is_file() or not thumbnail.is_file():
            raise ValueError(f"{folder}: metadata.json and thumbnail.png required")
        data = json.loads(metadata_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{metadata_file}: JSON object required")
        for field in FIELDS:
            if not isinstance(data.get(field), str):
                raise ValueError(f"{metadata_file}: missing or non-string {field}")
            if field != "DOI" and not data[field].strip():
                raise ValueError(f"{metadata_file}: empty {field}")
        raw = data["PublicationDate"].strip()
        try:
            published = date.fromisoformat(raw)
        except ValueError as exc:
            raise ValueError(f"{metadata_file}: invalid publication date") from exc
        if published.isoformat() != raw:
            raise ValueError(f"{metadata_file}: expected YYYY-MM-DD")
        expected = raw + "_" + slugify(data["Title"])
        if folder.name != expected:
            raise ValueError(f"{folder}: folder should be {expected}")
        doi = data["DOI"].strip()
        fallback = data.get("PublicationURL", "")
        if not isinstance(fallback, str):
            raise ValueError(f"{metadata_file}: PublicationURL must be text")
        link = doi or fallback.strip()
        if doi and not doi.startswith("https://doi.org/"):
            raise ValueError(f"{metadata_file}: DOI must use https://doi.org/")
        parts = urlsplit(link)
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
            raise ValueError(f"{metadata_file}: valid HTTPS DOI/PublicationURL required")
        publications.append({
            "folder": folder.name,
            "date": published,
            "title": data["Title"].strip(),
            "type": data["PublicationType"].strip(),
            "source": data["PublicationSource"].strip(),
            "abstract": data["ShortAbstract"].strip(),
            "url": link,
        })
    return sorted(publications, key=lambda item: (item["date"], item["folder"]), reverse=True)


def card(p):
    e = lambda value: html.escape(value, quote=True)
    folder = e(p["folder"])
    return (
        f"      <!-- {folder} -->\n"
        "      <section>\n"
        f'        <img src="{folder}/thumbnail.png" alt="{e(p["title"])}">\n'
        "        <div>\n"
        f'          <h3>{e(p["title"])}</h3>\n'
        f'          <p>{e(p["abstract"])}</p>\n'
        '          <div class="publication-meta">\n'
        "            <div>\n"
        f'              <span>{e(p["type"])}</span>\n'
        f'              <strong>{e(p["source"])}</strong>\n'
        "            </div>\n"
        "            <div>\n"
        "              <span>Published</span>\n"
        f'              <strong>{p["date"].strftime("%d.%m.%Y")}</strong>\n'
        "            </div>\n"
        "          </div>\n"
        f'          <a href="{e(p["url"])}" target="_blank" rel="noopener noreferrer">Read ►</a>\n'
        "        </div>\n"
        "      </section>"
    )


def main():
    page = INDEX.read_text(encoding="utf-8")
    if page.count(START) != 1 or page.count(END) != 1:
        raise ValueError(f"{INDEX}: expected exactly one marker pair")
    all_items = load_publications()
    before, rest = page.split(START, 1)
    _, after = rest.split(END, 1)
    generated = "\n\n".join(card(item) for item in all_items)
    updated = before + START + "\n" + generated + "\n      " + END + after
    if updated != page:
        INDEX.write_text(updated, encoding="utf-8")
        print(f"Updated JPA cards: {len(all_items)}")
    else:
        print(f"JPA cards up to date: {len(all_items)}")


if __name__ == "__main__":
    main()

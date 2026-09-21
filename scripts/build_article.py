from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]

TEMPLATE_FILE = ROOT / "templates" / "article-template.html"


def extract_command(text, command):
    pattern = rf"\\newcommand{{\\{command}}}{{(.*?)}}"
    match = re.search(pattern, text, re.DOTALL)

    if not match:
        return ""

    value = match.group(1)
    value = re.sub(r"\s+", " ", value).strip()

    return value


def latex_to_html_basic(text):
    text = re.sub(
        r"\\textit{(.*?)}",
        r"<em>\1</em>",
        text
    )

    text = re.sub(
        r"\\textbf{(.*?)}",
        r"<strong>\1</strong>",
        text
    )

    text = text.replace(r"\&", "&")
    text = text.replace(r"\_", "_")

    return text


def make_id(title):
    value = title.lower()

    value = re.sub(r"[^a-z0-9]+", "-", value)

    return value.strip("-")


def parse_article_body(tex):
    start = tex.find(r"\begin{document}")
    end = tex.find(r"\end{document}")

    if start == -1 or end == -1:
        raise RuntimeError("Could not find document body.")

    body = tex[start + len(r"\begin{document}"):end]

    body = re.sub(r"\\pagestyle{.*?}", "", body)
    body = re.sub(r"\\ArticleMetadata", "", body)
    body = re.sub(r"\\ArticleTitleBlock", "", body)

    sections = []

    for match in re.finditer(
        r"\\section{([^}]*)}",
        body
    ):
        sections.append(
            {
                "title": match.group(1),
                "start": match.start(),
                "end": match.end()
            }
        )

    html_parts = []
    toc_parts = []

    for i, section in enumerate(sections):

        content_start = section["end"]

        if i + 1 < len(sections):
            content_end = sections[i + 1]["start"]
        else:
            content_end = len(body)

        title = section["title"]
        section_id = make_id(title)

        content = body[content_start:content_end].strip()

        html_parts.append(
            f'<h2 id="{section_id}">{title}</h2>'
        )

        toc_parts.append(
            f'          <li><a href="#{section_id}">{title}</a></li>'
        )

        paragraphs = [
            p.strip()
            for p in re.split(r"\n\s*\n", content)
            if p.strip()
        ]

        for paragraph in paragraphs:

            if paragraph.startswith(r"\begin{figure}"):
                continue

            if paragraph.startswith(r"\begin{table}"):
                continue

            if paragraph.startswith(r"\begin{thebibliography}"):
                continue

            paragraph = latex_to_html_basic(paragraph)

            paragraph = re.sub(
                r"\\cite{([^}]*)}",
                lambda m: "[" + m.group(1) + "]",
                paragraph
            )

            html_parts.append(
                f"<p>{paragraph}</p>"
            )

    return "\n\n".join(html_parts), "\n".join(toc_parts)


def main():

    if len(sys.argv) != 2:
        print("Usage:")
        print("python scripts/build_article.py source/MOD/MOD_001")
        sys.exit(1)

    article_dir = ROOT / sys.argv[1]

    tex_file = article_dir / "article.tex"

    if not tex_file.exists():
        raise FileNotFoundError(tex_file)

    tex = tex_file.read_text(encoding="utf-8")

    article_id = article_dir.name
    series = article_dir.parent.name

    article_title = extract_command(
        tex,
        "ArticleTitle"
    )

    article_date = extract_command(
        tex,
        "ArticleDate"
    )

    template = TEMPLATE_FILE.read_text(
        encoding="utf-8"
    )

    article_body, toc = parse_article_body(tex)

    output_dir = (
        ROOT
        / "articles"
        / series
        / article_id
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    html = template

    html = html.replace(
        "{{PAGE_TITLE}}",
        article_title
    )

    html = html.replace(
        "{{ARTICLE_TITLE}}",
        article_title
    )

    html = html.replace(
        "{{ARTICLE_DATE}}",
        article_date
    )

    html = html.replace(
        "{{ARTICLE_ID}}",
        article_id
    )

    html = html.replace(
        "{{READING_TIME}}",
        "approx. 5 minutes"
    )

    html = html.replace(
        "{{ARTICLE_BODY}}",
        article_body
    )

    html = html.replace(
        "{{TABLE_OF_CONTENTS}}",
        toc
    )

    html = html.replace(
        "{{ARTICLE_TAGS}}",
        ""
    )

    output_file = output_dir / "index.html"

    output_file.write_text(
        html,
        encoding="utf-8"
    )

    source_figures = article_dir / "figures"
    target_assets = output_dir / "assets"

    if source_figures.exists():

        target_assets.mkdir(
            parents=True,
            exist_ok=True
        )

        for item in source_figures.iterdir():

            if item.is_file():

                shutil.copy2(
                    item,
                    target_assets / item.name
                )

    print(
        f"Generated {output_file}"
    )


if __name__ == "__main__":
    main()

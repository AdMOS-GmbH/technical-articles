from pathlib import Path
import html
import math
import re
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]

TEMPLATE_FILE = ROOT / "templates" / "article-template.html"


# ============================================================
# BASIC LATEX HELPERS
# ============================================================

def remove_comments(text):
    """
    Remove LaTeX comments while keeping escaped percent signs such as \%.
    """

    result = []

    for line in text.splitlines():

        cleaned = []
        i = 0

        while i < len(line):

            if line[i] == "%":

                if i > 0 and line[i - 1] == "\\":
                    cleaned.append(line[i])
                    i += 1
                    continue

                break

            cleaned.append(line[i])
            i += 1

        result.append("".join(cleaned))

    return "\n".join(result)


def find_braced_content(text, start):
    """
    Read a balanced {...} expression beginning at start.

    Returns:
        content, end_position
    """

    if start >= len(text) or text[start] != "{":
        return "", start

    depth = 0
    content = []

    i = start

    while i < len(text):

        char = text[i]

        if char == "{":
            depth += 1

            if depth > 1:
                content.append(char)

        elif char == "}":
            depth -= 1

            if depth == 0:
                return "".join(content), i + 1

            content.append(char)

        else:
            content.append(char)

        i += 1

    return "", start


def extract_newcommand(text, command):
    """
    Extract commands such as:

    \newcommand{\ArticleTitle}{...}
    """

    patterns = [
        rf"\\newcommand\s*{{\\{re.escape(command)}}}\s*",
        rf"\\renewcommand\s*{{\\{re.escape(command)}}}\s*"
    ]

    for pattern in patterns:

        match = re.search(pattern, text)

        if not match:
            continue

        pos = match.end()

        while pos < len(text) and text[pos].isspace():
            pos += 1

        if pos < len(text) and text[pos] == "{":

            value, _ = find_braced_content(text, pos)

            return clean_whitespace(value)

    return ""


def clean_whitespace(text):
    return re.sub(r"\s+", " ", text).strip()


def slugify(text):
    """
    Create a clean HTML ID from a heading.
    """

    value = latex_plain_text(text)
    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value
    )

    return value.strip("-")


def latex_plain_text(text):
    """
    Convert basic LaTeX markup to plain text.
    Useful for titles, captions, alt text and IDs.
    """

    previous = None

    while previous != text:

        previous = text

        text = re.sub(
            r"\\textit\s*{([^{}]*)}",
            r"\1",
            text
        )

        text = re.sub(
            r"\\emph\s*{([^{}]*)}",
            r"\1",
            text
        )

        text = re.sub(
            r"\\textbf\s*{([^{}]*)}",
            r"\1",
            text
        )

    text = text.replace(r"\&", "&")
    text = text.replace(r"\_", "_")
    text = text.replace(r"\%", "%")
    text = text.replace(r"\#", "#")
    text = text.replace(r"\$", "$")

    text = text.replace("``", '"')
    text = text.replace("''", '"')

    text = re.sub(
        r"\\[a-zA-Z]+\*?",
        "",
        text
    )

    text = text.replace("{", "")
    text = text.replace("}", "")

    return clean_whitespace(text)


# ============================================================
# BIBLIOGRAPHY
# ============================================================

def extract_bibliography(body):
    """
    Extract \bibitem entries from thebibliography.

    Returns:
        body_without_bibliography
        bibliography_items
        citation_numbers
    """

    match = re.search(
        r"\\begin{thebibliography}{[^}]*}(.*?)\\end{thebibliography}",
        body,
        re.DOTALL
    )

    if not match:
        return body, [], {}

    bibliography_text = match.group(1)

    pattern = re.compile(
        r"\\bibitem{([^}]+)}"
    )

    matches = list(
        pattern.finditer(bibliography_text)
    )

    items = []
    citation_numbers = {}

    for index, item_match in enumerate(matches):

        key = item_match.group(1).strip()

        start = item_match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(bibliography_text)

        content = bibliography_text[
            start:end
        ].strip()

        number = index + 1

        citation_numbers[key] = number

        items.append(
            {
                "key": key,
                "number": number,
                "content": content
            }
        )

    body = (
        body[:match.start()]
        + "\n"
        + body[match.end():]
    )

    return body, items, citation_numbers


# ============================================================
# INLINE LATEX TO HTML
# ============================================================

def convert_inline(
    text,
    citation_numbers=None,
    reference_map=None
):

    if citation_numbers is None:
        citation_numbers = {}

    if reference_map is None:
        reference_map = {}

    text = clean_whitespace(text)

    if not text:
        return ""

    replacements = {
        r"\&": "___LATEX_AMP___",
        r"\_": "___LATEX_UNDERSCORE___",
        r"\%": "___LATEX_PERCENT___",
        r"\#": "___LATEX_HASH___",
        r"\$": "___LATEX_DOLLAR___"
    }

    for latex_value, placeholder in replacements.items():

        text = text.replace(
            latex_value,
            placeholder
        )

    text = html.escape(
        text,
        quote=False
    )

    text = text.replace(
        "___LATEX_AMP___",
        "&amp;"
    )

    text = text.replace(
        "___LATEX_UNDERSCORE___",
        "_"
    )

    text = text.replace(
        "___LATEX_PERCENT___",
        "%"
    )

    text = text.replace(
        "___LATEX_HASH___",
        "#"
    )

    text = text.replace(
        "___LATEX_DOLLAR___",
        "$"
    )

    text = text.replace(
        "``",
        "&ldquo;"
    )

    text = text.replace(
        "''",
        "&rdquo;"
    )

    text = text.replace(
        "---",
        "—"
    )

    text = text.replace(
        "--",
        "–"
    )

    previous = None

    while previous != text:

        previous = text

        text = re.sub(
            r"\\textit\s*{([^{}]*)}",
            r"<em>\1</em>",
            text
        )

        text = re.sub(
            r"\\emph\s*{([^{}]*)}",
            r"<em>\1</em>",
            text
        )

        text = re.sub(
            r"\\textbf\s*{([^{}]*)}",
            r"<strong>\1</strong>",
            text
        )

    def replace_citation(match):

        keys = [
            key.strip()
            for key in match.group(1).split(",")
        ]

        numbers = []

        for key in keys:

            if key in citation_numbers:

                number = citation_numbers[key]

                numbers.append(
                    f'<a href="#ref-{number}">{number}</a>'
                )

            else:
                numbers.append(
                    html.escape(key)
                )

        return "[" + ", ".join(numbers) + "]"

    text = re.sub(
        r"\\cite\s*{([^}]+)}",
        replace_citation,
        text
    )

    def replace_reference(match):

        label = match.group(1).strip()

        info = reference_map.get(label)

        if not info:
            return "?"

        return (
            f'<a href="#{info["html_id"]}">'
            f'{info["number"]}'
            f'</a>'
        )

    text = re.sub(
        r"\\ref\s*{([^}]+)}",
        replace_reference,
        text
    )

    text = text.replace(
        "~",
        "&nbsp;"
    )

    commands_to_remove = [
        r"\centering",
        r"\justifying",
        r"\noindent",
        r"\small",
        r"\normalsize"
    ]

    for command in commands_to_remove:

        text = text.replace(
            command,
            ""
        )

    return clean_whitespace(text)


# ============================================================
# FIGURE FILE RESOLUTION
# ============================================================

def resolve_figure_filename(
    article_dir,
    latex_path
):
    """
    Resolve the image referenced by \includegraphics.

    Supports:
        figures/Fig1.png
        figures/Fig1
        Fig1.png
        Fig1
    """

    latex_path = latex_path.strip()

    requested = Path(latex_path)

    source_figures = (
        article_dir
        / "figures"
    )

    candidate_name = requested.name

    if not source_figures.exists():
        return candidate_name

    exact = (
        source_figures
        / candidate_name
    )

    if exact.exists():
        return exact.name

    if requested.suffix == "":

        extensions = [
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".svg",
            ".pdf"
        ]

        for extension in extensions:

            candidate = (
                source_figures
                / f"{candidate_name}{extension}"
            )

            if candidate.exists():
                return candidate.name

    requested_stem = (
        requested.stem.lower()
    )

    for item in source_figures.iterdir():

        if not item.is_file():
            continue

        if (
            item.stem.lower()
            == requested_stem
        ):
            return item.name

    return candidate_name


# ============================================================
# FIGURES
# ============================================================

def parse_figures(
    body,
    citation_numbers,
    reference_map,
    article_dir
):

    pattern = re.compile(
        r"\\begin{figure}(?:\[[^\]]*\])?(.*?)\\end{figure}",
        re.DOTALL
    )

    figures = []

    def replacement(match):

        content = match.group(1)

        image_match = re.search(
            r"\\includegraphics(?:\[[^\]]*\])?\s*{([^}]+)}",
            content
        )

        if not image_match:
            return ""

        image_path = (
            image_match
            .group(1)
            .strip()
        )

        image_name = resolve_figure_filename(
            article_dir,
            image_path
        )

        caption = ""

        caption_match = re.search(
            r"\\caption\s*{",
            content
        )

        if caption_match:

            start = (
                caption_match.end()
                - 1
            )

            caption, _ = find_braced_content(
                content,
                start
            )

        label = ""

        label_match = re.search(
            r"\\label\s*{([^}]+)}",
            content
        )

        if label_match:

            label = (
                label_match
                .group(1)
                .strip()
            )

        number = len(figures) + 1

        if label:

            html_id = (
                "figure-"
                + slugify(label)
            )

        else:

            html_id = (
                f"figure-{number}"
            )

        if label:

            reference_map[label] = {
                "type": "figure",
                "number": number,
                "html_id": html_id
            }

        caption_html = convert_inline(
            caption,
            citation_numbers,
            reference_map
        )

        alt_text = html.escape(
            latex_plain_text(caption),
            quote=True
        )

        figure_html = (
            f'<figure id="{html_id}">\n'
            f'  <img '
            f'src="assets/{html.escape(image_name)}" '
            f'alt="{alt_text}">\n'
            f'  <figcaption>'
            f'<span class="caption-label">Figure {number}:</span> '
            f'{caption_html}'
            f'</figcaption>\n'
            f'</figure>'
        )

        token = (
            f"@@FIGURE_{len(figures)}@@"
        )

        figures.append(
            figure_html
        )

        return (
            "\n\n"
            + token
            + "\n\n"
        )

    body = pattern.sub(
        replacement,
        body
    )

    return body, figures


# ============================================================
# TABLES
# ============================================================

def split_table_cells(row):
    """
    Split a LaTeX table row on unescaped &.
    """

    cells = re.split(
        r"(?<!\\)&",
        row
    )

    return [
        cell.strip()
        for cell in cells
    ]


def extract_tabular_content(content):
    """
    Extract the body of a tabular environment while correctly
    handling column specifications such as:

        {@{}ll@{}}
    """

    tabular_start = re.search(
        r"\\begin{tabular}\s*{",
        content
    )

    if not tabular_start:
        return None

    column_spec_start = (
        tabular_start.end()
        - 1
    )

    _, column_spec_end = find_braced_content(
        content,
        column_spec_start
    )

    if (
        column_spec_end
        <= column_spec_start
    ):
        return None

    tabular_end = content.find(
        r"\end{tabular}",
        column_spec_end
    )

    if tabular_end == -1:
        return None

    return content[
        column_spec_end:tabular_end
    ]


def parse_tables(
    body,
    citation_numbers,
    reference_map
):

    pattern = re.compile(
        r"\\begin{table}(?:\[[^\]]*\])?(.*?)\\end{table}",
        re.DOTALL
    )

    tables = []

    def replacement(match):

        content = match.group(1)

        caption = ""

        caption_match = re.search(
            r"\\caption\s*{",
            content
        )

        if caption_match:

            start = (
                caption_match.end()
                - 1
            )

            caption, _ = find_braced_content(
                content,
                start
            )

        label = ""

        label_match = re.search(
            r"\\label\s*{([^}]+)}",
            content
        )

        if label_match:

            label = (
                label_match
                .group(1)
                .strip()
            )

        table_body = extract_tabular_content(
            content
        )

        if table_body is None:
            return ""

        table_body = table_body.replace(
            r"\toprule",
            "\n@@TOPRULE@@\n"
        )

        table_body = table_body.replace(
            r"\midrule",
            "\n@@MIDRULE@@\n"
        )

        table_body = table_body.replace(
            r"\bottomrule",
            "\n@@BOTTOMRULE@@\n"
        )

        rows = re.split(
            r"\\\\",
            table_body
        )

        parsed_rows = []

        header_mode = True

        for row in rows:

            row = row.strip()

            if not row:
                continue

            row = row.replace(
                r"\centering",
                ""
            ).strip()

            if "@@TOPRULE@@" in row:

                row = row.replace(
                    "@@TOPRULE@@",
                    ""
                ).strip()

            if "@@MIDRULE@@" in row:

                before = row.replace(
                    "@@MIDRULE@@",
                    ""
                ).strip()

                if before:

                    parsed_rows.append(
                        (
                            "header",
                            split_table_cells(
                                before
                            )
                        )
                    )

                header_mode = False
                continue

            if "@@BOTTOMRULE@@" in row:

                row = row.replace(
                    "@@BOTTOMRULE@@",
                    ""
                ).strip()

            if not row:
                continue

            cells = split_table_cells(
                row
            )

            if header_mode:

                parsed_rows.append(
                    (
                        "header",
                        cells
                    )
                )

                header_mode = False

            else:

                parsed_rows.append(
                    (
                        "body",
                        cells
                    )
                )

        number = len(tables) + 1

        if label:

            html_id = (
                "table-"
                + slugify(label)
            )

        else:

            html_id = (
                f"table-{number}"
            )

        if label:

            reference_map[label] = {
                "type": "table",
                "number": number,
                "html_id": html_id
            }

        html_lines = [
            f'<div class="table-wrapper" id="{html_id}">',
            "<table>"
        ]

        header_written = False
        body_started = False

        for row_type, cells in parsed_rows:

            if (
                row_type == "header"
                and not header_written
            ):

                html_lines.append(
                    "<thead>"
                )

                html_lines.append(
                    "<tr>"
                )

                for cell in cells:

                    value = convert_inline(
                        cell,
                        citation_numbers,
                        reference_map
                    )

                    value = re.sub(
                        r"</?strong>",
                        "",
                        value
                    )

                    html_lines.append(
                        f"<th>{value}</th>"
                    )

                html_lines.append(
                    "</tr>"
                )

                html_lines.append(
                    "</thead>"
                )

                header_written = True

            else:

                if not body_started:

                    html_lines.append(
                        "<tbody>"
                    )

                    body_started = True

                html_lines.append(
                    "<tr>"
                )

                for cell in cells:

                    value = convert_inline(
                        cell,
                        citation_numbers,
                        reference_map
                    )

                    html_lines.append(
                        f"<td>{value}</td>"
                    )

                html_lines.append(
                    "</tr>"
                )

        if body_started:

            html_lines.append(
                "</tbody>"
            )

        html_lines.append(
            "</table>"
        )

        if caption:

            caption_html = convert_inline(
                caption,
                citation_numbers,
                reference_map
            )

            html_lines.append(
                f'<div class="table-caption">'
                f'<span class="caption-label">Table {number}:</span> '
                f'{caption_html}'
                f'</div>'
            )

        html_lines.append(
            "</div>"
        )

        token = (
            f"@@TABLE_{len(tables)}@@"
        )

        tables.append(
            "\n".join(html_lines)
        )

        return (
            "\n\n"
            + token
            + "\n\n"
        )

    body = pattern.sub(
        replacement,
        body
    )

    return body, tables


# ============================================================
# LISTS
# ============================================================

def parse_lists(
    body,
    citation_numbers,
    reference_map
):

    def convert_list(
        match,
        ordered=False
    ):

        content = match.group(1)

        items = re.split(
            r"\\item\s*",
            content
        )

        items = [
            item.strip()
            for item in items
            if item.strip()
        ]

        tag = (
            "ol"
            if ordered
            else "ul"
        )

        html_items = []

        for item in items:

            item_html = convert_inline(
                item,
                citation_numbers,
                reference_map
            )

            html_items.append(
                f"<li>{item_html}</li>"
            )

        return (
            f"\n\n<{tag}>\n"
            + "\n".join(html_items)
            + f"\n</{tag}>\n\n"
        )

    body = re.sub(
        r"\\begin{itemize}(.*?)\\end{itemize}",
        lambda match: convert_list(
            match,
            ordered=False
        ),
        body,
        flags=re.DOTALL
    )

    body = re.sub(
        r"\\begin{enumerate}(.*?)\\end{enumerate}",
        lambda match: convert_list(
            match,
            ordered=True
        ),
        body,
        flags=re.DOTALL
    )

    return body


# ============================================================
# ARTICLE BODY
# ============================================================

def parse_article_body(
    tex,
    article_dir
):

    document_start = tex.find(
        r"\begin{document}"
    )

    document_end = tex.rfind(
        r"\end{document}"
    )

    if (
        document_start == -1
        or document_end == -1
    ):

        raise RuntimeError(
            "Could not find "
            "\\begin{document} and "
            "\\end{document}."
        )

    body = tex[
        document_start
        + len(r"\begin{document}"):
        document_end
    ]

    body = remove_comments(
        body
    )

    commands_to_remove = [
        r"\pagestyle{empty}",
        r"\ArticleMetadata",
        r"\ArticleTitleBlock"
    ]

    for command in commands_to_remove:

        body = body.replace(
            command,
            ""
        )

    body, bibliography, citation_numbers = (
        extract_bibliography(
            body
        )
    )

    reference_map = {}

    body, figures = parse_figures(
        body,
        citation_numbers,
        reference_map,
        article_dir
    )

    body, tables = parse_tables(
        body,
        citation_numbers,
        reference_map
    )

    body = parse_lists(
        body,
        citation_numbers,
        reference_map
    )

    blocks = []

    toc_entries = []

    def section_replacement(match):

        title = clean_whitespace(
            match.group(1)
        )

        section_id = slugify(
            title
        )

        toc_entries.append(
            {
                "level": 2,
                "title": latex_plain_text(
                    title
                ),
                "id": section_id
            }
        )

        block = (
            f'<h2 id="{section_id}">'
            f'{convert_inline(title, citation_numbers, reference_map)}'
            f'</h2>'
        )

        token = (
            f"@@BLOCK_{len(blocks)}@@"
        )

        blocks.append(
            block
        )

        return (
            "\n\n"
            + token
            + "\n\n"
        )

    body = re.sub(
        r"\\section\s*{([^{}]*)}",
        section_replacement,
        body
    )

    def subsection_replacement(match):

        title = clean_whitespace(
            match.group(1)
        )

        section_id = slugify(
            title
        )

        toc_entries.append(
            {
                "level": 3,
                "title": latex_plain_text(
                    title
                ),
                "id": section_id
            }
        )

        block = (
            f'<h3 id="{section_id}">'
            f'{convert_inline(title, citation_numbers, reference_map)}'
            f'</h3>'
        )

        token = (
            f"@@BLOCK_{len(blocks)}@@"
        )

        blocks.append(
            block
        )

        return (
            "\n\n"
            + token
            + "\n\n"
        )

    body = re.sub(
        r"\\subsection\s*{([^{}]*)}",
        subsection_replacement,
        body
    )

    for index, figure_html in enumerate(
        figures
    ):

        token = (
            f"@@FIGURE_{index}@@"
        )

        block_token = (
            f"@@BLOCK_{len(blocks)}@@"
        )

        blocks.append(
            figure_html
        )

        body = body.replace(
            token,
            block_token
        )

    for index, table_html in enumerate(
        tables
    ):

        token = (
            f"@@TABLE_{index}@@"
        )

        block_token = (
            f"@@BLOCK_{len(blocks)}@@"
        )

        blocks.append(
            table_html
        )

        body = body.replace(
            token,
            block_token
        )

    parts = re.split(
        r"\n\s*\n",
        body
    )

    html_parts = []

    block_pattern = re.compile(
        r"^@@BLOCK_(\d+)@@$"
    )

    for part in parts:

        part = part.strip()

        if not part:
            continue

        block_match = (
            block_pattern.match(
                part
            )
        )

        if block_match:

            index = int(
                block_match.group(1)
            )

            html_parts.append(
                blocks[index]
            )

            continue

        if (
            part.startswith("<ul>")
            or part.startswith("<ol>")
        ):

            html_parts.append(
                part
            )

            continue

        part = re.sub(
            r"\\vspace\s*{[^}]*}",
            "",
            part
        )

        part = re.sub(
            r"\\(?:clearpage|newpage)",
            "",
            part
        )

        part = clean_whitespace(
            part
        )

        if not part:
            continue

        paragraph_html = convert_inline(
            part,
            citation_numbers,
            reference_map
        )

        if paragraph_html:

            html_parts.append(
                f"<p>{paragraph_html}</p>"
            )

    if bibliography:

        reference_id = "references"

        toc_entries.append(
            {
                "level": 2,
                "title": "References",
                "id": reference_id
            }
        )

        html_parts.append(
            f'<h2 id="{reference_id}">'
            f'References'
            f'</h2>'
        )

        html_parts.append(
            '<ol class="references">'
        )

        for item in bibliography:

            content_html = convert_inline(
                item["content"],
                citation_numbers,
                reference_map
            )

            html_parts.append(
                f'<li id="ref-{item["number"]}">'
                f'{content_html}'
                f'</li>'
            )

        html_parts.append(
            "</ol>"
        )

    toc_html = []

    for entry in toc_entries:

        css_class = ""

        if entry["level"] == 3:

            css_class = (
                ' class="toc-subsection"'
            )

        toc_html.append(
            f'          <li{css_class}>'
            f'<a href="#{entry["id"]}">'
            f'{html.escape(entry["title"])}'
            f'</a>'
            f'</li>'
        )

    return (
        "\n\n".join(html_parts),
        "\n".join(toc_html)
    )


# ============================================================
# TAGS
# ============================================================

def build_tags(tex):

    tags_value = extract_newcommand(
        tex,
        "ArticleTags"
    )

    if not tags_value:
        return ""

    tags = [
        tag.strip()
        for tag in tags_value.split(",")
        if tag.strip()
    ]

    return "\n".join(
        f'          '
        f'<span class="tag">'
        f'{html.escape(tag)}'
        f'</span>'
        for tag in tags
    )


# ============================================================
# READING TIME
# ============================================================

def calculate_reading_time(
    article_body_html
):

    plain = re.sub(
        r"<[^>]+>",
        " ",
        article_body_html
    )

    plain = html.unescape(
        plain
    )

    words = re.findall(
        r"\b[\w'-]+\b",
        plain
    )

    minutes = max(
        1,
        math.ceil(
            len(words) / 200
        )
    )

    if minutes == 1:
        return "approx. 1 minute"

    return (
        f"approx. {minutes} minutes"
    )


# ============================================================
# ASSET COPYING
# ============================================================

def copy_assets(
    article_dir,
    output_dir
):

    source_figures = (
        article_dir
        / "figures"
    )

    target_assets = (
        output_dir
        / "assets"
    )

    if source_figures.exists():

        target_assets.mkdir(
            parents=True,
            exist_ok=True
        )

        for item in source_figures.rglob(
            "*"
        ):

            if not item.is_file():
                continue

            relative = item.relative_to(
                source_figures
            )

            destination = (
                target_assets
                / relative
            )

            destination.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            shutil.copy2(
                item,
                destination
            )

    background_candidates = [
        article_dir / "bg.jpg",
        ROOT / "templates" / "bg.jpg"
    ]

    for background in background_candidates:

        if not background.exists():
            continue

        target_assets.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.copy2(
            background,
            target_assets / "bg.jpg"
        )

        break


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 2:

        print("Usage:")
        print(
            "python scripts/build_article.py "
            "source/MOD/MOD_001"
        )

        sys.exit(1)

    article_dir = (
        ROOT
        / sys.argv[1]
    )

    tex_file = (
        article_dir
        / "article.tex"
    )

    if not tex_file.exists():

        raise FileNotFoundError(
            f"Could not find {tex_file}"
        )

    if not TEMPLATE_FILE.exists():

        raise FileNotFoundError(
            f"Could not find {TEMPLATE_FILE}"
        )

    tex = tex_file.read_text(
        encoding="utf-8"
    )

    article_id = (
        article_dir.name
    )

    series = (
        article_dir.parent.name
    )

    article_title = extract_newcommand(
        tex,
        "ArticleTitle"
    )

    article_date = extract_newcommand(
        tex,
        "ArticleDate"
    )

    if not article_title:
        article_title = article_id

    template = TEMPLATE_FILE.read_text(
        encoding="utf-8"
    )

    article_body, toc = parse_article_body(
        tex,
        article_dir
    )

    reading_time = calculate_reading_time(
        article_body
    )

    tags = build_tags(
        tex
    )

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

    copy_assets(
        article_dir,
        output_dir
    )

    page_title = latex_plain_text(
        article_title
    )

    article_title_html = convert_inline(
        article_title
    )

    html_output = template

    replacements = {
        "{{PAGE_TITLE}}":
            html.escape(page_title),

        "{{ARTICLE_TITLE}}":
            article_title_html,

        "{{ARTICLE_DATE}}":
            html.escape(article_date),

        "{{ARTICLE_ID}}":
            html.escape(article_id),

        "{{READING_TIME}}":
            html.escape(reading_time),

        "{{ARTICLE_BODY}}":
            article_body,

        "{{TABLE_OF_CONTENTS}}":
            toc,

        "{{ARTICLE_TAGS}}":
            tags
    }

    for placeholder, value in replacements.items():

        html_output = html_output.replace(
            placeholder,
            value
        )

    output_file = (
        output_dir
        / "index.html"
    )

    output_file.write_text(
        html_output,
        encoding="utf-8"
    )

    print(
        f"Generated {output_file}"
    )

    print(
        f"Article ID: {article_id}"
    )

    print(
        f"Series: {series}"
    )

    print(
        f"Reading time: {reading_time}"
    )


if __name__ == "__main__":
    main()

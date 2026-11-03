# AdMOS Technical Articles

**Practical engineering insights into semiconductor devices, measurement, and modeling.**

The AdMOS Technical Articles website is a collection of accessible, technically grounded articles about semiconductor physics, low-frequency noise, electrical characterization, reliability, compact modeling, simulation, and emerging semiconductor technologies. The aim is to connect fundamental physical mechanisms with the practical methods and challenges faced in research and industry.

This repository contains the **website, LaTeX article sources, and automated publication pipeline**. Authors work primarily with LaTeX, while GitHub Actions generates readable HTML pages, downloadable PDFs, and up-to-date article listings.

> **Current website:** [GitHub Pages](https://admos-gmbh.github.io/technical-articles/)
>
> **Planned destination:** `articles.admos.de` (see section 1).

## 1. Planned migration to articles.admos.de

The website is **currently deployed through GitHub Pages** at:

**https://admos-gmbh.github.io/technical-articles/**

The long-term goal is to make the same site available at:

**https://articles.admos.de/**

This is a planned domain migration, not a completed one. Before switching, the custom domain must be configured in GitHub Pages, its DNS record validated, and HTTPS enabled. Site links should then be checked in the context of the new domain, because the current GitHub Pages project URL contains the additional `/technical-articles/` path.

Until the move is complete, use the GitHub Pages URL for sharing and testing articles.

## 2. Browse the articles

Articles are organized into technical series:

| Series | Subject | Category page |
| --- | --- | --- |
| **LFN** | Low-Frequency Noise | [Browse](https://admos-gmbh.github.io/technical-articles/lfn/) |
| **MAC** | Measurement & Characterization | [Browse](https://admos-gmbh.github.io/technical-articles/mac/) |
| **RVA** | Reliability & Variability | [Browse](https://admos-gmbh.github.io/technical-articles/rva/) |
| **MOD** | Modeling & Simulation | [Browse](https://admos-gmbh.github.io/technical-articles/mod/) |
| **EST** | Emerging Semiconductor Technologies | [Browse](https://admos-gmbh.github.io/technical-articles/est/) |
| **JPA** | Peer-Reviewed Publications | [Browse](https://admos-gmbh.github.io/technical-articles/jpa/) |

The homepage automatically highlights the **three newest published technical articles**, ordered by publication date. Each technical series page lists the published articles in that category. The peer-reviewed publications section is maintained separately.

The technical articles are currently available in **English only**. The homepage displays a short English/German notice about language availability.

## 3. How the publishing system works

```text
Author edits article.tex and figures
                |
                v
          Push to main
                |
                v
       GitHub Actions discovers
       all source/*/*/article.tex
                |
                v
    Compile PDF and generate HTML
                |
                v
  Publish to articles/<SERIES>/<ID>/
                |
                v
  Refresh homepage and series cards
                |
                v
        GitHub Pages deploys
```

The [Build Technical Articles workflow](.github/workflows/build-articles.yml) performs these steps:

1. **Discovery:** Finds each `source/*/*/article.tex`.
2. **PDF generation:** Runs `pdflatex` twice in a TeX Live environment.
3. **HTML generation:** Runs `scripts/build_article.py` using the common article HTML template.
4. **Publishing files:** Copies the resulting PDF, HTML, and assets into `articles/<SERIES>/<ARTICLE_ID>/`, and commits generated changes.
5. **Homepage refresh:** Runs `scripts/update_latest_articles.py` to choose the three newest published articles using `ArticleDate`.
6. **Category refresh:** Runs `scripts/update_series_articles.py` to list published articles under their matching series pages.
7. **Deployment:** GitHub Pages publishes the updated site from the repository.

The article builds are configured to run sequentially to reduce competing Git commits. Listing updates run after the article-building jobs succeed.

### What triggers a build?

Pushing changes to `main` under any of these locations starts the article workflow:

- `source/**`
- `templates/**`
- `scripts/**`
- `.github/workflows/build-articles.yml`

The same workflow can be started manually from [GitHub Actions](https://github.com/AdMOS-GmbH/technical-articles/actions/workflows/build-articles.yml) using **Run workflow**.

A README-only change does not trigger the article-building workflow. Updates to static website files can still trigger the separate GitHub Pages deployment.

## 4. How to add a new technical article

### Step 1. Choose the category and article ID

Create a folder in the relevant series under `source/`. For a new LFN article, for example:

```text
source/LFN/LFN_002/
├── article.tex
├── admos-article.sty
├── admos-letterhead.png
└── figures/
    ├── Fig1.png
    └── Fig2.png
```

Start from the structure of an existing article. Keep the series code consistent with the existing folders: LFN, MAC, RVA, MOD, or EST.

### Step 2. Set the article metadata

Edit the metadata near the top of `article.tex`:

```latex
\documentclass[10pt,a4paper]{article}
\usepackage{admos-article}

\newcommand{\ArticleType}{TECHNICAL ARTICLE}
\newcommand{\ArticleSeries}{Low-Frequency Noise}
\newcommand{\ArticleID}{LFN-002}
\newcommand{\ArticleDate}{15.11.2026}
\newcommand{\ArticleTitle}{Understanding Noise in Modern Devices}
\newcommand{\ArticleSubtitle}{From Device Physics to Measurements}
\newcommand{\ArticleTags}{Low-Frequency Noise, RTN, Device Physics}

\begin{document}
\ArticleMetadata
\ArticleTitleBlock

% Your technical content goes here.

\end{document}
```

**Important conventions:**

- The publication date must follow **DD.MM.YYYY**, for example `15.11.2026`. This date determines the order of the homepage's latest-article cards.
- The title is taken from `ArticleTitle`.
- The **folder name** determines the generated website path and PDF filename, for example `LFN_002`. Keep `ArticleID` consistent as document metadata, although it can follow the printed article-ID convention.
- Keep referenced figures and supporting assets alongside the source. Filename case matters on the Linux build runner.

For more useful article previews, optional metadata can be supplied:

```latex
\newcommand{\ArticleSummaryEN}{A short English description for article listings.}
\newcommand{\ArticleThumbnail}{Fig1.png}
```

The listing scripts can fall back to an introduction excerpt and the first published figure when preview metadata is missing. Some existing article summaries are curated directly in `scripts/update_latest_articles.py`.

### Step 3. Commit source files

Commit `article.tex`, the supporting style and letterhead files, and relevant figure assets. Push to `main`, directly or through a reviewed pull request.

**Do not commit temporary LaTeX artifacts**, such as `.aux`, `.log`, `.out`, or `.synctex.gz`. Avoid manually creating old-style article folders beneath a category page. Published articles belong under the generated `articles/` directory.

### Step 4. Check GitHub Actions

Open [the Actions page](https://github.com/AdMOS-GmbH/technical-articles/actions) and confirm that all required build and listing-update jobs have succeeded. GitHub Pages deployment may finish separately from the compilation jobs.

After publishing the example article, its pages would follow this pattern:

- HTML: `https://admos-gmbh.github.io/technical-articles/articles/LFN/LFN_002/`
- PDF: `https://admos-gmbh.github.io/technical-articles/articles/LFN/LFN_002/LFN_002.pdf`
- Series listing: `https://admos-gmbh.github.io/technical-articles/lfn/`

These are examples, not links to an article that currently exists.

## 5. Local build and preview

For local work, install **Python 3** and a LaTeX distribution that provides `pdflatex`. The publishing workflow uses the TeX Live GitHub Action.

From the repository root, you can compile an existing article and convert it to HTML:

```bash
cd source/LFN/LFN_001
pdflatex -interaction=nonstopmode -halt-on-error article.tex
pdflatex -interaction=nonstopmode -halt-on-error article.tex
cd ../../..
python scripts/build_article.py source/LFN/LFN_001
```

The HTML output is written to `articles/LFN/LFN_001/index.html`. The HTML script does not perform every publishing step. In GitHub Actions, additional steps rename and copy the PDF, upload a build artifact, refresh the category lists, and deploy the website.

The HTML generator and article-listing scripts use Python's standard library.

## 6. Where to make changes

| Goal | Edit |
| --- | --- |
| Change article text, formulas, metadata, or figures | `source/<SERIES>/<ARTICLE_ID>/` |
| Change styling or navigation shared by generated articles | `templates/article-template.html` |
| Change the homepage's general layout or content | `index.html` |
| Change the layout of a technical category | `lfn/index.html`, `mac/index.html`, `rva/index.html`, `mod/index.html`, or `est/index.html` |
| Change the newest-three logic or generated homepage cards | `scripts/update_latest_articles.py` |
| Change generated category article cards | `scripts/update_series_articles.py` |
| Change LaTeX-to-HTML conversion | `scripts/build_article.py` |
| Change publishing automation | `.github/workflows/build-articles.yml` |
| Update peer-reviewed publications | `jpa/index.html` |

**Important:** Do not manually edit generated article cards in the homepage or category pages. The scripts replace the content between these markers:

```html
<!-- AUTO-LATEST-ARTICLES:START -->
<!-- AUTO-LATEST-ARTICLES:END -->

<!-- AUTO-SERIES-ARTICLES:START -->
<!-- AUTO-SERIES-ARTICLES:END -->
```

Modify the generating scripts, or add preview metadata to the source article, instead.

## 7. About AdMOS

**[AdMOS GmbH](https://www.admos.de)**, Advanced Modeling Solutions, works in semiconductor characterization, electrical measurements, compact modeling, simulation, reliability, and related technologies.

This website is part of AdMOS's commitment to sharing practical technical knowledge and making semiconductor-device concepts understandable to researchers and engineers.

**Company website:** https://www.admos.de/

---

© AdMOS GmbH. All rights reserved.

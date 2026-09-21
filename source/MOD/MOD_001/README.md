# AdMOS LaTeX Technical Article Template

## Files

-   `article.tex` - Article metadata and article content only
-   `admos-article.sty` - AdMOS styling, layout, header, footer,
    captions, and reusable commands
-   `admos-letterhead.png` - Header image used by the style package
-   `README.md` - This file

## Compile

``` bash
pdflatex article.tex
pdflatex article.tex
```

Run twice so the total page count in the footer updates.

## Creating a New Article

For a new article, edit `article.tex`. In normal use there should be no
need to edit `admos-article.sty`.

Article-specific information in `article.tex`:

``` latex
\ArticleType
\ArticleSeries
\ArticleID
\ArticleDate
\ArticleTitle
\ArticleSubtitle
```

## Template Styling

Template-wide settings such as page geometry, colors, typography, header
and footer, company name, contact email, section formatting, captions,
tables, and bibliography styling are kept in `admos-article.sty`.

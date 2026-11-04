# Peer-reviewed publications

Each publication has its own folder named `YYYY-MM-DD_title-slug`, containing `metadata.json` and `thumbnail.png`.

## Metadata fields

- `Title`: full publication title
- `PublicationType`: Journal, Conference, Book, or similar
- `PublicationSource`: journal, conference, or book name
- `DOI`: full `https://doi.org/...` URL
- `PublicationDate`: `YYYY-MM-DD` (e.g. `2026-05-06`)
- `ShortAbstract`: short description shown on the card
- `PublicationURL`: optional HTTPS fallback link when `DOI` is empty

The folder slug is the lowercase hyphen-separated title. The date prefix must match `PublicationDate`. The generator sorts by date descending, displaying dates in `DD.MM.YYYY` format.

## Adding a publication

1. Create a dated publication folder under `jpa/`.
2. Add `metadata.json` with the fields above.
3. Add a PNG thumbnail named `thumbnail.png`.
4. Run `python3 jpa/update_publications.py` and commit the results.

The dedicated `Update Peer-Reviewed Publications` GitHub Actions workflow validates and regenerates the JPA cards when changes under `jpa/` reach `main`. It runs independently of the LaTeX article build. The workflow updates only the generated article-card region of `jpa/index.html` and preserves all other page styling. Shared `assets/` contains only `bg.jpg`.

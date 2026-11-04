#!/usr/bin/env python3
"""Safely restore original JPA PNG files from the one-time approved archive."""
import csv
import hashlib
import io
import sys
import zipfile
from pathlib import Path

EXPECTED_ZIP_SHA256 = "427eada61e2534907a250e82f185bb624c75f9105bac5d402a0b36ce377b83bd"
ARCHIVE = Path("jpa/JPA_Original_Images_Restoration.zip")


def git_blob_sha(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def main() -> None:
    if not ARCHIVE.is_file():
        raise RuntimeError(f"Upload {ARCHIVE} to the main branch first.")

    archive_bytes = ARCHIVE.read_bytes()
    actual_sha = hashlib.sha256(archive_bytes).hexdigest()
    if actual_sha != EXPECTED_ZIP_SHA256:
        raise RuntimeError("ZIP checksum mismatch. No images were changed.")

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        rows = list(csv.DictReader(io.StringIO(archive.read("audit.csv").decode("utf-8"))))
        if len(rows) != 18:
            raise RuntimeError(f"Expected 18 original images, found {len(rows)}")

        paths = [row["repo_path"] for row in rows]
        if len(set(paths)) != 18:
            raise RuntimeError("Duplicate paths in the archive audit.")

        expected_pngs = {"images/" + path for path in paths}
        actual_pngs = {name for name in archive.namelist() if name.endswith(".png")}
        if actual_pngs != expected_pngs:
            raise RuntimeError("ZIP image inventory differs from the approved audit.")

        changes = []
        for row in rows:
            rel = Path(row["repo_path"])
            if (len(rel.parts) != 3 or rel.parts[0] != "jpa"
                    or rel.name != "thumbnail.png" or ".." in rel.parts):
                raise RuntimeError(f"Unexpected destination: {rel}")

            original = archive.read("images/" + rel.as_posix())
            if hashlib.sha256(original).hexdigest() != row["original_sha256"]:
                raise RuntimeError(f"Original image checksum mismatch: {rel}")

            if original[:8] != b"\x89PNG\r\n\x1a\n":
                raise RuntimeError(f"Not a PNG file: {rel}")

            width = int.from_bytes(original[16:20], "big")
            height = int.from_bytes(original[20:24], "big")
            if (width, height) != (int(row["original_width"]), int(row["original_height"])):
                raise RuntimeError(f"Image dimensions mismatch: {rel}")

            if not rel.is_file():
                raise RuntimeError(f"Existing JPA thumbnail missing: {rel}")

            existing = rel.read_bytes()
            if existing == original:
                continue
            if git_blob_sha(existing) != row["previous_git_blob_sha"]:
                raise RuntimeError(f"Thumbnail changed since audit. No files changed: {rel}")

            changes.append((rel, original))

    # Do not modify any file until every image passes the checks above.
    for path, original in changes:
        path.write_bytes(original)
        if path.read_bytes() != original:
            raise RuntimeError(f"Byte-for-byte verification failed: {path}")
        print(f"Restored {path} ({len(original)} bytes)")

    print(f"Restored {len(changes)} full-resolution original PNGs without resizing.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyError, ValueError, zipfile.BadZipFile) as exc:
        sys.exit(f"Restoration aborted: {exc}")

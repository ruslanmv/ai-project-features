# src/tools/file_scanner.py
# ────────────────────────────────────────────────────────────────────────────
# Deterministic, stateless utility. Given a ZIP path, returns a Markdown-formatted
# directory tree plus the first line of each file (size-capped). Implements phase Z.

import zipfile
import textwrap


def scan_zip(zip_path: str) -> str:
    """
    Open the ZIP archive at `zip_path`, list all non-directory files in sorted order,
    and for each file output:
      ├── <filename>  (<size> B)
            <first line of content, truncated to 100 chars>

    Returns a single Markdown-formatted string representing the tree with previews.
    """
    lines = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in sorted(zf.namelist()):
            # Skip directory entries (they end with '/')
            if name.endswith("/"):
                continue

            info = zf.getinfo(name)
            size_bytes = info.file_size
            prefix = f"├── {name}"
            lines.append(f"{prefix}  ({size_bytes} B)")

            # Read up to 120 bytes to show as a one-line preview
            with zf.open(name) as fp:
                raw = fp.read(120)
                try:
                    snippet = raw.decode(errors="ignore").splitlines()[:1]
                    if snippet:
                        shortened = textwrap.shorten(snippet[0], width=100)
                        lines.append(f"      {shortened}")
                except Exception:
                    # If decoding fails, skip the preview
                    continue

    return "\n".join(lines)

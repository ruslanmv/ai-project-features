# src/tools/diff_generator.py
# ────────────────────────────────────────────────────────────────────────────
# Pure utility: create_patch(old_text, new_text, filename).
# Used by code_writer_agent so that doc_assembler_agent can show unified diffs.

import difflib
from typing import List


def create_patch(old_text: str, new_text: str, filename: str) -> str:
    """
    Produce a unified diff between `old_text` and `new_text` for a given `filename`.

    Parameters
    ----------
    old_text : str
        The original file content (empty string if the file did not exist).
    new_text : str
        The updated file content to compare against the old.
    filename : str
        The relative path (from project root) to label in the diff headers.

    Returns
    -------
    str
        A unified diff string with lines prefixed by '-', '+', or ' '.
        If there are no differences, the returned string will be empty.
    """
    # Split lines preserving newline characters for accurate diffing
    old_lines: List[str] = old_text.splitlines(keepends=True)
    new_lines: List[str] = new_text.splitlines(keepends=True)

    # Prefixes "a/filename" and "b/filename" mimic Git-style diff headers
    fromfile = f"a/{filename}"
    tofile = f"b/{filename}"

    diff_lines = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=fromfile,
        tofile=tofile,
        lineterm=""
    )

    return "".join(diff_lines)

"""Async file scanner for ZIP archives."""
from __future__ import annotations
import asyncio
import zipfile
from pathlib import Path

async def scan_zip_async(zip_path: str, preview_bytes: int = 120) -> str:
    """Scan a ZIP file and generate a directory tree with previews.
    
    Args:
        zip_path: Path to ZIP archive.
        preview_bytes: Number of bytes to preview per file.
    
    Returns:
        Markdown-formatted directory tree.
    """
    def _scan() -> str:
        tree_lines = [f"# Contents of {Path(zip_path).name}\n"]
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for info in zf.infolist()[:50]:  # Limit to 50 files
                tree_lines.append(f"- {info.filename} ({info.file_size} bytes)")
        return "\n".join(tree_lines)
    
    # Run blocking I/O in executor
    return await asyncio.to_thread(_scan)

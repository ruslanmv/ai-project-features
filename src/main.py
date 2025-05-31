"""
src/main.py
════════════════════════════════════════════════════════════════════════════
Command-line (and importable) entry point for *ai-project-features*.

* Accepts*:  --zip   : Path to the code-base archive to patch/refactor
            --prompt: Natural-language instruction string
            --max-attempts: Optional (default=4) retries for the P5⇆D1 loop
            --quiet : Suppress progress banners; only print the recap

* What it does*:
  1. Boots a `Settings` object from `config.py`
  2. Passes the ZIP + prompt into `workflows.run_all()`
  3. Prints the final Markdown recap (or returns it if called as a library)

Exit code is **0** on success, **1** if static checks never pass or any
unexpected exception bubbles up.

Example
-------
python -m src --zip my_project.zip \
               --prompt "Add OpenTelemetry tracing but keep architecture"
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────
# Local imports
# ────────────────────────────────────────────────────────────────────────────
from config import Settings
from workflows import run_all

# ────────────────────────────────────────────────────────────────────────────
# CLI Argument Parser
# ────────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ai-project-features",
        formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent(
            """
            Multi-agent refactor assistant powered by BeeAI + Watsonx.ai.

            Required:
              --zip <path>      Path to a .zip archive of the target code base
              --prompt "<text>" Natural-language instructions for the LLM

            Optional:
              --max-attempts N  P5⇆D1 retry budget (default 4)
              --quiet           Only print the final recap
            """
        ),
    )
    p.add_argument("--zip", required=True, help="Path to the ZIP archive")
    p.add_argument(
        "--prompt",
        required=True,
        help="Instruction string. Enclose in quotes if it contains spaces.",
    )
    p.add_argument(
        "--max-attempts",
        type=int,
        default=4,
        help="Retries for code-gen + static-check loop (P5⇆D1).",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress phase banners; output only the final recap.",
    )
    return p


# ────────────────────────────────────────────────────────────────────────────
# Progress helpers
# ────────────────────────────────────────────────────────────────────────────
def banner(title: str) -> None:
    """Pretty printer for phase banners (skipped when --quiet)."""
    if not banner.quiet:
        print(f"\n── {title} {'─' * (70 - len(title))}", flush=True)


banner.quiet = False  # dynamic attribute


# ────────────────────────────────────────────────────────────────────────────
# Main driver
# ────────────────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> None:
    """Parse CLI args, run the workflow, and print recap."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Attach banner helper to user preference
    banner.quiet = bool(args.quiet)

    # Sanity-check inputs
    zip_path = Path(args.zip).expanduser().resolve()
    if not zip_path.exists():
        parser.error(f"--zip path not found: {zip_path}")

    settings = Settings()  # validates env vars or raises ValueError
    banner("Settings loaded")

    try:
        recap_md = run_all(str(zip_path), args.prompt)
        print("\n✅  Workflow completed successfully!\n")
        print(recap_md)
        sys.exit(0)

    except RuntimeError as rte:
        # Expected failure, e.g., static checker exhaustion
        print(f"\n❌  {rte}", file=sys.stderr)
        sys.exit(1)

    except Exception as exc:  # noqa: BLE001
        # Unexpected crash – re-raise after friendly message
        print("\n💥  Unhandled exception; see traceback below.\n", file=sys.stderr)
        raise


# ────────────────────────────────────────────────────────────────────────────
# `python -m src` entry-point behaviour
# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()

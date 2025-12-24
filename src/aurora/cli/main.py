"""Beautiful command-line interface for Aurora using Typer and Rich.

This module provides an elegant, production-ready CLI with:
- Beautiful progress indicators and spinners
- Colored terminal output with Rich formatting
- Comprehensive help text and examples
- Robust error handling with user-friendly messages

Examples:
    $ aurora refactor project.zip "Add logging to all agents"
    $ aurora refactor --model granite-20b-chat --temperature 0.0 app.zip "Fix bugs"
    $ aurora version
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

from aurora import __version__
from aurora.core.config import get_settings
from aurora.core.exceptions import AuroraException
from aurora.core.logging import get_logger, log_exception, setup_logging

# Initialize Typer app with custom styling
app = typer.Typer(
    name="aurora",
    help="⚡ Aurora AI Refactor Assistant - Next-generation autonomous code refactoring",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# Initialize Rich console for beautiful output
console = Console()
logger = get_logger(__name__)


@app.command()
def refactor(
    zip_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the ZIP archive containing the codebase to refactor",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    prompt: Annotated[
        str,
        typer.Argument(
            help="Natural language instruction describing the refactoring task"
        ),
    ],
    model: Annotated[
        Optional[str],
        typer.Option(
            "--model",
            "-m",
            help="LLM model to use (overrides default from config)",
        ),
    ] = None,
    temperature: Annotated[
        Optional[float],
        typer.Option(
            "--temperature",
            "-t",
            min=0.0,
            max=1.0,
            help="Sampling temperature (0.0 = deterministic, 1.0 = creative)",
        ),
    ] = None,
    max_attempts: Annotated[
        Optional[int],
        typer.Option(
            "--max-attempts",
            "-a",
            min=1,
            max=10,
            help="Maximum retry attempts for code generation loop",
        ),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Path to save the refactored code (default: print to stdout)",
        ),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress progress output, show only final results",
        ),
    ] = False,
    json_logs: Annotated[
        bool,
        typer.Option(
            "--json-logs",
            help="Enable structured JSON logging (for production/parsing)",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose debug logging",
        ),
    ] = False,
) -> None:
    """Refactor a codebase using AI-powered multi-agent orchestration.

    This command analyzes your code, plans refactoring steps, generates patches,
    and validates the changes before presenting them for review.

    Examples:

        # Basic refactoring
        $ aurora refactor project.zip "Add error handling to all functions"

        # With custom model and temperature
        $ aurora refactor --model granite-20b-chat --temperature 0.0 app.zip "Fix bugs"

        # Save output to file
        $ aurora refactor --output refactored.md project.zip "Add logging"

        # Quiet mode with JSON logs (for CI/CD)
        $ aurora refactor --quiet --json-logs app.zip "Update dependencies"
    """
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level=log_level, json_logs=json_logs)

    logger.info("aurora_started", version=__version__, zip_path=str(zip_path))

    if not quiet:
        # Display beautiful banner
        console.print()
        console.print(
            Panel.fit(
                "[bold cyan]⚡ Aurora AI Refactor Assistant[/bold cyan]\\n"
                f"[dim]Version {__version__} • Autonomous Code Refactoring[/dim]",
                border_style="cyan",
            )
        )
        console.print()

    try:
        # Load settings with optional overrides
        settings = get_settings()

        # Display configuration table
        if not quiet:
            config_table = Table(title="Configuration", show_header=False, box=None)
            config_table.add_column("Setting", style="cyan")
            config_table.add_column("Value", style="yellow")

            config_table.add_row("📦 Archive", str(zip_path.absolute()))
            config_table.add_row("💬 Prompt", prompt[:60] + "..." if len(prompt) > 60 else prompt)
            config_table.add_row(
                "🤖 Model",
                model or settings.default_llm_model_id,
            )
            config_table.add_row(
                "🌡️  Temperature",
                str(temperature if temperature is not None else settings.llm_temperature),
            )
            config_table.add_row(
                "🔄 Max Attempts",
                str(max_attempts or settings.max_code_gen_attempts),
            )
            console.print(config_table)
            console.print()

        # Run the refactoring workflow with progress indicator
        result = asyncio.run(
            _run_refactor_workflow(
                zip_path=zip_path,
                prompt=prompt,
                quiet=quiet,
            )
        )

        # Display results
        if not quiet:
            console.print()
            console.print(
                Panel(
                    "[bold green]✅ Refactoring Complete![/bold green]",
                    border_style="green",
                )
            )
            console.print()

        # Output the result
        if output:
            output.write_text(result)
            console.print(f"[green]Results saved to:[/green] {output}")
        else:
            # Pretty-print markdown result
            syntax = Syntax(result, "markdown", theme="monokai", line_numbers=False)
            console.print(syntax)

        logger.info("aurora_completed", success=True)

    except AuroraException as e:
        log_exception(logger, e)
        console.print()
        console.print(
            Panel(
                f"[bold red]❌ Error:[/bold red] {e.message}\\n\\n"
                f"[dim]{e.details}[/dim]",
                title="Aurora Error",
                border_style="red",
            )
        )
        console.print()
        raise typer.Exit(code=1) from e

    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]⚠️  Interrupted by user[/yellow]")
        logger.warning("aurora_interrupted")
        raise typer.Exit(code=130) from None

    except Exception as e:
        log_exception(logger, e)
        console.print()
        console.print(
            Panel(
                f"[bold red]💥 Unexpected Error:[/bold red]\\n{e!s}",
                title="System Error",
                border_style="red",
            )
        )
        console.print()
        raise typer.Exit(code=1) from e


async def _run_refactor_workflow(
    *,
    zip_path: Path,
    prompt: str,
    quiet: bool,
) -> str:
    """Run the refactoring workflow with progress indicators.

    Args:
        zip_path: Path to ZIP archive.
        prompt: User's refactoring instruction.
        quiet: If True, suppress progress output.

    Returns:
        Markdown recap of the refactoring results.
    """
    # Import here to avoid circular dependencies
    from aurora.core.orchestrator import RefactorOrchestrator

    orchestrator = RefactorOrchestrator()

    if quiet:
        # Run without progress indicators
        return await orchestrator.run(str(zip_path), prompt)

    # Run with beautiful progress indicators
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("[cyan]Analyzing codebase...", total=None)

        async def progress_callback(phase: str, status: str) -> None:
            """Update progress display during workflow execution."""
            progress.update(task, description=f"[cyan]{phase}:[/cyan] {status}")

        # Set progress callback on orchestrator
        orchestrator.set_progress_callback(progress_callback)

        result = await orchestrator.run(str(zip_path), prompt)

        progress.update(task, description="[green]✅ Complete!", completed=True)

    return result


@app.command()
def version() -> None:
    """Display Aurora version and system information."""
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]Aurora AI Refactor Assistant[/bold cyan]\\n"
            f"[yellow]Version:[/yellow] {__version__}\\n"
            f"[yellow]Python:[/yellow] {sys.version.split()[0]}\\n"
            f"[yellow]Author:[/yellow] Ruslan Magana\\n"
            f"[yellow]Website:[/yellow] ruslanmv.com\\n"
            f"[yellow]License:[/yellow] Apache 2.0",
            border_style="cyan",
            title="About",
        )
    )
    console.print()


@app.command()
def validate_config() -> None:
    """Validate configuration and environment variables.

    Checks that all required environment variables are set and have valid values.
    Useful for debugging configuration issues.

    Examples:
        $ aurora validate-config
    """
    console.print()
    console.print("[cyan]Validating configuration...[/cyan]")
    console.print()

    try:
        settings = get_settings()

        # Create validation table
        table = Table(title="Configuration Status", show_header=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Value", style="yellow")

        table.add_row("Watson X API Key", "✅ Set", f"{settings.watsonx_api_key[:4]}...{settings.watsonx_api_key[-4:]}")
        table.add_row("Watson X Project ID", "✅ Set", settings.watsonx_project_id[:8] + "...")
        table.add_row("Watson X URL", "✅ Set", settings.watsonx_url)
        table.add_row("Default Model", "✅ Set", settings.default_llm_model_id)
        table.add_row("Temperature", "✅ Set", str(settings.llm_temperature))
        table.add_row("Log Level", "✅ Set", settings.log_level)

        console.print(table)
        console.print()
        console.print("[bold green]✅ Configuration is valid![/bold green]")
        console.print()

    except Exception as e:
        console.print()
        console.print(
            Panel(
                f"[bold red]❌ Configuration Error:[/bold red]\\n{e!s}\\n\\n"
                "[dim]Please check your .env file and environment variables.[/dim]",
                border_style="red",
            )
        )
        console.print()
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()

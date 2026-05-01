"""Si nano Factory CLI — entry point `factory`.

Implemented commands (Phase 1):
    factory --help
    factory version
    factory init
    factory spec validate <PATH>
    factory spec hash <PATH>

Stubs (raise NotImplementedError until the relevant module lands):
    factory build
    factory screen
    factory run
    factory recipe
    factory queue
    factory replay
    factory dashboard
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from sinanofactory.config import get_settings
from sinanofactory.core import NanoparticleSpec
from sinanofactory.version import __version__

app = typer.Typer(
    name="factory",
    help="Si nano Factory — Two-Dimensional World. AI-driven nanoparticle design platform.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=False,
)

spec_app = typer.Typer(name="spec", help="Operations on NanoparticleSpec JSON files.")
app.add_typer(spec_app)

_console = Console()


# ============================================================================
# version
# ============================================================================
@app.command()
def version() -> None:
    """Print package version."""
    rprint(f"si-nano-factory [bold cyan]{__version__}[/bold cyan]")


# ============================================================================
# init
# ============================================================================
@app.command()
def init(
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace directory (default: from .env / ~/sinanofactory).",
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing skeleton."),
) -> None:
    """Initialise a workspace directory with the standard layout.

    Creates:
        <workspace>/data/{raw,processed,trajectories}/
        <workspace>/models/
        <workspace>/recipes/
        <workspace>/specs/
    """
    settings = get_settings()
    target = workspace or settings.workspace_dir
    target = target.expanduser().resolve()

    subdirs = [
        target / "data" / "raw",
        target / "data" / "processed",
        target / "data" / "trajectories",
        target / "models",
        target / "recipes",
        target / "specs",
    ]

    rprint(f"[bold]Initialising workspace at[/bold] [cyan]{target}[/cyan]")
    for sub in subdirs:
        if sub.exists() and not force:
            rprint(f"  [yellow]⊙ exists[/yellow] {sub.relative_to(target)}/")
        else:
            sub.mkdir(parents=True, exist_ok=True)
            rprint(f"  [green]✓ created[/green] {sub.relative_to(target)}/")
    rprint("[bold green]Done.[/bold green]")


# ============================================================================
# spec subcommands
# ============================================================================
@spec_app.command("validate")
def spec_validate(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
) -> None:
    """Validate a NanoparticleSpec JSON file against the schema."""
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        spec = NanoparticleSpec.model_validate(data)
    except (json.JSONDecodeError, ValueError) as exc:
        rprint(f"[bold red]✗ INVALID[/bold red] {path}")
        rprint(f"  [red]{exc}[/red]")
        raise typer.Exit(code=2) from exc

    table = Table(title=f"Spec: {path.name}", show_header=False, box=None)
    table.add_row("name", spec.name or "(unnamed)")
    table.add_row("hash", spec.canonical_hash())
    table.add_row("short_id", spec.short_id)
    table.add_row(
        "core",
        f"{type(spec.core).__name__} ({spec.core.material.value}, {spec.core.diameter_nm} nm)",
    )
    table.add_row(
        "surface",
        f"{len(spec.surface.ligands)} ligands; "
        f"density={spec.surface.grafting_density} /nm²; "
        f"coverage={spec.surface.coverage_fraction:.2f}",
    )
    table.add_row(
        "environment",
        f"solvent={spec.environment.solvent.name}; "
        f"T={spec.environment.temperature_K} K; "
        f"sorbates={len(spec.environment.sorbates)}",
    )
    table.add_row("worst provenance", spec.surface.worst_provenance().value)
    rprint(table)
    rprint(f"[bold green]✓ VALID[/bold green] {path}")


@spec_app.command("hash")
def spec_hash(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    full: bool = typer.Option(False, "--full", help="Print full SHA-256 instead of short_id."),
) -> None:
    """Print the canonical hash of a NanoparticleSpec JSON file.

    Two specs with the same hash describe the same physical system.
    """
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    spec = NanoparticleSpec.model_validate(data)
    rprint(spec.canonical_hash() if full else spec.short_id)


# ============================================================================
# Stubs — implemented in later phases
# ============================================================================
@app.command()
def build(_spec: Path = typer.Argument(...)) -> None:
    """Build atomistic topology from a NanoparticleSpec (Phase 1)."""
    _not_yet("build")


@app.command()
def screen() -> None:
    """Run a screening flow over a ligand pool (Phase 2)."""
    _not_yet("screen")


@app.command()
def run() -> None:
    """Run a Deep-Study flow for a single spec (Phase 1)."""
    _not_yet("run")


@app.command()
def recipe() -> None:
    """Render a SynthesisRecipe PDF for a completed run (Phase 1.5)."""
    _not_yet("recipe")


@app.command()
def queue() -> None:
    """List queued / running / completed jobs (Phase 3)."""
    _not_yet("queue")


@app.command()
def replay() -> None:
    """Reproduce a previous run from MLflow snapshot (Phase 3)."""
    _not_yet("replay")


@app.command()
def dashboard() -> None:
    """Launch the Streamlit PI dashboard (Phase 1.5)."""
    _not_yet("dashboard")


def _not_yet(command: str) -> None:
    """Helper for stub commands — keeps the CLI surface honest."""
    rprint(
        f"[bold yellow]⚠[/bold yellow] [bold]{command}[/bold] is not yet implemented "
        "(see [cyan]docs/00_TZ.md §10 Roadmap[/cyan])."
    )
    raise typer.Exit(code=64)  # EX_USAGE


if __name__ == "__main__":
    app()

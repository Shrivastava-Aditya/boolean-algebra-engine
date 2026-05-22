"""
cli/main.py — boolcalc command-line interface.

Usage:
    boolcalc [OPTIONS] EXPRESSION

Examples:
    boolcalc "A+B"
    boolcalc "A.(B+C)" --format json
    boolcalc "A.!A" --satisfiable
    boolcalc "A+B.C" --synthesize --metrics
    echo "A^B" | boolcalc --format minimal
"""
from __future__ import annotations
import json
import sys
from enum import Enum
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from core.evaluator import evaluate
from core.synthesizer import synthesize

app = typer.Typer(
    name="boolcalc",
    help="Boolean algebra engine — evaluate expressions and synthesize minimal forms.",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)


class Format(str, Enum):
    table   = "table"
    json    = "json"
    csv     = "csv"
    minimal = "minimal"


def _read_stdin() -> str | None:
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return None


@app.command()
def main(
    expression: Optional[str] = typer.Argument(
        None,
        help="Boolean expression. Variables: A–Z. Operators: ! . ^ +"
    ),
    format: Format = typer.Option(
        Format.table,
        "--format", "-f",
        help="Output format.",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Write output to file instead of stdout.",
    ),
    synthesize_flag: bool = typer.Option(
        False,
        "--synthesize", "-s",
        help="Print the minimal equivalent expression.",
    ),
    satisfiable: bool = typer.Option(
        False,
        "--satisfiable",
        help="Exit 0 if satisfiable, 1 if not. No truth table printed.",
    ),
    tautology: bool = typer.Option(
        False,
        "--tautology",
        help="Exit 0 if tautology, 1 if not. No truth table printed.",
    ),
    minterms: bool = typer.Option(
        False,
        "--minterms",
        help="Print minterm indices (rows where output = 1).",
    ),
    maxterms: bool = typer.Option(
        False,
        "--maxterms",
        help="Print maxterm indices (rows where output = 0).",
    ),
    metrics: bool = typer.Option(
        False,
        "--metrics",
        help="Print performance metrics (time and memory).",
    ),
):
    # Accept expression from stdin if not passed as argument
    expr = expression or _read_stdin()
    if not expr:
        err_console.print("[red]Error:[/red] No expression provided. Pass as argument or via stdin.")
        raise typer.Exit(1)

    # Evaluate
    try:
        table, eval_metrics = evaluate(expr)
    except ValueError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    # --- Query flags (no truth table output) ---
    if satisfiable:
        raise typer.Exit(0 if table.satisfiable else 1)

    if tautology:
        raise typer.Exit(0 if table.tautology else 1)

    # --- Synthesize ---
    synth_expr = None
    synth_metrics = None
    if synthesize_flag:
        synth_expr, synth_metrics = synthesize(table)

    # --- Build output ---
    out = _build_output(table, eval_metrics, synth_expr, synth_metrics,
                        format, minterms, maxterms, metrics)

    # --- Write or print ---
    if output:
        with open(output, 'w') as f:
            f.write(out if isinstance(out, str) else '\n'.join(out))
        console.print(f"[green]Written to {output}[/green]")
    else:
        if format == Format.table:
            _print_rich_table(table, eval_metrics, synth_expr, synth_metrics,
                              minterms, maxterms, metrics)
        else:
            print(out)


def _build_output(table, eval_metrics, synth_expr, synth_metrics,
                  format, show_minterms, show_maxterms, show_metrics) -> str:
    if format == Format.json:
        data = {
            "expression": table.expression,
            "variables": table.variables,
            "rows": [
                {**row.inputs, "output": row.output}
                for row in table.rows
            ],
            "satisfiable": table.satisfiable,
            "tautology": table.tautology,
            "minterms": table.minterms,
            "maxterms": table.maxterms,
        }
        if synth_expr is not None:
            data["minimal_expression"] = synth_expr
        if show_metrics:
            data["metrics"] = {
                "eval_time_ms": eval_metrics.eval_time_ms,
                "peak_memory_bytes": eval_metrics.peak_memory_bytes,
                "rows_evaluated": eval_metrics.rows_evaluated,
            }
            if synth_metrics:
                data["metrics"]["synth_time_ms"] = synth_metrics.synth_time_ms
                data["metrics"]["synth_peak_memory_bytes"] = synth_metrics.peak_memory_bytes
                data["metrics"]["prime_implicant_count"] = synth_metrics.prime_implicant_count
        return json.dumps(data, indent=2)

    if format == Format.csv:
        lines = [",".join(table.variables + ["output"])]
        for row in table.rows:
            lines.append(",".join(str(row.inputs[v]) for v in table.variables) + f",{row.output}")
        return "\n".join(lines)

    if format == Format.minimal:
        return "\n".join(str(row.output) for row in table.rows)

    return ""


def _print_rich_table(table, eval_metrics, synth_expr, synth_metrics,
                      show_minterms, show_maxterms, show_metrics):
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan")

    for var in table.variables:
        t.add_column(var, justify="center", style="dim")
    t.add_column(table.expression, justify="center", style="bold")

    for row in table.rows:
        values = [str(row.inputs[v]) for v in table.variables]
        output = "[green]1[/green]" if row.output == 1 else "[red]0[/red]"
        t.add_row(*values, output)

    console.print(t)
    console.print(f"  Variables  : [cyan]{', '.join(table.variables)}[/cyan]")
    console.print(f"  Rows       : {eval_metrics.rows_evaluated}")
    console.print(f"  Satisfiable: {'[green]Yes[/green]' if table.satisfiable else '[red]No[/red]'}")
    console.print(f"  Tautology  : {'[green]Yes[/green]' if table.tautology else '[red]No[/red]'}")

    if show_minterms:
        console.print(f"  Minterms   : {table.minterms}")
    if show_maxterms:
        console.print(f"  Maxterms   : {table.maxterms}")
    if synth_expr is not None:
        console.print(f"  Minimal    : [bold yellow]{synth_expr}[/bold yellow]")
    if show_metrics:
        console.print(f"\n  [dim]Eval  : {eval_metrics.eval_time_ms} ms  |  {eval_metrics.peak_memory_bytes} bytes[/dim]")
        if synth_metrics:
            console.print(f"  [dim]Synth : {synth_metrics.synth_time_ms} ms  |  {synth_metrics.peak_memory_bytes} bytes  |  {synth_metrics.prime_implicant_count} prime implicants[/dim]")


if __name__ == "__main__":
    app()

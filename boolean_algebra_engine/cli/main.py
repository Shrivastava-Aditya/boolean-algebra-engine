"""
cli/main.py — boolcalc command-line interface.

Usage:
    boolcalc [OPTIONS] EXPRESSION   one-shot mode
    boolcalc                        interactive REPL mode

Examples:
    boolcalc "A+B"
    boolcalc "A.(B+C)" --format json
    boolcalc "A.!A" --satisfiable
    boolcalc "A+B.C" --synthesize --metrics
    echo "A^B" | boolcalc --format minimal
"""
from __future__ import annotations
import json
import shlex
import sys
from enum import Enum
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from boolean_algebra_engine.core.evaluator import evaluate
from boolean_algebra_engine.core.synthesizer import synthesize
from boolean_algebra_engine.cli import telemetry

_VERSION = "0.3.9"


def _version_callback(value: bool):
    if value:
        typer.echo(f"boolcalc {_VERSION}")
        raise typer.Exit()


app = typer.Typer(
    name="boolcalc",
    help="Boolean algebra engine — evaluate expressions and synthesize minimal forms.",
    add_completion=False,
)


@app.callback()
def _root(
    version: Optional[bool] = typer.Option(None, "--version", "-V", callback=_version_callback, is_eager=True, help="Show version and exit."),
):
    pass
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


@app.command("evaluate")
def cmd_evaluate(
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
    interactive: bool = typer.Option(
        False,
        "--interactive", "-i",
        help="Launch interactive REPL mode.",
    ),
):
    """Evaluate a boolean expression and print its truth table."""
    # Launch REPL if requested
    if interactive:
        _repl()
        return

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
        telemetry.send("evaluate", success=False, error=type(e).__name__)
        raise typer.Exit(1)

    telemetry.send("evaluate", success=True, variable_count=len(table.variables))

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

    telemetry.maybe_nudge()


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


REPL_BANNER = """
[bold cyan]╔══════════════════════════════════════════════════════╗
║          Boolean Algebra Engine  —  boolcalc         ║
╚══════════════════════════════════════════════════════╝[/bold cyan]

[white]A boolean algebra engine that evaluates expressions against
truth tables and synthesizes minimal forms using Quine-McCluskey.[/white]

[bold]What it does:[/bold]
  [green]Forward[/green]   expression  →  truth table
  [green]Inverse[/green]   truth table →  minimal expression

[bold]Operators:[/bold]
  [yellow]![/yellow]   NOT   (highest precedence)
  [yellow].[/yellow]   AND
  [yellow]^[/yellow]   XOR
  [yellow]+[/yellow]   OR    (lowest precedence)

  Variables must be uppercase letters [cyan]A–Z[/cyan].
  Parentheses override precedence as usual.
"""

REPL_HELP = """
[bold cyan]── Commands ──────────────────────────────────────────────[/bold cyan]

  [yellow]<expression>[/yellow]                   evaluate and show truth table
  [yellow]<expression> -s[/yellow]                also show minimal expression
  [yellow]<expression> --metrics[/yellow]         show timing and memory usage
  [yellow]<expression> --minterms[/yellow]        show minterm indices
  [yellow]<expression> --maxterms[/yellow]        show maxterm indices
  [yellow]<expression> --satisfiable[/yellow]     check if satisfiable
  [yellow]<expression> --tautology[/yellow]       check if tautology

[bold cyan]── Output formats ────────────────────────────────────────[/bold cyan]

  [yellow]<expression> --format table[/yellow]    rich table (default)
  [yellow]<expression> --format json[/yellow]     JSON — good for scripting
  [yellow]<expression> --format csv[/yellow]      CSV
  [yellow]<expression> --format minimal[/yellow]  output column only

[bold cyan]── Examples ──────────────────────────────────────────────[/bold cyan]

  [dim]boolcalc>[/dim] [green]A+B[/green]
  [dim]boolcalc>[/dim] [green]A.(B+C) -s --metrics[/green]
  [dim]boolcalc>[/dim] [green]!(A.B) --format json[/green]
  [dim]boolcalc>[/dim] [green]A.B+!A.C+B.C -s[/green]       [dim]← consensus theorem[/dim]
  [dim]boolcalc>[/dim] [green]A.!A --satisfiable[/green]     [dim]← contradiction check[/dim]

[bold cyan]── Session ───────────────────────────────────────────────[/bold cyan]

  [yellow]help[/yellow]                           show this manual
  [yellow]exit[/yellow] / [yellow]quit[/yellow] / [yellow]Ctrl+C[/yellow]           exit
"""

def _repl():
    console.print(REPL_BANNER)
    console.print(REPL_HELP)
    while True:
        try:
            line = console.input("[bold cyan]boolcalc>[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]bye[/dim]")
            break

        if not line:
            continue
        if line.lower() in ("exit", "quit", "q"):
            console.print("[dim]bye[/dim]")
            break
        if line.lower() in ("help", "?", "h"):
            console.print(REPL_HELP)
            continue

        # Parse the line as if it were CLI args
        try:
            parts = shlex.split(line)
            # First token is the expression, rest are flags
            app(parts, standalone_mode=False)
        except SystemExit:
            pass
        except Exception as e:
            err_console.print(f"[red]Error:[/red] {e}")

        console.print()


def _make_provider(provider_name: str, api_key: Optional[str], model: Optional[str], base_url: Optional[str]):
    from boolean_algebra_engine.nl.nl import AnthropicProvider, OpenAIProvider, OllamaProvider, OpenAICompatProvider
    if provider_name == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model or "claude-sonnet-4-6")
    if provider_name == "openai":
        return OpenAIProvider(api_key=api_key, model=model or "gpt-4o")
    if provider_name == "ollama":
        return OllamaProvider(model=model or "deepseek-r1:7b", base_url=base_url or "http://localhost:11434")
    if provider_name == "compat":
        if not base_url or not model:
            err_console.print("[red]Error:[/red] --base-url and --model required for compat provider")
            raise typer.Exit(1)
        return OpenAICompatProvider(api_key=api_key or "", base_url=base_url, model=model)
    err_console.print(f"[red]Error:[/red] Unknown provider '{provider_name}'. Choose: anthropic, openai, ollama, compat")
    raise typer.Exit(1)


@app.command("ask")
def nl_ask(
    sentence: str = typer.Argument(..., help="Plain English logical statement."),
    provider: str = typer.Option("ollama", "--provider", "-p", help="LLM provider: ollama (default), anthropic, openai, compat"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for the provider."),
    model: Optional[str] = typer.Option(None, "--model", help="Model ID override."),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Base URL for compat provider."),
    format: Format = typer.Option(Format.table, "--format", "-f"),
):
    """Convert a plain English rule into a verified boolean result."""
    try:
        from boolean_algebra_engine.nl.nl import ask
        prov = _make_provider(provider, api_key, model, base_url)
        result = ask(sentence, provider=prov)
    except ImportError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        telemetry.send("ask", success=False, error=type(e).__name__, provider=provider)
        raise typer.Exit(1)
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        telemetry.send("ask", success=False, error=type(e).__name__, provider=provider)
        raise typer.Exit(1)

    telemetry.send("ask", success=True, provider=provider, variable_count=len(result.variables))

    if format == Format.json:
        print(json.dumps({
            "input": result.input_sentence,
            "expression": result.expression,
            "variables": result.variables,
            "minimal": result.minimal,
            "satisfiable": result.satisfiable,
            "tautology": result.tautology,
            "contradiction": result.contradiction,
            "minterms": result.minterms,
            "explanation": result.explanation,
        }, indent=2))
        return

    console.print(f"\n  [dim]Input    :[/dim] {result.input_sentence}")
    console.print(f"  [dim]Parsed as:[/dim] [cyan]{result.expression}[/cyan]")
    console.print(f"\n  [bold]Variables:[/bold]")
    for var, meaning in result.variables.items():
        console.print(f"    [yellow]{var}[/yellow] = {meaning}")

    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan")
    for var in sorted(result.variables.keys()):
        t.add_column(var, justify="center", style="dim")
    t.add_column(result.expression, justify="center", style="bold")
    for row in result.rows:
        values = [str(row[v]) for v in sorted(result.variables.keys())]
        output = "[green]1[/green]" if row["output"] == 1 else "[red]0[/red]"
        t.add_row(*values, output)
    console.print(t)

    console.print(f"  Minimal    : [bold yellow]{result.minimal}[/bold yellow]")
    console.print(f"  Satisfiable: {'[green]Yes[/green]' if result.satisfiable else '[red]No[/red]'}")
    console.print(f"  Tautology  : {'[green]Yes[/green]' if result.tautology else '[red]No[/red]'}")
    console.print(f"\n  [bold]Explanation:[/bold]\n  {result.explanation}\n")
    telemetry.maybe_nudge()


@app.command("check-rules")
def nl_check_rules(
    rules: list[str] = typer.Argument(..., help="Plain English rules to check."),
    provider: str = typer.Option("ollama", "--provider", "-p", help="LLM provider: ollama (default), anthropic, openai, compat"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for the provider."),
    model: Optional[str] = typer.Option(None, "--model", help="Model ID override."),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Base URL for compat provider."),
):
    """Check a list of plain English rules for contradictions and conflicts."""
    try:
        from boolean_algebra_engine.nl.nl import check_rules
        prov = _make_provider(provider, api_key, model, base_url)
        result = check_rules(rules, provider=prov)
    except ImportError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        telemetry.send("check-rules", success=False, error=type(e).__name__, provider=provider)
        raise typer.Exit(1)
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        telemetry.send("check-rules", success=False, error=type(e).__name__, provider=provider)
        raise typer.Exit(1)

    telemetry.send("check-rules", success=True, provider=provider, rule_count=len(rules))

    print(json.dumps(result, indent=2))
    telemetry.maybe_nudge()


_SUBCOMMANDS = {"ask", "check-rules", "evaluate"}


def _entrypoint():
    telemetry.maybe_prompt()
    args = sys.argv[1:]
    if not args:
        _repl()
        return
    first = args[0]
    if first in _SUBCOMMANDS or first.startswith("-"):
        app()
    else:
        sys.argv.insert(1, "evaluate")
        app()


if __name__ == "__main__":
    _entrypoint()

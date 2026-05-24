#!/usr/bin/env python3
"""
curve.py — Run one model across variable counts to find its breaking point.

Usage:
  python3 curve.py --provider groq --model llama-3.1-8b-instant --cases 100
  python3 curve.py --provider ollama --model gemma3:4b --cases 20

Results saved to results/curve/{model}/{n}vars_{timestamp}.json
"""

import os
import sys
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.table import Table
from rich import box

from benchmark import generate_cases, verify_with_z3, run_benchmark, build_providers

console = Console()

VAR_COUNTS = [3, 5, 7, 10]


def save_curve_result(summary: dict, n_vars: int):
    model = summary["model"]
    safe_model = model.replace("/", "_").replace(":", "-")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("results", "curve", safe_model)
    os.makedirs(path, exist_ok=True)
    filename = os.path.join(path, f"{n_vars}vars_{ts}.json")
    summary["n_vars"] = n_vars
    with open(filename, "w") as f:
        json.dump(summary, f, indent=2)
    return filename


def print_curve_summary(model_name: str, curve: list):
    table = Table(
        title=f"[bold white]Variable curve — {model_name}[/bold white]",
        box=box.SIMPLE_HEAVY, border_style="blue", expand=False,
    )
    table.add_column("vars (n)", style="cyan", justify="center")
    table.add_column("truth table rows", style="dim", justify="right")
    table.add_column("hallucination rate", justify="center")
    table.add_column("missed conflicts", justify="center")
    table.add_column("missed compatibles", justify="center")

    for entry in curve:
        n = entry["n_vars"]
        rate = entry["hallucination_rate"]
        colour = "red" if rate > 60 else "yellow" if rate > 30 else "green"
        mc = entry.get("missed_conflicts", 0)
        mp = entry.get("missed_compat", 0)
        half = entry["total"] // 2
        table.add_row(
            str(n),
            str(2 ** n),
            f"[{colour}]{rate:.1f}%[/{colour}]",
            f"{mc}/{half}",
            f"{mp}/{half}",
        )

    console.print(table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Variable curve benchmark")
    parser.add_argument("--provider", choices=["ollama", "groq", "openai", "anthropic"],
                        default="groq")
    parser.add_argument("--model", default="llama-3.1-8b-instant")
    parser.add_argument("--cases", type=int, default=100,
                        help="Cases per variable count (split 50/50)")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--vars", nargs="+", type=int, default=VAR_COUNTS,
                        help="Variable counts to test (default: 3 5 7 10)")
    parser.add_argument("--no-think", action="store_true",
                        help="Prepend /no_think to prompt (for qwen3 and other thinking models)")
    parser.add_argument("--web", action="store_true",
                        help="Stream results to live dashboard at localhost:8080")
    args = parser.parse_args()

    args.all = False
    providers = build_providers(args)
    if not providers:
        print("No providers configured. Check API keys or --provider flag.")
        sys.exit(1)
    provider = providers[0]

    dashboard = None
    if args.web:
        from dashboard import Dashboard
        dashboard = Dashboard(port=8080)
        dashboard.start()
        console.print("[bold blue]Dashboard:[/bold blue] http://localhost:8080")

    n_each = max(1, args.cases // 2)
    curve = []

    for n_vars in sorted(args.vars):
        console.print(f"\n[bold blue]── n={n_vars} vars  ({2**n_vars} truth table rows) ──[/bold blue]")
        cases = generate_cases(n_each=n_each, seed=args.seed, n_vars=n_vars)
        if not verify_with_z3(cases):
            console.print(f"[red]z3 verification failed at n={n_vars} — skipping.[/red]")
            continue
        summary = run_benchmark(provider, cases, workers=args.workers, dashboard=dashboard,
                               no_think=args.no_think)
        if summary:
            summary["n_vars"] = n_vars
            path = save_curve_result(summary, n_vars)
            console.print(f"[dim]Saved: {path}[/dim]")
            curve.append(summary)

    if curve:
        console.print()
        print_curve_summary(provider.name, curve)
        console.print("\n[dim]Run curve_plot.py to generate the chart.[/dim]")

    if dashboard:
        import threading
        console.print("\n[dim]Dashboard still running at http://localhost:8080 — Ctrl+C to exit.[/dim]")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass

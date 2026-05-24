#!/usr/bin/env python3
"""
benchmark.py — Measure LLM logical hallucination rate against engine ground truth.

The engine is the oracle — exhaustive enumeration, provably correct.
Every LLM disagreement is a measurable, unambiguous hallucination.

Supported providers:
  Ollama   — local, free, no key needed   (tinyllama, llama3.2:3b, mistral)
  Groq     — free tier, fast              (llama-3.1-8b-instant, llama-3.3-70b-versatile)
  OpenAI   — gpt-4o-mini, gpt-4o
  Anthropic — claude-haiku-4-5, claude-sonnet-4-6

Usage:
  # single model
  python3 benchmark.py --provider ollama --model llama3.2:3b --cases 100

  # multi-model run (comma-separated, same provider)
  python3 benchmark.py --provider groq --model "llama-3.1-8b-instant,llama-3.3-70b-versatile" --cases 100

  # all configured providers at once
  python3 benchmark.py --all --cases 100

Results saved to results/{provider}/{model}/{timestamp}.json
"""

import sys
import os
import re
import json
import random
import argparse
import threading
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from abc import ABC, abstractmethod

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn  # kept for future use
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.evaluator import evaluate

# ---------------------------------------------------------------------------
# Expression pool — used to generate test cases
# ---------------------------------------------------------------------------

EXPRESSIONS = [
    "A", "B", "C", "D", "!A", "!B", "!C",
    "A.B", "A+B", "A.!B", "!A.B", "!A.!B",
    "A.B.C", "A+B+C", "A.B+C", "A.(B+C)",
    "!A+B", "A+!B", "!A.!B+A.B",
    "A.B+A.!B",
    "A+!A.B",
    "(A+B).(A+C)",
    "!A+!B", "A.B+!A.!B",
    "A^B", "!(A.B)",
    "A.B+C.D", "A+B.C.D", "!A.!B.!C",
    "(A+B).(C+D)", "A.!B+!A.B",
    "A.B.!C", "!A+B.C",
]

EXPRESSIONS_5VAR = [
    "A", "B", "C", "D", "E",
    "!A", "!B", "!C", "!D", "!E",
    "A.E", "B.E", "C.E", "D.E",
    "A+E", "B+E", "C+E", "D+E",
    "A.!E", "!A.E", "B.!E", "!B.E",
    "A.B.E", "C.D.E", "A+B+E",
    "A.B+C.E", "A.(B+E)", "C.(D+E)",
    "!A.!E", "!D.!E",
    "A^E", "!(A.E)",
    "A.B.C.D.E", "!A.!B.!C.!D.!E",
    "(A+B).(D+E)", "A.B+D.E",
    "!A+B.E", "A+!B.!E",
]

EXPRESSIONS_7VAR = [
    "A", "B", "C", "D", "E", "F", "G",
    "!F", "!G", "A.F", "B.G", "C.F",
    "A+F", "B+G", "!F.!G",
    "A.B.F", "C.D.G", "E.F.G",
    "A.!F", "!A.F", "B.!G", "!B.G",
    "A.B+F.G", "C.(D+F)", "E.(F+G)",
    "!A.!F.!G", "(A+F).(B+G)",
    "A^F", "F.G", "!(F.G)",
    "A.B.C.F", "D.E.F.G",
    "!D.!E.!F.!G", "A+B+F+G",
]

EXPRESSIONS_10VAR = [
    "A", "B", "C", "D", "E",
    "!H", "!I", "!J", "H.I", "H.J",
    "A.H", "B.I", "C.J", "D.H", "E.I",
    "A+H", "B+I", "C+J",
    "A.!H", "!A.H", "B.!I", "!B.I",
    "A.B.H", "C.D.I", "E.F.J",
    "H.I.J", "!H.!I.!J",
    "A.B+H.I", "(A+H).(B+I)",
    "A.H+B.I+C.J", "!(H.I.J)",
    "A^H", "H+I+J",
    "A.B.C.H.I", "D.E.F.G.J",
]

_VAR_POOL = {
    3: EXPRESSIONS, 4: EXPRESSIONS,
    5: EXPRESSIONS_5VAR,
    7: EXPRESSIONS_7VAR,
    10: EXPRESSIONS_10VAR,
}

PROMPT_TEMPLATE = """\
Boolean logic question. Operators: . = AND,  + = OR,  ! = NOT,  ^ = XOR

Rule 1: {e1}
Rule 2: {e2}

Can both rules be satisfied simultaneously — is there any input where both are true?
Answer with only the single word 'yes' or 'no'. No explanation."""

PROMPT_TEMPLATE_NO_THINK = "/no_think\n" + PROMPT_TEMPLATE


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------

class Provider(ABC):
    name: str

    @abstractmethod
    def ask(self, prompt: str) -> bool:
        """Return True if LLM says 'yes', False if 'no'."""

    def __str__(self):
        return self.name


class OllamaProvider(Provider):
    def __init__(self, model: str, url: str = "http://localhost:11434/api/generate"):
        self.model = model
        self.url = url
        self.name = f"ollama/{model}"

    def ask(self, prompt: str) -> bool:
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 5},
        }).encode()
        req = urllib.request.Request(
            self.url, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            answer = json.loads(resp.read())["response"].strip().lower()
        return "yes" in answer


class OpenAICompatProvider(Provider):
    """Covers OpenAI and any OpenAI-compatible endpoint (Groq, Together, etc.)."""
    def __init__(self, model: str, api_key: str, base_url: str = "https://api.openai.com/v1",
                 provider_name: str = "openai"):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.name = f"{provider_name}/{model}"

    def ask(self, prompt: str) -> bool:
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 5,
        }).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "curl/7.68.0",
            },
        )
        wait = 5
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    answer = json.loads(resp.read())["choices"][0]["message"]["content"].strip().lower()
                return "yes" in answer
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    import time
                    time.sleep(wait)
                    wait = min(wait * 2, 60)
                else:
                    raise
        raise RuntimeError(f"Rate limit: gave up after 6 retries")


class AnthropicProvider(Provider):
    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key
        self.name = f"anthropic/{model}"

    def ask(self, prompt: str) -> bool:
        payload = json.dumps({
            "model": self.model,
            "max_tokens": 5,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            answer = json.loads(resp.read())["content"][0]["text"].strip().lower()
        return "yes" in answer


# ---------------------------------------------------------------------------
# Case generation
# ---------------------------------------------------------------------------

def can_both_be_true(e1: str, e2: str):
    try:
        table, _ = evaluate(f"({e1}).({e2})")
        return table.satisfiable
    except ValueError:
        return None


def generate_cases(n_each: int = 50, seed: int = 42, n_vars: int = 4):
    random.seed(seed)
    pool = _VAR_POOL.get(n_vars, EXPRESSIONS)
    conflicts, compatibles = [], []
    tried = set()

    while len(conflicts) < n_each or len(compatibles) < n_each:
        e1, e2 = random.choice(pool), random.choice(pool)
        if (e1, e2) in tried or e1 == e2:
            continue
        tried.add((e1, e2))

        result = can_both_be_true(e1, e2)
        if result is None:
            continue
        if not result and len(conflicts) < n_each:
            conflicts.append((e1, e2, False))
        elif result and len(compatibles) < n_each:
            compatibles.append((e1, e2, True))

    cases = conflicts + compatibles
    random.shuffle(cases)
    return cases


# ---------------------------------------------------------------------------
# Z3 verification — cross-validates engine ground truth before any LLM call
# ---------------------------------------------------------------------------

def _expr_to_z3(expr):
    import z3
    z3_vars = {v: z3.Bool(v) for v in sorted(set(re.findall(r"[A-Z]", expr)))}
    # operator translation: our syntax → Python bitwise ops (z3 overloads these)
    z3_expr = expr.replace("!", "~").replace(".", "&").replace("+", "|")
    return eval(z3_expr, {"__builtins__": {}}, z3_vars)


def _z3_satisfiable(e1: str, e2: str) -> bool:
    import z3
    s = z3.Solver()
    s.add(_expr_to_z3(f"({e1})&({e2})"))
    return s.check() == z3.sat


def verify_with_z3(cases: list) -> bool:
    """Cross-check every engine ground truth label against z3. Returns False on any mismatch."""
    try:
        import z3  # noqa: F401
    except ImportError:
        console.print("[yellow]Warning: z3-solver not installed — skipping verification.[/yellow]")
        console.print("[yellow]  pip install z3-solver   to enable ground truth validation.[/yellow]")
        return True

    console.print(f"[bold blue]⬡ z3[/bold blue]  [dim]verifying {len(cases)} ground truth labels...[/dim]", end=" ")
    mismatches = []

    for e1, e2, engine_result in cases:
        try:
            z3_result = _z3_satisfiable(e1, e2)
            if z3_result != engine_result:
                mismatches.append((e1, e2, engine_result, z3_result))
        except Exception as exc:
            console.print(f"\n[red]z3 error on ({e1}, {e2}): {exc}[/red]")
            mismatches.append((e1, e2, engine_result, None))

    if mismatches:
        console.print(f"\n[bold red]✗  {len(mismatches)} mismatch(es) — engine has a bug:[/bold red]")
        for e1, e2, eng, z3r in mismatches:
            console.print(
                f"  [cyan]{e1}[/cyan] + [cyan]{e2}[/cyan]  "
                f"engine={'yes' if eng else 'no'}  "
                f"z3={'yes' if z3r else 'no' if z3r is not None else 'error'}"
            )
        console.print("[bold red]Aborting — ground truth is unverified.[/bold red]")
        return False

    console.print(f"[bold green]✓  all {len(cases)} cases agree[/bold green]")
    return True


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _case_vars(e1: str, e2: str) -> str:
    return " ".join(sorted(set(re.findall(r"[A-D]", e1 + e2))))


def _make_live_table(results: list, total: int, model_name: str) -> Table:
    done = len(results)
    correct = sum(r["correct"] for r in results)
    wrong = done - correct
    rate = wrong / done * 100 if done else 0.0

    colour = "red" if rate > 30 else "yellow" if rate > 15 else "green"

    pending = total - done
    title = (
        f"[bold white]{model_name}[/bold white]  [dim]·[/dim]  "
        f"[dim]{done}/{total}[/dim]  "
        f"[{colour}]{rate:.1f}% hallucination[/{colour}]"
        + (f"  [yellow]{pending} pending[/yellow]" if pending else "  [bold green]done[/bold green]")
    )

    table = Table(title=title, box=box.SIMPLE_HEAVY, show_lines=False, expand=True,
                  border_style="blue")
    table.add_column("#",      style="dim",          width=4,  justify="right")
    table.add_column("",                             width=2)
    table.add_column("Rule 1", style="cyan",         no_wrap=True)
    table.add_column("Rule 2", style="bright_cyan",  no_wrap=True)
    table.add_column("vars",   style="blue",         width=8)
    table.add_column("engine",                       width=7,  justify="center")
    table.add_column("llm",                          width=5,  justify="center")

    for i, r in enumerate(results[-30:], start=max(1, done - 29)):
        mark       = "[bold green]✓[/bold green]" if r["correct"] else "[bold red]✗[/bold red]"
        engine_val = ("[green]yes[/green]" if r["ground_truth"] else "[red]no[/red]")
        llm_val    = "yes" if r["llm"] else "no"
        llm_col    = f"[dim]{llm_val}[/dim]" if r["correct"] else f"[bold red]{llm_val}[/bold red]"
        vars_used  = _case_vars(r["e1"], r["e2"])
        table.add_row(str(i), mark, r["e1"], r["e2"], vars_used, engine_val, llm_col)

    return table


def _print_config(provider: Provider, cases: list, workers: int):
    n_conflict = sum(1 for _, _, gt in cases if not gt)
    n_compat   = sum(1 for _, _, gt in cases if gt)
    all_vars   = sorted(set(re.findall(r"[A-D]", " ".join(e1 + e2 for e1, e2, _ in cases))))

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="dim",          no_wrap=True)
    grid.add_column(style="bright_white", no_wrap=True)
    grid.add_row("model",        f"[bold]{provider.name}[/bold]")
    grid.add_row("cases",        f"[cyan]{len(cases)}[/cyan]  [dim]({n_conflict} conflict · {n_compat} compatible)[/dim]")
    grid.add_row("variables",    f"[cyan]{len(all_vars)}[/cyan]  [dim]({', '.join(all_vars)})[/dim]")
    grid.add_row("temperature",  "[dim]0  (deterministic)[/dim]")
    grid.add_row("max tokens",   "[dim]5  (yes / no)[/dim]")
    grid.add_row("workers",      f"[cyan]{min(workers, len(cases))}[/cyan]  [dim]parallel[/dim]")
    console.print(Panel(grid, title="[bold blue]benchmark config[/bold blue]",
                         border_style="blue", expand=False))


def run_benchmark(provider: Provider, cases: list, workers: int = 8,
                   dashboard=None, no_think: bool = False) -> dict:
    results = []
    total = len(cases)

    _print_config(provider, cases, workers)

    if dashboard:
        n_conflict = sum(1 for _, _, gt in cases if not gt)
        n_compat   = sum(1 for _, _, gt in cases if gt)
        all_vars   = sorted(set(re.findall(r"[A-D]", " ".join(e1 + e2 for e1, e2, _ in cases))))
        dashboard.push_config(provider.name, total, n_conflict, n_compat, all_vars, min(workers, total))

    template = PROMPT_TEMPLATE_NO_THINK if no_think else PROMPT_TEMPLATE

    def run_case(case):
        e1, e2, ground_truth = case
        llm_answer = provider.ask(template.format(e1=e1, e2=e2))
        return {"e1": e1, "e2": e2, "ground_truth": ground_truth,
                "llm": llm_answer, "correct": llm_answer == ground_truth}

    with Live(console=console, refresh_per_second=4, vertical_overflow="visible") as live:
        live.update(_make_live_table([], total, provider.name))
        with ThreadPoolExecutor(max_workers=min(workers, total)) as executor:
            futures = [executor.submit(run_case, case) for case in cases]
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    if dashboard:
                        dashboard.push_case(
                            len(results), result["e1"], result["e2"],
                            result["ground_truth"], result["llm"], result["correct"],
                        )
                    live.update(_make_live_table(results, total, provider.name))
                except Exception as exc:
                    console.print(f"[red]Error:[/red] {exc}")

    return _summarise(provider.name, results)


def _summarise(model_name: str, results: list) -> dict:
    total = len(results)
    correct_count = sum(r["correct"] for r in results)
    wrong_count = total - correct_count

    conflict_results = [r for r in results if not r["ground_truth"]]
    compat_results   = [r for r in results if r["ground_truth"]]
    missed_conflicts = sum(1 for r in conflict_results if not r["correct"])
    missed_compat    = sum(1 for r in compat_results   if not r["correct"])

    if total == 0:
        console.print("[bold red]No results — all cases failed (model unreachable or wrong name?)[/bold red]")
        return {}
    rate = wrong_count / total * 100
    colour = "red" if rate > 30 else "yellow" if rate > 15 else "green"

    all_vars = sorted(set(re.findall(r"[A-D]", " ".join(r["e1"] + r["e2"] for r in results))))

    summary_text = (
        f"[dim]model[/dim]               [bold white]{model_name}[/bold white]\n"
        f"[dim]total cases[/dim]         [cyan]{total}[/cyan]  [dim]({len(conflict_results)} conflict · {len(compat_results)} compatible)[/dim]\n"
        f"[dim]variables[/dim]           [cyan]{len(all_vars)}[/cyan]  [dim]({', '.join(all_vars)})[/dim]\n"
        f"[dim]temperature[/dim]         [dim]0  (deterministic)[/dim]\n"
        f"[dim]max tokens[/dim]          [dim]5[/dim]\n"
        f"[dim]correct[/dim]             [green]{correct_count}[/green]\n"
        f"[dim]hallucinated[/dim]        [red]{wrong_count}[/red]\n"
        f"[dim]hallucination rate[/dim]  [{colour}]{rate:.1f}%[/{colour}]\n"
    )
    if conflict_results:
        mc_rate = missed_conflicts / len(conflict_results) * 100
        mc_col  = "red" if mc_rate > 50 else "yellow" if mc_rate > 0 else "green"
        summary_text += (f"[dim]missed conflicts[/dim]    [{mc_col}]{missed_conflicts}/{len(conflict_results)}  ({mc_rate:.1f}%)[/{mc_col}]\n")
    if compat_results:
        mp_rate = missed_compat / len(compat_results) * 100
        mp_col  = "red" if mp_rate > 50 else "yellow" if mp_rate > 0 else "green"
        summary_text += (f"[dim]missed compatibles[/dim]  [{mp_col}]{missed_compat}/{len(compat_results)}  ({mp_rate:.1f}%)[/{mp_col}]\n")

    console.print(Panel(summary_text.strip(),
                         title=f"[bold {colour}]results — {model_name}[/bold {colour}]",
                         border_style=colour, expand=False))

    if wrong_count:
        console.print("\n[bold red]Failed cases:[/bold red]")
        for r in results:
            if not r["correct"]:
                console.print(
                    f"  [cyan]{r['e1']:<24}[/cyan] + [cyan]{r['e2']:<24}[/cyan]  "
                    f"engine={'yes' if r['ground_truth'] else 'no'}  "
                    f"[red]llm={'yes' if r['llm'] else 'no'}[/red]"
                )

    return {
        "model": model_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "correct": correct_count,
        "hallucinated": wrong_count,
        "hallucination_rate": round(wrong_count / total * 100, 1),
        "missed_conflicts": missed_conflicts,
        "missed_compat": missed_compat,
        "results": results,
    }


def save_result(summary: dict):
    provider, model = summary["model"].split("/", 1)
    safe_model = model.replace(":", "-").replace("/", "-")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("results", provider, safe_model)
    os.makedirs(path, exist_ok=True)
    filename = os.path.join(path, f"{ts}.json")
    with open(filename, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Results saved: {filename}")
    return filename


# ---------------------------------------------------------------------------
# Visualisation
# ---------------------------------------------------------------------------

def plot_comparison(summaries: list):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    models = [s["model"] for s in summaries]
    rates  = [s["hallucination_rate"] for s in summaries]
    missed_c = [s["missed_conflicts"] / max(s["total"] // 2, 1) * 100 for s in summaries]
    missed_p = [s["missed_compat"]    / max(s["total"] // 2, 1) * 100 for s in summaries]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor("#0d1117")

    colors = ["#f85149" if r > 30 else "#e3b341" if r > 15 else "#3fb950" for r in rates]

    # Left — overall hallucination rate per model
    ax = axes[0]
    ax.set_facecolor("#0d1117")
    bars = ax.barh(models, rates, color=colors)
    ax.set_xlabel("Hallucination rate (%)", color="#e6edf3")
    ax.set_title("Overall hallucination rate by model", color="#e6edf3", fontsize=12)
    ax.tick_params(colors="#e6edf3")
    ax.spines[:].set_edgecolor("#30363d")
    ax.axvline(0, color="#30363d")
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{rate:.1f}%", va="center", color="#e6edf3", fontsize=9)
    ax.set_xlim(0, max(rates + [10]) * 1.2)

    # Right — conflict vs compatible miss rate
    ax2 = axes[1]
    ax2.set_facecolor("#0d1117")
    x = np.arange(len(models))
    w = 0.35
    ax2.bar(x - w/2, missed_c, w, label="Missed conflicts", color="#f85149", alpha=0.85)
    ax2.bar(x + w/2, missed_p, w, label="Missed compatibles", color="#388bfd", alpha=0.85)
    ax2.set_xticks(x)
    ax2.set_xticklabels(models, rotation=20, ha="right", color="#e6edf3", fontsize=8)
    ax2.set_ylabel("Miss rate (%)", color="#e6edf3")
    ax2.set_title("Miss rate by type", color="#e6edf3", fontsize=12)
    ax2.tick_params(colors="#e6edf3")
    ax2.spines[:].set_edgecolor("#30363d")
    ax2.legend(facecolor="#161b22", labelcolor="#e6edf3")

    plt.tight_layout()
    out = os.path.join("images", "benchmark_results.png")
    os.makedirs("images", exist_ok=True)
    plt.savefig(out, dpi=140, bbox_inches="tight", facecolor="#0d1117")
    plt.close()
    print(f"\nComparison chart saved: {out}")


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------

def build_providers(args) -> list:
    providers = []

    if args.provider == "ollama" or args.all:
        models = args.model.split(",") if args.model and args.provider == "ollama" else ["tinyllama"]
        if args.all:
            models = ["tinyllama", "llama3.2:3b"]
        for m in models:
            providers.append(OllamaProvider(m.strip()))

    if args.provider == "groq" or args.all:
        key = os.environ.get("GROQ_API_KEY", "")
        if not key:
            print("GROQ_API_KEY not set — skipping Groq.")
        else:
            models = args.model.split(",") if args.model and args.provider == "groq" else []
            if args.all:
                models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
            for m in models:
                providers.append(OpenAICompatProvider(
                    model=m.strip(), api_key=key,
                    base_url="https://api.groq.com/openai/v1",
                    provider_name="groq"
                ))

    if args.provider == "openai" or args.all:
        key = os.environ.get("OPENAI_API_KEY", "")
        if not key:
            print("OPENAI_API_KEY not set — skipping OpenAI.")
        else:
            models = args.model.split(",") if args.model and args.provider == "openai" else []
            if args.all:
                models = ["gpt-4o-mini", "gpt-4o"]
            for m in models:
                providers.append(OpenAICompatProvider(
                    model=m.strip(), api_key=key,
                    provider_name="openai"
                ))

    if args.provider == "anthropic" or args.all:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            print("ANTHROPIC_API_KEY not set — skipping Anthropic.")
        else:
            models = args.model.split(",") if args.model and args.provider == "anthropic" else []
            if args.all:
                models = ["claude-haiku-4-5-20251001", "claude-sonnet-4-6"]
            for m in models:
                providers.append(AnthropicProvider(model=m.strip(), api_key=key))

    return providers


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM hallucination benchmark")
    parser.add_argument("--provider", choices=["ollama", "groq", "openai", "anthropic"],
                        default="ollama")
    parser.add_argument("--model", default="tinyllama",
                        help="Model name(s), comma-separated for multi-model runs")
    parser.add_argument("--cases", type=int, default=100,
                        help="Total cases per model (split 50/50 conflict/compatible)")
    parser.add_argument("--workers", type=int, default=8,
                        help="Parallel workers for concurrent inference calls (default: 8)")
    parser.add_argument("--all", action="store_true",
                        help="Run all configured providers")
    parser.add_argument("--vars", type=int, default=4, choices=[3, 4, 5, 7, 10],
                        help="Variable count to scope case generation")
    parser.add_argument("--no-think", action="store_true",
                        help="Prepend /no_think to prompt (for qwen3 and other thinking models)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--web", action="store_true",
                        help="Open live dashboard at localhost:8080")
    args = parser.parse_args()

    n_each = max(1, args.cases // 2)
    total_cases = n_each * 2
    print(f"Generating {total_cases} test cases ({n_each} conflicting, {n_each} compatible)...")
    cases = generate_cases(n_each=n_each, seed=args.seed, n_vars=args.vars)

    if not verify_with_z3(cases):
        sys.exit(1)

    providers = build_providers(args)
    if not providers:
        print("No providers configured. Check API keys or --provider flag.")
        sys.exit(1)

    dashboard = None
    if args.web:
        from dashboard import Dashboard
        dashboard = Dashboard(port=8080)
        dashboard.start()
        console.print("[bold blue]Dashboard:[/bold blue] http://localhost:8080")
        console.print("[dim]On a remote VM, use your public IP: http://<your-ip>:8080[/dim]")

    summaries = []
    for provider in providers:
        summary = run_benchmark(provider, cases, workers=args.workers, dashboard=dashboard,
                               no_think=args.no_think)
        if summary:
            save_result(summary)
            plot_comparison([summary])
            chart_path = os.path.join("images", "benchmark_results.png")
            if dashboard:
                dashboard.push_summary(summary, chart_path)
        summaries.append(summary)

    valid = [s for s in summaries if s]
    if len(valid) > 1:
        plot_comparison(valid)

    if dashboard:
        console.print("\n[dim]Dashboard still running at http://localhost:8080 — press Ctrl+C to exit.[/dim]")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass

    print("\nDone.")

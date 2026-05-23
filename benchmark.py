#!/usr/bin/env python3
"""
benchmark.py — Measure LLM logical hallucination rate against engine ground truth.

Generates 50 rule pairs (25 conflicting, 25 compatible), asks an LLM whether
both rules can be satisfied simultaneously, compares to engine answer.

The engine is the oracle — exhaustive enumeration, no guessing.
Every LLM disagreement is a provable logical hallucination.

Runs against Ollama locally — no API key, no cost.
Start Ollama:  systemctl start ollama  (or: ollama serve)
Pull model:    ollama pull llama3.2:3b
"""
import sys
import random
import urllib.request
import json
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.evaluator import evaluate

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "tinyllama"

EXPRESSIONS = [
    "A", "B", "C", "!A", "!B", "!C",
    "A.B", "A+B", "A.!B", "!A.B", "!A.!B",
    "A.B.C", "A+B+C", "A.B+C", "A.(B+C)",
    "!A+B", "A+!B", "!A.!B+A.B",
    "A.B+A.!B",
    "A+!A.B",
    "(A+B).(A+C)",
    "!A+!B", "A.B+!A.!B",
    "A^B", "!(A.B)",
]


def can_both_be_true(e1, e2):
    try:
        table, _ = evaluate(f"({e1}).({e2})")
        return table.satisfiable
    except ValueError:
        return None


def generate_cases(n_each=25, seed=42):
    random.seed(seed)
    conflicts, compatibles = [], []
    tried = set()

    while len(conflicts) < n_each or len(compatibles) < n_each:
        e1, e2 = random.choice(EXPRESSIONS), random.choice(EXPRESSIONS)
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


def ask_llm(e1, e2):
    prompt = (
        "Boolean logic question. Operators: . = AND,  + = OR,  ! = NOT,  ^ = XOR\n"
        f"Rule 1: {e1}\n"
        f"Rule 2: {e2}\n"
        "Can both rules be satisfied simultaneously?\n"
        "Answer only the single word 'yes' or 'no'."
    )
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "num_predict": 5}
    }).encode()

    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        answer = json.loads(resp.read())["response"].strip().lower()
    return "yes" in answer


if __name__ == "__main__":
    n = 5
    print(f"Generating {n*2} test cases ({n} conflicting, {n} compatible)...")
    cases = generate_cases(n_each=n)

    print(f"Testing against {MODEL} via Ollama (CPU)...\n")
    print(f"{'#':>3}  {'':1}  {'Rule 1':<22}  {'Rule 2':<22}  {'engine':<7}  llm")
    print("-" * 70)

    results = []
    for i, (e1, e2, ground_truth) in enumerate(cases):
        llm_answer = ask_llm(e1, e2)
        correct = llm_answer == ground_truth
        results.append({
            "e1": e1, "e2": e2,
            "ground_truth": ground_truth,
            "llm": llm_answer,
            "correct": correct,
        })
        mark = "✓" if correct else "✗"
        print(f"{i+1:>3}  {mark}  {e1:<22}  {e2:<22}  {'yes' if ground_truth else 'no':<7}  {'yes' if llm_answer else 'no'}")

    total = len(results)
    correct_count = sum(r["correct"] for r in results)
    wrong_count = total - correct_count

    conflict_results = [r for r in results if not r["ground_truth"]]
    compat_results   = [r for r in results if r["ground_truth"]]
    missed_conflicts = sum(1 for r in conflict_results if not r["correct"])
    missed_compat    = sum(1 for r in compat_results   if not r["correct"])

    print("\n" + "=" * 70)
    print(f"Model:                 {MODEL} (Ollama, CPU)")
    print(f"Total cases:           {total}")
    print(f"Correct:               {correct_count}")
    print(f"Wrong (hallucinated):  {wrong_count}")
    print(f"Hallucination rate:    {wrong_count / total * 100:.1f}%")
    print("=" * 70)
    print(f"Conflicting pairs:     {len(conflict_results) - missed_conflicts}/{len(conflict_results)} correct  "
          f"({missed_conflicts / len(conflict_results) * 100:.1f}% missed)")
    print(f"Compatible pairs:      {len(compat_results) - missed_compat}/{len(compat_results)} correct  "
          f"({missed_compat / len(compat_results) * 100:.1f}% missed)")
    print("=" * 70)

    if wrong_count:
        print(f"\nFailed cases:")
        for r in results:
            if not r["correct"]:
                print(f"  {r['e1']:<22} + {r['e2']:<22}  engine={'yes' if r['ground_truth'] else 'no'}  llm={'yes' if r['llm'] else 'no'}")

    # --- Visualisation ---
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    fig.patch.set_facecolor("#0d1117")

    # Left: summary bar chart
    ax1.set_facecolor("#0d1117")
    categories = ["All cases", "Conflicting pairs", "Compatible pairs"]
    correct_vals = [
        correct_count,
        len(conflict_results) - missed_conflicts,
        len(compat_results) - missed_compat,
    ]
    wrong_vals = [wrong_count, missed_conflicts, missed_compat]
    totals = [total, len(conflict_results), len(compat_results)]
    x = np.arange(len(categories))
    w = 0.35
    ax1.bar(x - w/2, correct_vals, w, label="Correct", color="#3fb950")
    ax1.bar(x + w/2, wrong_vals,   w, label="Hallucinated", color="#f85149")
    for i, (c, wr, t) in enumerate(zip(correct_vals, wrong_vals, totals)):
        ax1.text(i - w/2, c + 0.05, f"{c}/{t}", ha="center", color="#e6edf3", fontsize=9)
        ax1.text(i + w/2, wr + 0.05, f"{wr}/{t}", ha="center", color="#e6edf3", fontsize=9)
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories, color="#e6edf3", fontsize=10)
    ax1.set_ylabel("Cases", color="#e6edf3")
    ax1.set_title(f"Hallucination rate: {wrong_count/total*100:.0f}%  |  Model: {MODEL}", color="#e6edf3", fontsize=11)
    ax1.tick_params(colors="#e6edf3")
    ax1.spines[:].set_edgecolor("#30363d")
    ax1.legend(facecolor="#161b22", labelcolor="#e6edf3")

    # Right: case-by-case grid
    ax2.set_facecolor("#0d1117")
    ax2.set_title("Case-by-case results", color="#e6edf3", fontsize=11)
    for i, r in enumerate(results):
        y = len(results) - 1 - i
        color = "#3fb950" if r["correct"] else "#f85149"
        label = f"{r['e1']}  +  {r['e2']}"
        verdict = "✓" if r["correct"] else f"✗  (llm={'yes' if r['llm'] else 'no'}, engine={'yes' if r['ground_truth'] else 'no'})"
        ax2.text(0.02, y, label, color="#e6edf3", fontsize=8, va="center", transform=ax2.transData)
        ax2.text(0.98, y, verdict, color=color, fontsize=8, va="center", ha="right", transform=ax2.transData)
    ax2.set_xlim(0, 1)
    ax2.set_ylim(-0.5, len(results) - 0.5)
    ax2.axis("off")

    plt.tight_layout()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "benchmark_results.png")
    plt.savefig(out, dpi=140, bbox_inches="tight", facecolor="#0d1117")
    plt.close()
    print(f"\nPlot saved: {out}")

#!/usr/bin/env python3
"""
visualise_results.py — Generate Reddit-ready visualisations from benchmark results.

Produces 4 PNGs:
  viz_1_headline.png       — the 40% headline, clean and striking
  viz_2_truth_table.png    — truth table proof for the access control failure
  viz_3_failure_panel.png  — all 4 failures side by side with plain English
  viz_4_engine_vs_llm.png  — what the engine sees vs what the model sees
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from boolean_algebra_engine.core.evaluator import evaluate

BG     = "#0d1117"
PANEL  = "#161b22"
BORDER = "#30363d"
GREEN  = "#3fb950"
RED    = "#f85149"
YELLOW = "#e3b341"
TEXT   = "#e6edf3"
MUTED  = "#8b949e"

def save(fig, name):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"Saved: {path}")


# ── VIZ 1 — Headline ────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

categories = ["All cases\n(10 total)", "Conflicting pairs\n(5 total)", "Compatible pairs\n(5 total)"]
correct    = [6, 2, 4]
wrong      = [4, 3, 1]
x = np.arange(len(categories))
w = 0.38

b1 = ax.bar(x - w/2, correct, w, color=GREEN, label="Correct", zorder=3)
b2 = ax.bar(x + w/2, wrong,   w, color=RED,   label="Hallucinated", zorder=3)

for bar, c, t in zip(b1, correct, [10, 5, 5]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.08,
            f"{c}/{t}", ha="center", color=TEXT, fontsize=12, fontweight="bold")
for bar, w_, t in zip(b2, wrong, [10, 5, 5]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.08,
            f"{w_}/{t}", ha="center", color=TEXT, fontsize=12, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(categories, color=TEXT, fontsize=12)
ax.set_ylabel("Cases", color=TEXT, fontsize=12)
ax.set_ylim(0, 7)
ax.tick_params(colors=TEXT)
ax.spines[:].set_edgecolor(BORDER)
ax.set_facecolor(BG)
ax.grid(axis="y", color=BORDER, alpha=0.5, zorder=0)

ax.set_title("tinyllama (1B) on basic boolean logic — 40% hallucination rate",
             color=TEXT, fontsize=14, pad=15)
fig.text(0.5, 0.01,
         "3 variables · symbolic notation · no ambiguity · engine verified every answer by exhaustive enumeration",
         ha="center", color=MUTED, fontsize=9)

ax.legend(facecolor=PANEL, labelcolor=TEXT, edgecolor=BORDER, fontsize=11)
save(fig, "viz_1_headline.png")


# ── VIZ 2 — Truth table proof (A.B vs !A+!B) ────────────────────────────────

table1, _ = evaluate("A.B")
table2, _ = evaluate("!A+!B")
table3, _ = evaluate("(A.B).(!A+!B)")

fig, axes = plt.subplots(1, 3, figsize=(13, 5))
fig.patch.set_facecolor(BG)
fig.suptitle('Why "A.B" and "!A+!B" always conflict — the access control failure',
             color=TEXT, fontsize=13, y=1.02)

for ax, table, title, highlight in zip(
    axes,
    [table1, table2, table3],
    ["Rule 1:  A.B\n(admin AND valid session)",
     "Rule 2:  !A+!B\n(not admin OR no session)",
     "Both rules simultaneously\n(A.B).(!A+!B)"],
    [GREEN, GREEN, RED]
):
    ax.set_facecolor(BG)
    rows = [{**r.inputs, "out": r.output} for r in table.rows]
    cols = list(table.variables) + ["out"]
    arr  = np.array([[row[c] for c in cols] for row in rows])

    for i, row in enumerate(arr):
        for j, val in enumerate(row):
            is_out = (j == len(cols) - 1)
            if is_out:
                color = GREEN if val == 1 else RED
            else:
                color = "#1f2937"
            rect = mpatches.FancyBboxPatch(
                (j - 0.4, i - 0.4), 0.8, 0.8,
                boxstyle="round,pad=0.05",
                facecolor=color, edgecolor=BORDER, linewidth=0.5
            )
            ax.add_patch(rect)
            ax.text(j, i, str(int(val)), ha="center", va="center",
                    color=TEXT, fontsize=13, fontweight="bold" if is_out else "normal")

    ax.set_xlim(-0.6, len(cols) - 0.4)
    ax.set_ylim(-0.6, len(arr) - 0.4)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols, color=TEXT, fontsize=11)
    ax.set_yticks(range(len(arr)))
    ax.set_yticklabels([f"row {i}" for i in range(len(arr))], color=MUTED, fontsize=9)
    ax.tick_params(colors=TEXT, length=0)
    ax.spines[:].set_edgecolor(BORDER)
    ax.set_title(title, color=highlight, fontsize=10, pad=10)
    ax.invert_yaxis()

axes[2].text(0.5, -0.18,
    "All zeros. The rules can NEVER both be satisfied.\nThe model said they were compatible.",
    ha="center", transform=axes[2].transAxes, color=RED, fontsize=10, fontweight="bold")

plt.tight_layout()
save(fig, "viz_2_truth_table.png")


# ── VIZ 3 — All 4 failures in plain English ──────────────────────────────────

failures = [
    {
        "expr": "A.B  +  !A+!B",
        "engine": "CONFLICT",
        "llm": "compatible",
        "plain": "\"Grant access if admin AND valid session\"\n\"Deny if not admin OR no session\"\n→ Every qualifying user is simultaneously granted and denied.",
        "domain": "Access Control"
    },
    {
        "expr": "A.B.C  +  !C",
        "engine": "CONFLICT",
        "llm": "compatible",
        "plain": "\"Dispense if prescription valid AND patient verified AND in stock\"\n\"Do not dispense if not in stock\"\n→ Drug is dispensed when stock state is ambiguous.",
        "domain": "Pharmacy"
    },
    {
        "expr": "A.!B  +  A.B+!A.!B",
        "engine": "CONFLICT",
        "llm": "compatible",
        "plain": "\"Flag for review if on probation AND no training\"\n\"Status consistent if probation and training match\"\n→ System flags and validates the same record simultaneously.",
        "domain": "HR Compliance"
    },
    {
        "expr": "(A+B).(A+C)  +  !A",
        "engine": "COMPATIBLE",
        "llm": "conflict",
        "plain": "\"Approve if (good credit OR guarantor) AND (good credit OR collateral)\"\n\"This applicant has no good credit\"\n→ Model blocks a valid approval path. Qualified applicant rejected.",
        "domain": "Loan Approval"
    },
]

fig, axes = plt.subplots(2, 2, figsize=(14, 9))
fig.patch.set_facecolor(BG)
fig.suptitle("4 real-world consequences of logical hallucination\ntinyllama got every one of these wrong",
             color=TEXT, fontsize=14, y=1.01)

for ax, f in zip(axes.flat, failures):
    ax.set_facecolor(PANEL)
    ax.spines[:].set_edgecolor(BORDER)
    ax.set_xticks([])
    ax.set_yticks([])

    is_false_conflict = f["engine"] == "COMPATIBLE"
    engine_color = GREEN if f["engine"] == "COMPATIBLE" else RED

    ax.text(0.5, 0.95, f["domain"], transform=ax.transAxes,
            ha="center", va="top", color=YELLOW, fontsize=13, fontweight="bold")
    ax.text(0.5, 0.83, f["expr"], transform=ax.transAxes,
            ha="center", va="top", color=TEXT, fontsize=10,
            fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.3", facecolor=BG, edgecolor=BORDER))

    ax.text(0.5, 0.67, f["plain"], transform=ax.transAxes,
            ha="center", va="top", color=MUTED, fontsize=9,
            wrap=True, linespacing=1.6)

    verdict_y = 0.18
    ax.text(0.28, verdict_y, f"Engine: {f['engine']}", transform=ax.transAxes,
            ha="center", color=engine_color, fontsize=11, fontweight="bold")
    ax.text(0.72, verdict_y, f"Model:  {f['llm']}", transform=ax.transAxes,
            ha="center", color=RED, fontsize=11, fontweight="bold")

    ax.axhline(y=0.22, color=BORDER, linewidth=0.8)

plt.tight_layout()
save(fig, "viz_3_failure_panel.png")


# ── VIZ 4 — Engine vs LLM on the same problem ────────────────────────────────

fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(13, 6))
fig.patch.set_facecolor(BG)
fig.suptitle("Same problem. Engine vs LLM. One is always right.",
             color=TEXT, fontsize=14)

# Left — engine
ax_left.set_facecolor(PANEL)
ax_left.spines[:].set_edgecolor(GREEN)
ax_left.spines[:].set_linewidth(2)
ax_left.set_xticks([])
ax_left.set_yticks([])
ax_left.set_title("The Engine", color=GREEN, fontsize=13, pad=10)

engine_lines = [
    ("Input",        "A.B  +  !A+!B",          TEXT),
    ("",             "",                         TEXT),
    ("Step 1",       "Parse to prefix notation", MUTED),
    ("Step 2",       "Evaluate all 4 rows",      MUTED),
    ("",             "A=0 B=0 → 0 · 1 = 0",     MUTED),
    ("",             "A=0 B=1 → 0 · 1 = 0",     MUTED),
    ("",             "A=1 B=0 → 0 · 1 = 0",     MUTED),
    ("",             "A=1 B=1 → 1 · 0 = 0",     MUTED),
    ("Step 3",       "All rows = 0",             MUTED),
    ("",             "",                         TEXT),
    ("Answer",       "CONFLICT — always false",  RED),
    ("Time",         "0.3ms",                    GREEN),
    ("Certainty",    "100% — exhaustive",        GREEN),
]

for i, (label, value, color) in enumerate(engine_lines):
    y = 0.92 - i * 0.068
    if label:
        ax_left.text(0.08, y, label + ":", transform=ax_left.transAxes,
                     color=MUTED, fontsize=9, fontweight="bold")
    ax_left.text(0.35, y, value, transform=ax_left.transAxes,
                 color=color, fontsize=9, fontfamily="monospace" if "=" in value or "." in value else "sans-serif")

# Right — LLM
ax_right.set_facecolor(PANEL)
ax_right.spines[:].set_edgecolor(RED)
ax_right.spines[:].set_linewidth(2)
ax_right.set_xticks([])
ax_right.set_yticks([])
ax_right.set_title("tinyllama (1B)", color=RED, fontsize=13, pad=10)

llm_lines = [
    ("Input",        "A.B  +  !A+!B",                  TEXT),
    ("",             "",                                 TEXT),
    ("Process",      "Token prediction over",           MUTED),
    ("",             "training distribution",           MUTED),
    ("",             "",                                MUTED),
    ("",             "A.B looks like 'both true'",      MUTED),
    ("",             "!A+!B looks like 'one false'",    MUTED),
    ("",             "Both can exist... probably?",     MUTED),
    ("",             "",                                MUTED),
    ("",             "",                                TEXT),
    ("Answer",       "compatible  ✗ WRONG",             RED),
    ("Time",         "28 seconds",                      RED),
    ("Certainty",    "none — prediction",               RED),
]

for i, (label, value, color) in enumerate(llm_lines):
    y = 0.92 - i * 0.068
    if label:
        ax_right.text(0.08, y, label + ":", transform=ax_right.transAxes,
                      color=MUTED, fontsize=9, fontweight="bold")
    ax_right.text(0.35, y, value, transform=ax_right.transAxes,
                  color=color, fontsize=9)

fig.text(0.5, 0.01,
         "The engine checks every possible input. The model guesses. This is not a model quality problem — it is architectural.",
         ha="center", color=MUTED, fontsize=9)

plt.tight_layout()
save(fig, "viz_4_engine_vs_llm.png")

print("\nAll visualisations saved. Ready to post.")

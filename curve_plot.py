#!/usr/bin/env python3
"""
curve_plot.py — Plot hallucination rate vs variable count for each model.

Reads all JSONs under results/curve/ and produces images/curve.png.

Usage:
  python3 curve_plot.py
"""

import os
import json
import glob
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS_DIR = os.path.join("results", "curve")
OUT_PATH    = os.path.join("images", "curve.png")

BG      = "#0d1117"
BG2     = "#161b22"
BORDER  = "#30363d"
TEXT    = "#e6edf3"
MUTED   = "#8b949e"

PALETTE = [
    "#58a6ff", "#3fb950", "#f85149", "#d29922",
    "#bc8cff", "#ff7b72", "#79c0ff", "#56d364",
]


def load_results() -> dict:
    model_data = defaultdict(dict)
    pattern = os.path.join(RESULTS_DIR, "**", "*.json")
    for path in glob.glob(pattern, recursive=True):
        with open(path) as f:
            data = json.load(f)
        model = data.get("model", "unknown")
        n_vars = data.get("n_vars")
        if n_vars is None:
            continue
        # keep latest result per (model, n_vars)
        if n_vars not in model_data[model] or data["timestamp"] > model_data[model][n_vars]["timestamp"]:
            model_data[model][n_vars] = data
    return model_data


def plot(model_data: dict):
    if not model_data:
        print("No curve results found in results/curve/ — run curve.py first.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    for i, (model, by_vars) in enumerate(sorted(model_data.items())):
        xs = sorted(by_vars.keys())
        ys = [by_vars[n]["hallucination_rate"] for n in xs]
        colour = PALETTE[i % len(PALETTE)]
        ax.plot(xs, ys, marker="o", linewidth=2, markersize=7,
                color=colour, label=model)
        for x, y in zip(xs, ys):
            ax.annotate(f"{y:.0f}%", (x, y),
                        textcoords="offset points", xytext=(0, 8),
                        ha="center", fontsize=8, color=colour)

    ax.set_xlabel("Variable count (n)", color=TEXT, fontsize=11)
    ax.set_ylabel("Hallucination rate (%)", color=TEXT, fontsize=11)
    ax.set_title("LLM hallucination rate vs logical complexity",
                 color=TEXT, fontsize=13, pad=14)
    ax.set_ylim(0, 105)
    ax.axhline(50, color=MUTED, linewidth=0.8, linestyle="--", alpha=0.5,
               label="coin flip (50%)")
    ax.axhline(100, color=BORDER, linewidth=0.6, linestyle=":")
    ax.tick_params(colors=TEXT)
    ax.spines[:].set_edgecolor(BORDER)
    ax.set_facecolor(BG2)

    legend = ax.legend(facecolor=BG2, labelcolor=TEXT, edgecolor=BORDER,
                       fontsize=9, loc="upper left")

    plt.tight_layout()
    os.makedirs("images", exist_ok=True)
    plt.savefig(OUT_PATH, dpi=140, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"Chart saved: {OUT_PATH}")


if __name__ == "__main__":
    plot(load_results())

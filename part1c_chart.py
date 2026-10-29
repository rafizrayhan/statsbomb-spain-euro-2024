"""
Part 1 chart: Spain (and Portugal) against all 24 teams at Euro 2024.

One row per dominance measure. Each dot is a team; right = better.
Input:  results/euro2024_team_totals.csv (from part 1)
Output: figures/part1_spain_vs_field.png
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

ROWS = [  # column, label, higher is better, format
    ("time_share", "Possession (time on the ball)", True, "{:.0%}"),
    ("field_tilt", "Field tilt (share of final-third passes)", True, "{:.0%}"),
    ("np_shots_p90", "Shots per 90", True, "{:.1f}"),
    ("np_xg_p90", "xG per 90", True, "{:.2f}"),
    ("np_xg_against_p90", "xG conceded per 90", False, "{:.2f}"),
    ("ppda", "Pressing (PPDA, lower = more intense)", False, "{:.1f}"),
    ("high_ball_wins_p90", "Ball wins in attacking third per 90", True, "{:.1f}"),
]
SURFACE, INK, INK_2, INK_3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
TRACK, GREY = "#e8e7e3", "#c9c8c2"
SPAIN, PORTUGAL = "#eb6834", "#2a78d6"


def ordinal(n):
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def main():
    os.makedirs("figures", exist_ok=True)
    t = pd.read_csv("results/euro2024_team_totals.csv", index_col="team")
    for f in font_manager.findSystemFonts():
        if "Inter" in f:
            font_manager.fontManager.addfont(f)
    plt.rcParams.update({"font.family": "Inter", "text.color": INK,
                         "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})

    fig, ax = plt.subplots(figsize=(11, 8.2))
    n = len(ROWS)
    rng = np.random.default_rng(3)
    for i, (col, label, high, fmt) in enumerate(ROWS):
        y = n - 1 - i
        v = t[col]
        lo, hi = v.min(), v.max()
        pos = (v - lo) / (hi - lo)
        if not high:
            pos = 1 - pos
        ax.hlines(y, 0, 1, color=TRACK, lw=8, capstyle="round", zorder=1)
        others = pos.drop(["Spain", "Portugal"])
        ax.scatter(others, y + rng.uniform(-0.06, 0.06, len(others)), s=36, color=GREY,
                   edgecolor=SURFACE, lw=0.8, zorder=2)
        ax.scatter([pos["Portugal"]], [y], s=120, color=PORTUGAL, edgecolor=SURFACE,
                   lw=1.5, zorder=3)
        ax.scatter([pos["Spain"]], [y], s=200, color=SPAIN, edgecolor=SURFACE, lw=2,
                   zorder=4)
        rank = int(v.rank(ascending=not high, method="min")["Spain"])
        ax.text(-0.03, y + 0.2, label, ha="left", fontsize=11, color=INK, va="bottom",
                fontweight="semibold")
        ax.text(1.03, y, f"Spain {fmt.format(v['Spain'])}", ha="left", va="center",
                fontsize=10.5, color=SPAIN, fontweight="bold")
        ax.text(1.03, y - 0.24, f"{ordinal(rank)} of 24", ha="left", va="center",
                fontsize=9.5, color=INK_2)
    ax.text(0, -0.75, "← worse", fontsize=9.5, color=INK_3)
    ax.text(1, -0.75, "better →", fontsize=9.5, color=INK_3, ha="right")
    ax.set_xlim(-0.04, 1.22)
    ax.set_ylim(-0.95, n - 0.35)
    ax.axis("off")

    fig.text(0.045, 0.965, "Did Spain dominate Euro 2024?", fontsize=19, fontweight="bold",
             va="top")
    fig.text(0.045, 0.925, "Spain and Portugal were the only teams in the top 4 on all "
             "seven measures. Portugal went out in the quarter-finals.",
             fontsize=11, color=INK_2, va="top")
    # Legend
    fig.text(0.045, 0.885, "●", fontsize=15, color=SPAIN, va="center")
    fig.text(0.068, 0.885, "Spain", fontsize=10.5, color=INK_2, va="center")
    fig.text(0.13, 0.885, "●", fontsize=12, color=PORTUGAL, va="center")
    fig.text(0.15, 0.885, "Portugal", fontsize=10.5, color=INK_2, va="center")
    fig.text(0.23, 0.885, "●", fontsize=10, color=GREY, va="center")
    fig.text(0.248, 0.885, "Other 22 teams", fontsize=10.5, color=INK_2, va="center")
    fig.text(0.045, 0.02, "Data: StatsBomb open data, Euro 2024. First 90 minutes only, "
             "11 v 11. Extra time, shootouts and play after red cards excluded. "
             "xG excludes penalties.", fontsize=8, color=INK_3)
    fig.subplots_adjust(left=0.05, right=0.97, top=0.85, bottom=0.07)
    fig.savefig("figures/part1_spain_vs_field.png", dpi=200)
    print("Saved figures/part1_spain_vs_field.png")


if __name__ == "__main__":
    main()

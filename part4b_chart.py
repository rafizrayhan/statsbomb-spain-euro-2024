"""
Part 4 chart: how quickly Spain scored after winning the ball, per tournament.

Each dot is an open-play goal (first 90 minutes, 11 v 11). Black line = median.
Input:  results/spain_shots_speed.csv, results/speed_by_team.csv (from part 4)
Output: figures/part4_spain_goal_speed.png
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

ORDER = ["Euro 2020", "World Cup 2022", "Euro 2024"]
SURFACE, INK, INK_2, INK_3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
ZONE, OLD, NEW = "#f1f0ec", "#9b9a94", "#eb6834"
CAP, FAST = 120, 15


def ordinal(n):
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def main():
    os.makedirs("figures", exist_ok=True)
    S = pd.read_csv("results/spain_shots_speed.csv")
    T = pd.read_csv("results/speed_by_team.csv")
    for f in font_manager.findSystemFonts():
        if "Inter" in f:
            font_manager.fontManager.addfont(f)
    plt.rcParams.update({"font.family": "Inter", "text.color": INK,
                         "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})

    fig, ax = plt.subplots(figsize=(12.5, 5.8))
    ax.axvspan(0, FAST, color=ZONE, zorder=0)
    ax.text(FAST / 2, 2.62, "Within\n15 s", ha="center", va="center", fontsize=9,
            color=INK_3)
    rng = np.random.default_rng(2)
    for i, t in enumerate(ORDER):
        y = 2 - i
        c = NEW if t == "Euro 2024" else OLD
        g = S[(S.tournament == t) & S.goal]
        x = np.minimum(g.seconds.values, CAP)
        ax.scatter(x, y + rng.uniform(-0.18, 0.18, len(x)), s=70, color=c,
                   edgecolor=SURFACE, lw=1.3, zorder=3)
        med = g.seconds.median()
        ax.plot([med, med], [y - 0.3, y + 0.3], color=INK, lw=2.2, zorder=4)
        d = T[T.tournament == t].set_index("team")
        rank = int(d.fast_shots_p90.rank(ascending=False, method="min")["Spain"])
        ax.text(CAP + 4, y + 0.17, f"median {med:.0f} s · {g.passes.median():.0f} passes",
                fontsize=10.5, fontweight="semibold", color=c, va="center")
        ax.text(CAP + 4, y - 0.13, f"{g.fast.mean():.0%} of {len(g)} goals within 15 s",
                fontsize=9.5, color=INK_2, va="center")
        ax.text(CAP + 4, y - 0.38, f"fast shots per 90: {ordinal(rank)} of {len(d)} teams",
                fontsize=9, color=INK_3, va="center")
    ax.set_yticks(range(3))
    ax.set_yticklabels(ORDER[::-1], fontsize=11.5, fontweight="bold")
    for lab, t in zip(ax.get_yticklabels(), ORDER[::-1]):
        lab.set_color(NEW if t == "Euro 2024" else OLD)
    ax.set_xlim(-1, CAP + 1)
    ax.set_ylim(-0.6, 2.85)
    ax.set_xticks([0, 15, 30, 60, 90, 120])
    ax.set_xticklabels(["0 s", "15 s", "30 s", "60 s", "90 s", "120 s+"], fontsize=9.5,
                       color=INK_3)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xlabel("Seconds from winning the ball to scoring", fontsize=10.5, color=INK_2)

    fig.text(0.02, 0.97, "In 2022, none of Spain's goals came within 15 seconds. In 2024, "
             "half did.", fontsize=17, fontweight="bold", va="top")
    fig.text(0.02, 0.905, "Each dot is an open-play goal (no penalties or set pieces). "
             "Black line = median.", fontsize=11, color=INK_2, va="top")
    fig.text(0.02, 0.02, "Data: StatsBomb open data. First 90 minutes, 11 v 11. Time "
             "measured from the start of Spain's possession. Set-piece goals = within 10 "
             "seconds of a corner, free kick or throw-in.", fontsize=8, color=INK_3)
    fig.subplots_adjust(left=0.13, right=0.73, top=0.8, bottom=0.17)
    fig.savefig("figures/part4_spain_goal_speed.png", dpi=200)
    print("Saved figures/part4_spain_goal_speed.png")


if __name__ == "__main__":
    main()

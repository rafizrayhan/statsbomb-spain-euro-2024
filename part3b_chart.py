"""
Part 3 chart: same flanks, different wingers.

Left: share of Spain's final-third entries by lane, per tournament (mini pitches).
Right: Spain's wingers per 90 minutes on the wing, per tournament.

Input:  results/spain_lanes.csv, results/spain_winger_group.csv (from part 3)
Output: figures/part3_same_flanks_different_wingers.png
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

ORDER = ["Euro 2020", "World Cup 2022", "Euro 2024"]
SURFACE, INK, INK_2, INK_3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
GRID, OLD, NEW = "#e8e7e3", "#9b9a94", "#eb6834"


def main():
    os.makedirs("figures", exist_ok=True)
    L = pd.read_csv("results/spain_lanes.csv").groupby("tournament").sum(numeric_only=True)
    G = pd.read_csv("results/spain_winger_group.csv", index_col="tournament").loc[ORDER]
    L["eff"] = (L[["box_left", "box_centre", "box_right"]].sum(axis=1)
                / L[["final_third_left", "final_third_centre", "final_third_right"]]
                .sum(axis=1))
    for f in font_manager.findSystemFonts():
        if "Inter" in f:
            font_manager.fontManager.addfont(f)
    plt.rcParams.update({"font.family": "Inter", "text.color": INK,
                         "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})
    fig = plt.figure(figsize=(13.5, 7.6))

    # ----- left: one bar per tournament, split by lane -----
    tot = L[["final_third_left", "final_third_centre", "final_third_right"]].sum(axis=1)
    axl = fig.add_axes([0.035, 0.2, 0.44, 0.48])
    for i, t in enumerate(ORDER):
        y = 2 - i
        c = NEW if t == "Euro 2024" else OLD
        left = 0
        for lane, alpha in [("left", 1.0), ("centre", 0.35), ("right", 0.7)]:
            share = L.loc[t, f"final_third_{lane}"] / tot[t]
            axl.barh(y, share, left=left, height=0.5, color=c, alpha=alpha,
                     edgecolor=SURFACE, lw=2, zorder=2)
            axl.text(left + share / 2, y, f"{share:.0%}", ha="center", va="center",
                     fontsize=12.5, fontweight="bold",
                     color="white" if alpha > 0.5 else INK, zorder=3)
            left += share
        axl.text(-0.02, y, t, ha="right", va="center", fontsize=11, fontweight="bold",
                 color=c)
        axl.text(1.03, y + 0.06, f"{L.loc[t, 'eff'] * 100:.0f}", ha="left", va="center",
                 fontsize=14, fontweight="bold", color=c)
        axl.text(1.03, y - 0.19, "box entries per 100\nfinal-third entries", ha="left",
                 va="center", fontsize=8.5, color=INK_2, linespacing=1.15)
    for x, lab in [(0.22, "Left"), (0.5, "Centre"), (0.8, "Right")]:
        axl.text(x, 2.45, lab, ha="center", fontsize=10, color=INK_2)
    axl.set_xlim(-0.3, 1.25)
    axl.set_ylim(-0.5, 2.7)
    axl.axis("off")
    fig.text(0.035, 0.84, "Same flanks", fontsize=15, fontweight="bold")
    fig.text(0.035, 0.80, "Share of Spain's final-third entries by lane, and how often "
             "they got the ball into the box.", fontsize=10, color=INK_2)

    # ----- right: winger bars -----
    metrics = [("dribbles_completed", "Dribbles\ncompleted"),
               ("carries_into_box", "Carries into\nthe box"),
               ("box_entries", "Passes and carries\ninto the box")]
    ax = fig.add_axes([0.56, 0.2, 0.41, 0.52])
    w = 0.25
    for j, t in enumerate(ORDER):
        c = NEW if t == "Euro 2024" else OLD
        vals = [G.loc[t, m] for m, _ in metrics]
        xs = np.arange(len(metrics)) + (j - 1) * (w + 0.02)
        ax.bar(xs, vals, width=w, color=c, alpha=1 if t == "Euro 2024" else 0.55 + j * 0.2,
               zorder=2, label=t)
        for x, v in zip(xs, vals):
            ax.text(x, v + 0.08, f"{v:.1f}", ha="center", fontsize=10,
                    fontweight="bold" if t == "Euro 2024" else "normal",
                    color=c if t == "Euro 2024" else INK_2)
    ax.set_xticks(range(len(metrics)))
    ax.set_xticklabels([l for _, l in metrics], fontsize=10.5, color=INK_2)
    ax.set_yticks([])
    for sp in ["top", "right", "left"]:
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0)
    ax.set_ylim(0, 5.4)
    ax.legend(frameon=False, fontsize=10, loc="upper left", labelcolor=INK_2,
              bbox_to_anchor=(0, 1.02), ncol=3, handlelength=1.2, columnspacing=1.4)
    fig.text(0.56, 0.84, "Different wingers", fontsize=15, fontweight="bold")
    fig.text(0.56, 0.80, "Spain's wingers, per 90 minutes on the wing. 2024: Yamal and "
             "Williams.", fontsize=10, color=INK_2)

    fig.text(0.035, 0.965, "Spain attacked down the same flanks. Their wingers changed "
             "what happened there.", fontsize=18, fontweight="bold", va="top")
    fig.text(0.035, 0.925, "At Euro 2024, Spain got the ball into the box more often for "
             "each final-third entry, as the wingers carried it in nearly twice as often.", fontsize=11.5,
             color=INK_2, va="top")
    fig.text(0.035, 0.03, "Data: StatsBomb open data. First 90 minutes, 11 v 11. "
             "Final-third entry = completed pass or carry ending in the final third. Box "
             "entries exclude set pieces. Wingers = players at left/right wing or "
             "left/right midfield in that match.", fontsize=8, color=INK_3)
    fig.savefig("figures/part3_same_flanks_different_wingers.png", dpi=200)
    print("Saved figures/part3_same_flanks_different_wingers.png")


if __name__ == "__main__":
    main()

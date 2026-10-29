"""
Part 2 chart: how Spain's style changed across three tournaments.

Six panels; in each, every Spain match is a dot and the line marks the
tournament average (minutes-weighted). The game-state panel shows totals.

Input:  results/spain_matches.csv, results/spain_game_state.csv,
        results/spain_opponent_adjusted.csv (from part 2)
Output: figures/part2_spain_style_change.png
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

ORDER = ["Euro 2020", "World Cup 2022", "Euro 2024"]
LABELS = ["Euro\n2020", "World Cup\n2022", "Euro\n2024"]
SURFACE, INK, INK_2, INK_3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
GRID, OLD, NEW = "#e8e7e3", "#9b9a94", "#eb6834"


def style_ax(ax, title, sub, ylim, fmt):
    ax.set_title(title, loc="left", fontsize=12.5, fontweight="bold", pad=24)
    ax.text(0, 1.035, sub, transform=ax.transAxes, fontsize=9.5, color=INK_2)
    ax.set_xticks(range(3))
    ax.set_xticklabels(LABELS, fontsize=9.5, color=INK_2)
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylim(*ylim)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(fmt))
    ax.tick_params(length=0, labelsize=9, colors=INK_3)
    for sp in ["top", "right", "left"]:
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis="y", color=GRID, lw=0.7)
    ax.set_axisbelow(True)


def dots(ax, df, col, fmt):
    rng = np.random.default_rng(7)
    for i, t in enumerate(ORDER):
        d = df[df.tournament == t]
        c = NEW if t == "Euro 2024" else OLD
        ax.scatter(i + rng.uniform(-0.13, 0.13, len(d)), d[col], s=42, color=c,
                   alpha=0.55, edgecolor=SURFACE, lw=0.8, zorder=2)
        avg = (d[col] * d.minutes).sum() / d.minutes.sum()
        ax.hlines(avg, i - 0.3, i + 0.3, color=c, lw=3, zorder=3)
        ax.text(i + 0.34, avg, fmt(avg, None), va="center", fontsize=10,
                fontweight="bold", color=c)


def main():
    os.makedirs("figures", exist_ok=True)
    m = pd.read_csv("results/spain_matches.csv")
    gs = pd.read_csv("results/spain_game_state.csv")
    adj = pd.read_csv("results/spain_opponent_adjusted.csv")
    for f in font_manager.findSystemFonts():
        if "Inter" in f:
            font_manager.fontManager.addfont(f)
    plt.rcParams.update({"font.family": "Inter", "text.color": INK,
                         "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})
    pct = lambda v, _: f"{v:.0%}"
    pct_pts = lambda v, _: f"{v * 100:+.0f} pts"
    num1 = lambda v, _: f"{v:.1f}"

    fig, axes = plt.subplots(2, 3, figsize=(13, 9.4))
    a = axes.flat

    dots(a[0], m, "time_share", pct)
    style_ax(a[0], "Possession", "Share of time on the ball", (0.4, 1.0), pct)

    level = gs[gs.state == "level"].set_index("tournament").loc[ORDER]
    for i, t in enumerate(ORDER):
        c = NEW if t == "Euro 2024" else OLD
        v = level.loc[t, "possession (time)"]
        a[1].bar(i, v, width=0.5, color=c, alpha=0.85, zorder=2)
        a[1].text(i, v + 0.012, f"{v:.0%}", ha="center", fontsize=10.5,
                  fontweight="bold", color=c)
    style_ax(a[1], "Possession when level", "Only while the score was level", (0.4, 1.0),
             pct)

    dots(a[2], adj, "adjusted", pct_pts)
    a[2].axhline(0, color=INK_3, lw=1, ls="--", zorder=1)
    style_ax(a[2], "Possession vs same opponents", "Spain minus what other teams had",
             (-0.1, 0.45), pct_pts)

    dots(a[3], m, "passes_per_possession", num1)
    style_ax(a[3], "Passes per possession", "Fewer = quicker attacks", (4, 15.5), num1)

    dots(a[4], m, "build_up_speed", num1)
    style_ax(a[4], "Build-up speed", "Metres forward per second, in possession",
             (1.2, 3.6), lambda v, _: f"{v:.1f}")

    dots(a[5], m, "long_ball_share", pct)
    style_ax(a[5], "Long-ball share", "Share of passes over 30 m", (0.0, 0.25), pct)

    fig.text(0.04, 0.975, "Did Spain change how they play?", fontsize=20,
             fontweight="bold", va="top")
    fig.text(0.04, 0.938, "Less of the ball at Euro 2024, even when the score was level and "
             "against the same opponents. Quicker attacks, but not more long balls.",
             fontsize=11.5, color=INK_2, va="top")
    fig.text(0.04, 0.012, "Data: StatsBomb open data. Each dot is a Spain match (first 90 "
             "minutes, 11 v 11; extra time, shootouts and play after red cards excluded). "
             "Line = tournament average.", fontsize=8, color=INK_3)
    fig.subplots_adjust(left=0.06, right=0.96, top=0.82, bottom=0.08, hspace=0.62,
                        wspace=0.32)
    fig.savefig("figures/part2_spain_style_change.png", dpi=200)
    print("Saved figures/part2_spain_style_change.png")


if __name__ == "__main__":
    main()

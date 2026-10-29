"""
Part 1b: Opponent-adjusted dominance at Euro 2024

A raw average rewards teams with easy fixtures. Here each match is judged
against what OTHER teams did against the same opponent:

  adjusted value = team's value in the match
                   - average value other teams achieved against that opponent

Example: if teams usually had 40% of the ball against France and Spain had 58%,
Spain's adjusted possession for that match is +18 points.

Input:  results/team_matches.csv (from part 1)
Output: results/euro2024_opponent_adjusted.csv, printed rankings
"""

import pandas as pd

METRICS = {"time_share": "Possession (time)", "field_tilt": "Field tilt",
           "xg_diff_p90": "xG difference per 90", "np_xg_p90": "xG per 90",
           "np_xg_against_p90": "xG against per 90"}


def main():
    df = pd.read_csv("results/team_matches.csv")
    df = df[df.tournament == "Euro 2024"].copy()
    df["np_xg_p90"] = df.np_xg / df.minutes * 90
    df["np_xg_against_p90"] = df.np_xg_against / df.minutes * 90
    df["xg_diff_p90"] = df.np_xg_p90 - df.np_xg_against_p90

    # What teams achieved AGAINST each opponent, excluding the match being judged
    adj_rows = []
    for _, r in df.iterrows():
        others = df[(df.opponent == r.opponent) & (df.match_id != r.match_id)]
        row = {"team": r.team, "opponent": r.opponent, "match_id": r.match_id,
               "minutes": r.minutes, "n_reference": len(others)}
        for m in METRICS:
            row[m] = r[m] - others[m].mean()
        adj_rows.append(row)
    adj = pd.DataFrame(adj_rows)
    adj.to_csv("results/euro2024_opponent_adjusted.csv", index=False)
    print(f"Reference matches per opponent: min {adj.n_reference.min()}, "
          f"max {adj.n_reference.max()}\n")

    tot = adj.groupby("team").apply(
        lambda g: pd.Series({m: (g[m] * g.minutes).sum() / g.minutes.sum()
                             for m in METRICS} | {"matches": len(g)}),
        include_groups=False)
    pd.set_option("display.width", 200)
    for m, label in METRICS.items():
        asc = m == "np_xg_against_p90"
        top = tot[m].sort_values(ascending=asc)
        rank = list(top.index).index("Spain") + 1
        print(f"{label}: Spain {tot.loc['Spain', m]:+.2f}, rank {rank} of {len(tot)}  |  "
              + " | ".join(f"{t} {v:+.2f}" for t, v in top.head(4).items()))

    print("\nSpain match by match (adjusted for opponent)")
    sp = adj[adj.team == "Spain"][["opponent", "time_share", "xg_diff_p90"]]
    print(sp.round(2).to_string(index=False))
    print("\nPortugal match by match (adjusted for opponent)")
    pt = adj[adj.team == "Portugal"][["opponent", "time_share", "xg_diff_p90"]]
    print(pt.round(2).to_string(index=False))


if __name__ == "__main__":
    main()

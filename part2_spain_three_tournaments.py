"""
Part 2: Did Spain change their style between Euro 2020, World Cup 2022 and
Euro 2024?

Three views, all using the cleaning rules in common.py:
  A. Style measures per tournament, and Spain's rank among all teams there
  B. Game state: possession and passes per possession when level / leading /
     trailing (a leading team often lets the opponent have the ball)
  C. Opponent-adjusted possession: Spain's share minus what other teams had
     against the same opponent at the same tournament

Input:  results/team_matches.csv (from part 1), cached events in data/events/
Output: results/spain_matches.csv, results/spain_game_state.csv,
        results/spain_opponent_adjusted.csv, printed tables
"""

import pandas as pd

from common import TOURNAMENTS, clean_events, load_events, ts_seconds

ORDER = list(TOURNAMENTS)
STYLE = ["time_share", "pass_share", "field_tilt", "passes_per_possession",
         "build_up_speed", "long_ball_share", "pass_completion", "ppda"]
RATES = ["np_xg", "np_xg_against", "np_shots", "high_ball_wins"]


def wavg(g, col):
    return (g[col] * g.minutes).sum() / g.minutes.sum()


def view_a(df):
    print("A. Spain's style per tournament (minutes-weighted), and rank among all teams\n")
    rows = []
    for t in ORDER:
        d = df[df.tournament == t]
        teams = d.groupby("team").apply(
            lambda g: pd.Series({c: wavg(g, c) for c in STYLE}
                                | {f"{c}_p90": g[c].sum() / g.minutes.sum() * 90
                                   for c in RATES}), include_groups=False)
        n = len(teams)
        row = {"tournament": t, "matches": d[d.team == "Spain"].match_id.nunique()}
        for c in STYLE + [f"{c}_p90" for c in RATES]:
            asc = c in ("ppda", "np_xg_against_p90")
            r = int(teams[c].rank(ascending=asc, method="min")["Spain"])
            row[c] = f"{teams.loc['Spain', c]:.2f} ({r}/{n})"
        rows.append(row)
    out = pd.DataFrame(rows).set_index("tournament").T
    print(out.to_string())
    print("\nRank 1 = highest value, except PPDA and xG against where 1 = lowest.\n")


def spain_states(match_id, spain_name):
    """Possession seconds and passes per possession by game state, for Spain."""
    ev, _, _ = clean_events(load_events(match_id))
    spain_id = next(e["team"]["id"] for e in ev if e["team"]["name"] == spain_name)
    score = {"spain": 0, "opp": 0}
    seq = {}  # (period, possession) -> dict
    for e in ev:
        key = (e["period"], e["possession"])
        if key not in seq:
            diff = score["spain"] - score["opp"]
            state = "level" if diff == 0 else ("leading" if diff > 0 else "trailing")
            seq[key] = {"state": state, "spain": e["possession_team"]["id"] == spain_id,
                        "t0": ts_seconds(e), "t1": ts_seconds(e), "passes": 0}
        s = seq[key]
        s["t1"] = ts_seconds(e)
        if e["type"]["name"] == "Pass" and e["team"]["id"] == spain_id:
            s["passes"] += 1
        # Update the score after the event
        scored = (e["type"]["name"] == "Shot" and e["shot"]["outcome"]["name"] == "Goal") \
            or e["type"]["name"] == "Own Goal For"
        if scored:
            score["spain" if e["team"]["id"] == spain_id else "opp"] += 1
    return pd.DataFrame([{"state": s["state"], "spain": s["spain"],
                          "seconds": s["t1"] - s["t0"], "passes": s["passes"]}
                         for s in seq.values()])


def view_b(df):
    print("B. Game state: Spain's possession (time) and passes per possession\n")
    rows = []
    for t in ORDER:
        for _, m in df[(df.tournament == t) & (df.team == "Spain")].iterrows():
            s = spain_states(m.match_id, "Spain")
            s["tournament"] = t
            s["opponent"] = m.opponent
            rows.append(s)
    allseq = pd.concat(rows)
    out = []
    for (t, st), g in allseq.groupby(["tournament", "state"]):
        sp = g[g.spain]
        out.append({"tournament": t, "state": st,
                    "minutes in state": g.seconds.sum() / 60,
                    "possession (time)": sp.seconds.sum() / g.seconds.sum(),
                    "passes per possession": sp.passes.mean()})
    res = pd.DataFrame(out)
    res["tournament"] = pd.Categorical(res.tournament, ORDER, ordered=True)
    res = res.sort_values(["state", "tournament"])
    res.to_csv("results/spain_game_state.csv", index=False)
    print(res.round(2).to_string(index=False))
    print("\nMinutes = ball-in-play time inside possession sequences (excludes stoppages).\n")


def view_c(df):
    print("C. Opponent-adjusted possession (time): Spain minus what other teams had "
          "against the same opponent\n")
    rows = []
    for _, r in df[df.team == "Spain"].iterrows():
        ref = df[(df.tournament == r.tournament) & (df.opponent == r.opponent)
                 & (df.match_id != r.match_id)]
        rows.append({"tournament": r.tournament, "opponent": r.opponent,
                     "spain_share": r.time_share, "others_vs_opp": ref.time_share.mean(),
                     "adjusted": r.time_share - ref.time_share.mean(),
                     "n_ref": len(ref), "minutes": r.minutes})
    adj = pd.DataFrame(rows)
    adj.to_csv("results/spain_opponent_adjusted.csv", index=False)
    summ = adj.groupby("tournament").apply(
        lambda g: pd.Series({"raw possession": wavg(g.rename(columns={"spain_share": "v"}), "v"),
                             "adjusted (points above others)": wavg(
                                 g.rename(columns={"adjusted": "v"}), "v")}),
        include_groups=False).loc[ORDER]
    print(summ.round(3).to_string())
    print("\nMatch by match:")
    print(adj[["tournament", "opponent", "spain_share", "others_vs_opp", "adjusted"]]
          .round(2).to_string(index=False))


def main():
    df = pd.read_csv("results/team_matches.csv")
    sp = df[df.team == "Spain"].sort_values("date")
    sp.to_csv("results/spain_matches.csv", index=False)
    pd.set_option("display.width", 220)
    view_a(df)
    view_b(df)
    view_c(df)


if __name__ == "__main__":
    main()

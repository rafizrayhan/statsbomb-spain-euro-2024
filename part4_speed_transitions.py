"""
Part 4: Speed and transitions. Did Spain attack faster and win the ball higher?

For every team at each tournament (first 90 minutes, 11 v 11):
  open-play shot  = non-penalty shot, excluding shots within 10 seconds of a
                    corner, free kick or throw-in (same rule as earlier projects)
  fast shot       = open-play shot within 15 seconds of the start of the
                    team's possession
  high regain     = a possession whose first event by the team is in the
                    attacking third (x >= 80) and did not start from a restart
  high-regain shot= open-play shot in such a possession

Input:  results/team_matches.csv (from part 1), cached events
Output: results/speed_by_team.csv, results/spain_shots_speed.csv, printed tables
"""

import concurrent.futures as cf

import numpy as np
import pandas as pd

from common import TOURNAMENTS, clean_events, load_events, ts_seconds

ORDER = list(TOURNAMENTS)
SET_PIECE_PATTERNS = {"From Corner", "From Free Kick", "From Throw In"}
RESTARTS = SET_PIECE_PATTERNS | {"From Goal Kick", "From Kick Off"}
FAST, SET_PIECE_WINDOW = 15, 10


def match_shots(match_id):
    ev, minutes, _ = clean_events(load_events(match_id))
    start, first_own, passes = {}, {}, {}
    rows = []
    for e in ev:
        key = (e["period"], e["possession"])
        start.setdefault(key, (ts_seconds(e), e["play_pattern"]["name"]))
        tid = e.get("team", {}).get("id")
        if tid == e["possession_team"]["id"] and "location" in e and key not in first_own:
            first_own[key] = e["location"][0]
        if e["type"]["name"] == "Pass" and tid == e["possession_team"]["id"]:
            passes[key] = passes.get(key, 0) + 1
        if e["type"]["name"] != "Shot" or e["shot"].get("type", {}).get("name") == "Penalty":
            continue
        t0, pattern = start[key]
        secs = ts_seconds(e) - t0
        if pattern in SET_PIECE_PATTERNS and secs <= SET_PIECE_WINDOW:
            continue
        high = first_own.get(key, 0) >= 80 and pattern not in RESTARTS
        rows.append({"match_id": match_id, "team": e["team"]["name"], "seconds": secs,
                     "passes": passes.get(key, 0), "xg": e["shot"].get("statsbomb_xg", 0),
                     "goal": e["shot"]["outcome"]["name"] == "Goal", "high_regain": high})
    return rows


def main():
    tm = pd.read_csv("results/team_matches.csv")
    ids = tm.match_id.unique().tolist()
    rows = []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for r in ex.map(match_shots, ids):
            rows.extend(r)
    S = pd.DataFrame(rows).merge(tm[["match_id", "team", "tournament"]].drop_duplicates(),
                                 on=["match_id", "team"])
    S["fast"] = S.seconds <= FAST
    mins = tm.groupby(["tournament", "team"]).minutes.sum()

    g = S.groupby(["tournament", "team"])
    T = pd.DataFrame({
        "op_shots": g.size(), "fast_shots": g.fast.sum(),
        "high_regain_shots": g.high_regain.sum(),
        "high_regain_xg": g.apply(lambda d: d.xg[d.high_regain].sum(), include_groups=False),
        "fast_xg": g.apply(lambda d: d.xg[d.fast].sum(), include_groups=False),
        "median_seconds": g.seconds.median(), "median_passes": g.passes.median(),
    }).join(mins)
    for c in ["op_shots", "fast_shots", "high_regain_shots", "high_regain_xg", "fast_xg"]:
        T[f"{c}_p90"] = T[c] / T.minutes * 90
    T["fast_share"] = T.fast_shots / T.op_shots
    T.to_csv("results/speed_by_team.csv")
    S[S.team == "Spain"].to_csv("results/spain_shots_speed.csv", index=False)

    cols = ["op_shots_p90", "fast_share", "fast_shots_p90", "high_regain_shots_p90",
            "high_regain_xg_p90", "median_seconds", "median_passes"]
    pd.set_option("display.width", 220)
    print("Spain per tournament (rank among all teams in brackets; rank 1 = highest,")
    print("except median seconds and passes where 1 = lowest, i.e. fastest)\n")
    out = {}
    for t in ORDER:
        d = T.loc[t]
        col = {}
        for c in cols:
            asc = c.startswith("median")
            r = int(d[c].rank(ascending=asc, method="min")["Spain"])
            v = d.loc["Spain", c]
            col[c] = f"{v:.0%} ({r}/{len(d)})" if c == "fast_share" else f"{v:.2f} ({r}/{len(d)})"
        out[t] = col
    print(pd.DataFrame(out).to_string())

    sp = S[S.team == "Spain"]
    print("\nSpain's open-play GOALS: count, share within 15 s, median seconds")
    for t in ORDER:
        gls = sp[(sp.tournament == t) & sp.goal]
        print(f"  {t}: {len(gls)} goals, {gls.fast.mean():.0%} within 15 s, "
              f"median {gls.seconds.median():.0f} s, "
              f"{int(gls.high_regain.sum())} from high regains")

    print("\nTournament medians (all teams) for context")
    for t in ORDER:
        d = T.loc[t]
        print(f"  {t}: fast share {d.fast_share.median():.0%}, high-regain shots per 90 "
              f"{d.high_regain_shots_p90.median():.2f}")


if __name__ == "__main__":
    main()

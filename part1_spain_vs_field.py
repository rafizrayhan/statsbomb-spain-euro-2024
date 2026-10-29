"""
Part 1: How dominant were Spain at Euro 2024, compared with all 24 teams?

Builds a team-match feature table for all three tournaments (reused by later
parts), then ranks Spain among the 24 Euro 2024 teams.

Output: results/team_matches.csv  (one row per team per match, all tournaments)
        results/euro2024_team_totals.csv
        printed Spain ranks and Spain's match-by-match possession
"""

import concurrent.futures as cf
import os

import pandas as pd

from common import TOURNAMENTS, load_events, tournament_matches
from features import team_match_features

# Shares are averaged (weighted by minutes); counts become per-90 rates
SHARES = ["pass_share", "time_share", "field_tilt", "pass_completion",
          "passes_per_possession", "build_up_speed", "long_ball_share"]
COUNTS = ["high_ball_wins", "ball_wins", "np_shots", "np_xg", "np_shots_against",
          "np_xg_against", "goals_for", "goals_against"]
# Metric: (label, higher is better for "dominance"?)
SHOW = {
    "time_share": ("Possession (time on the ball)", True),
    "pass_share": ("Possession (share of passes)", True),
    "field_tilt": ("Field tilt (final-third passes)", True),
    "pass_completion": ("Pass completion", True),
    "np_xg_p90": ("xG per 90 (no penalties)", True),
    "np_shots_p90": ("Shots per 90", True),
    "np_xg_against_p90": ("xG against per 90", False),
    "np_shots_against_p90": ("Shots against per 90", False),
    "xg_diff_p90": ("xG difference per 90", True),
    "ppda": ("PPDA (lower = more pressing)", False),
    "high_ball_wins_p90": ("Ball wins in attacking third per 90", True),
    "passes_per_possession": ("Passes per possession", None),
    "build_up_speed": ("Build-up speed (m/s)", None),
    "long_ball_share": ("Long-ball share", None),
}


def match_rows(label, m):
    events = load_events(m["match_id"])
    h, a = m["home_team"], m["away_team"]
    rows = []
    for team, opp in [(h["home_team_id"], a["away_team_id"]),
                      (a["away_team_id"], h["home_team_id"])]:
        name = h["home_team_name"] if team == h["home_team_id"] else a["away_team_name"]
        opp_name = a["away_team_name"] if team == h["home_team_id"] else h["home_team_name"]
        f = team_match_features(events, team, opp)
        f.update({"tournament": label, "match_id": m["match_id"],
                  "date": m["match_date"], "stage": m["competition_stage"]["name"],
                  "team": name, "opponent": opp_name})
        rows.append(f)
    return rows


def build_table():
    jobs = [(lab, m) for lab in TOURNAMENTS for m in tournament_matches(lab)]
    rows = []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for r in ex.map(lambda j: match_rows(*j), jobs):
            rows.extend(r)
    df = pd.DataFrame(rows)
    df.to_csv("results/team_matches.csv", index=False)
    print(f"Team-match rows: {len(df)} "
          f"({df.groupby('tournament').match_id.nunique().to_dict()} matches)")
    print(f"Matches cut by a red card: {df.red_card_cut.notna().sum() // 2}\n")
    return df


def team_totals(df):
    g = df.groupby("team")
    tot = g[COUNTS].sum()
    tot["minutes"] = g.minutes.sum()
    tot["matches"] = g.match_id.nunique()
    for c in COUNTS:
        tot[f"{c}_p90"] = tot[c] / tot.minutes * 90
    tot["xg_diff_p90"] = tot.np_xg_p90 - tot.np_xg_against_p90
    for c in SHARES:
        tot[c] = g.apply(lambda x: (x[c] * x.minutes).sum() / x.minutes.sum(),
                         include_groups=False)
    # PPDA over the tournament = mean of match PPDA weighted by minutes
    tot["ppda"] = g.apply(lambda x: (x.ppda * x.minutes).sum() / x.minutes.sum(),
                          include_groups=False)
    return tot


def main():
    os.makedirs("results", exist_ok=True)
    df = build_table()
    e24 = df[df.tournament == "Euro 2024"]
    tot = team_totals(e24)
    tot.to_csv("results/euro2024_team_totals.csv")

    n = len(tot)
    rows = []
    for col, (label, better_high) in SHOW.items():
        asc = False if better_high in (True, None) else True
        rank = int(tot[col].rank(ascending=asc, method="min")["Spain"])
        rows.append({"metric": label, "Spain": tot.loc["Spain", col],
                     "median of 24": tot[col].median(), "Spain rank": f"{rank} of {n}"})
    out = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print("Spain at Euro 2024 compared with all 24 teams (first 90 minutes, 11 v 11)")
    print("Rank 1 = highest, except xG/shots against and PPDA where 1 = lowest\n")
    print(out.round(3).to_string(index=False))

    print("\nSpain's possession match by match (first 90 minutes)")
    sp = e24[e24.team == "Spain"].sort_values("date")
    print(sp[["date", "stage", "opponent", "goals_for", "goals_against", "pass_share",
              "time_share", "np_xg", "np_xg_against"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()

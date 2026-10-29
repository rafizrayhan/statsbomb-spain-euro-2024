"""
Data-integrity and robustness checks. Run after part 1 to 4.

  1. Every tournament loads fully, with sensible minutes per team-match
  2. Possession shares (time and passes) sum to 100% in every match
  3. First-90-minute goals equal the official score in every match without
     extra time or a red-card cut (tests goals, own goals, shootout exclusion)
  4. Lists the matches cut by a red card
  5. Lane orientation: Yamal (right wing) and Williams (left wing) touches
     fall in the lanes the analysis calls right and left
  6. Fast goals under a stricter rule: every possession that started from a
     corner, free kick or throw-in excluded
"""

import pandas as pd

from common import TOURNAMENTS, clean_events, load_events, tournament_matches, ts_seconds


def main():
    tm = pd.read_csv("results/team_matches.csv")

    print("1. Matches, rows and minutes per team-match")
    print(tm.groupby("tournament").agg(matches=("match_id", "nunique"), rows=("team", "size"),
                                       min_minutes=("minutes", "min"),
                                       max_minutes=("minutes", "max")).round(1), "\n")

    s = tm.groupby("match_id")[["time_share", "pass_share"]].sum()
    print("2. Possession shares sum to 1: time "
          f"{s.time_share.min():.4f} to {s.time_share.max():.4f}, passes "
          f"{s.pass_share.min():.4f} to {s.pass_share.max():.4f}; "
          f"correlation of the two measures {tm.time_share.corr(tm.pass_share):.2f}\n")

    checked = bad = 0
    for lab in TOURNAMENTS:
        for m in tournament_matches(lab):
            ev = load_events(m["match_id"])
            rows = tm[tm.match_id == m["match_id"]]
            if max(e["period"] for e in ev) > 2 or rows.red_card_cut.notna().any():
                continue
            checked += 1
            h = rows[rows.team == m["home_team"]["home_team_name"]].iloc[0]
            if (h.goals_for, h.goals_against) != (m["home_score"], m["away_score"]):
                bad += 1
                print("   mismatch:", lab, m["home_team"]["home_team_name"],
                      m["away_team"]["away_team_name"])
    print(f"3. First-90 goals vs official score: {checked} matches checked, "
          f"{bad} mismatches\n")

    print("4. Matches cut by a red card")
    r = tm[tm.red_card_cut.notna()].drop_duplicates("match_id")
    print(r[["tournament", "team", "opponent", "red_card_cut"]].round(0)
          .to_string(index=False), "\n")

    ys = {"Yamal": [], "Williams": []}
    for mid in tm[(tm.team == "Spain") & (tm.tournament == "Euro 2024")].match_id:
        ev, _, _ = clean_events(load_events(mid))
        for e in ev:
            n = e.get("player", {}).get("name", "")
            for k in ys:
                if k in n and "location" in e:
                    ys[k].append(e["location"][1])
    print("5. Lane orientation")
    for k, v in ys.items():
        v = pd.Series(v)
        print(f"   {k}: {(v > 160 / 3).mean():.0%} of touches in the 'right' lane, "
              f"{(v < 80 / 3).mean():.0%} in the 'left' lane")

    print("\n6. Fast goals with every set-piece possession excluded")
    sp_patterns = {"From Corner", "From Free Kick", "From Throw In"}
    for t in TOURNAMENTS:
        goals, shots = [], []
        for mid in tm[(tm.team == "Spain") & (tm.tournament == t)].match_id:
            ev, _, _ = clean_events(load_events(mid))
            start = {}
            for e in ev:
                k = (e["period"], e["possession"])
                start.setdefault(k, (ts_seconds(e), e["play_pattern"]["name"]))
                if (e["type"]["name"] == "Shot" and e["team"]["name"] == "Spain"
                        and e["shot"].get("type", {}).get("name") != "Penalty"):
                    t0, pat = start[k]
                    if pat in sp_patterns:
                        continue
                    secs = ts_seconds(e) - t0
                    shots.append(secs)
                    if e["shot"]["outcome"]["name"] == "Goal":
                        goals.append(secs)
        g, sh = pd.Series(goals), pd.Series(shots)
        print(f"   {t}: {(g <= 15).sum()} of {len(g)} goals within 15 s; "
              f"{(sh <= 15).mean():.0%} of {len(sh)} shots within 15 s")


if __name__ == "__main__":
    main()

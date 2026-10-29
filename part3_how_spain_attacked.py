"""
Part 3: How did Spain attack? Flanks, box entries and wingers, 2020 / 2022 / 2024.

Lanes (from the attacking team's view, StatsBomb y runs 0-80 with y=0 on the
attacking team's left): left y < 26.7, centre 26.7-53.3, right y > 53.3.

  Final-third entry: a completed pass or a carry that starts before x=80 and
                     ends at x >= 80 (lane = where it ends)
  Box entry:         a completed pass (not a set piece) or a carry that ends in
                     the penalty box and starts outside it
  Chance origin:     lane where each key pass started
  Wingers:           players listed at Left Wing / Right Wing / Left Midfield /
                     Right Midfield in the event data

Same cleaning rules as every part (first 90 minutes, 11 v 11).
Input:  results/team_matches.csv (from part 1), cached events
Output: results/spain_lanes.csv, results/spain_wingers.csv, printed tables
"""

from collections import defaultdict

import pandas as pd

from common import TOURNAMENTS, clean_events, clock, load_events

ORDER = list(TOURNAMENTS)
SET_PIECES = {"Corner", "Free Kick", "Throw-in", "Goal Kick", "Kick Off"}
WING = {"Left Wing", "Right Wing", "Left Midfield", "Right Midfield"}


def lane(y):
    return "left" if y < 80 / 3 else ("right" if y > 160 / 3 else "centre")


def in_box(x, y):
    return x >= 102 and 18 <= y <= 62


def end_loc(e):
    t = e["type"]["name"]
    if t == "Pass":
        return e["pass"]["end_location"]
    if t == "Carry":
        return e["carry"]["end_location"]
    return None


def completed_or_carry(e):
    t = e["type"]["name"]
    if t == "Carry":
        return True
    return t == "Pass" and "outcome" not in e["pass"]


def player_minutes(ev, end):
    """Minutes per player inside the cleaned window, with their main position."""
    on, off, pos = {}, {}, {}
    for e in ev:
        t = e["type"]["name"]
        if t == "Starting XI":
            for p in e["tactics"]["lineup"]:
                on[p["player"]["id"]] = 0.0
                pos[p["player"]["id"]] = (p["player"]["name"], p["position"]["name"],
                                          e["team"]["name"])
        elif t == "Substitution":
            off[e["player"]["id"]] = clock(e)
            r = e["substitution"]["replacement"]
            on[r["id"]] = clock(e)
            pos[r["id"]] = (r["name"], e.get("position", {}).get("name", ""),
                            e["team"]["name"])
    return {pid: (max(min(off.get(pid, end), end) - st, 0), *pos[pid])
            for pid, st in on.items()}


def analyse_match(match_id, spain="Spain"):
    raw = load_events(match_id)
    ev, end, _ = clean_events(raw)
    # Starting XI events have period 1, so they survive cleaning; substitutions too
    mins = player_minutes(ev, end)
    lanes = defaultdict(float)
    players = defaultdict(lambda: defaultdict(float))
    pos_seen = defaultdict(lambda: defaultdict(int))
    passes = {e["id"]: e for e in ev if e["type"]["name"] == "Pass"}
    for e in ev:
        if e.get("team", {}).get("name") != spain or "location" not in e:
            continue
        x, y = e["location"][0], e["location"][1]
        pid = e.get("player", {}).get("id")
        if pid and "position" in e:
            pos_seen[pid][e["position"]["name"]] += 1
        t = e["type"]["name"]
        el = end_loc(e)
        set_piece = t == "Pass" and e["pass"].get("type", {}).get("name") in SET_PIECES
        if el and completed_or_carry(e):
            if x < 80 <= el[0]:
                lanes[f"final_third_{lane(el[1])}"] += 1
            if not set_piece and not in_box(x, y) and in_box(el[0], el[1]):
                lanes[f"box_{lane(el[1])}"] += 1
                if pid:
                    players[pid]["box_entries"] += 1
                    if t == "Carry":
                        players[pid]["carries_into_box"] += 1
        if t == "Dribble" and pid:
            players[pid]["dribbles"] += 1
            if e["dribble"].get("outcome", {}).get("name") == "Complete":
                players[pid]["dribbles_completed"] += 1
        if t == "Pass" and e["pass"].get("cross") and not set_piece and pid:
            players[pid]["crosses"] += 1
            lanes["crosses"] += 1
        if t == "Shot" and "key_pass_id" in e["shot"]:
            kp = passes.get(e["shot"]["key_pass_id"])
            if kp and kp["pass"].get("type", {}).get("name") not in SET_PIECES:
                lanes[f"chance_{lane(kp['location'][1])}"] += 1
                lanes[f"xa_{lane(kp['location'][1])}"] += e["shot"].get("statsbomb_xg", 0)
                players[kp["player"]["id"]]["xa"] += e["shot"].get("statsbomb_xg", 0)
                players[kp["player"]["id"]]["chances"] += 1
        if t == "Shot" and e["shot"].get("type", {}).get("name") != "Penalty" and pid:
            players[pid]["np_xg"] += e["shot"].get("statsbomb_xg", 0)
    rows = []
    for pid, (m, name, start_pos, team) in mins.items():
        if team != spain:
            continue
        seen = pos_seen.get(pid)
        main_pos = max(seen, key=seen.get) if seen else start_pos
        rows.append({"player": name, "position": main_pos, "minutes": m,
                     **players.get(pid, {})})
    return dict(lanes), end, rows


def main():
    df = pd.read_csv("results/team_matches.csv")
    sp = df[df.team == "Spain"]
    lane_rows, player_rows = [], []
    for _, m in sp.iterrows():
        lanes, minutes, rows = analyse_match(m.match_id)
        lanes.update({"tournament": m.tournament, "opponent": m.opponent,
                      "minutes": minutes})
        lane_rows.append(lanes)
        for r in rows:
            r["tournament"] = m.tournament
            player_rows.append(r)

    L = pd.DataFrame(lane_rows).fillna(0)
    L.to_csv("results/spain_lanes.csv", index=False)
    agg = L.groupby("tournament").sum(numeric_only=True).loc[ORDER]
    pd.set_option("display.width", 220)

    print("Spain's attacks by flank (share of each tournament's total)\n")
    out = pd.DataFrame(index=ORDER)
    for kind, label in [("final_third", "Final-third entries"), ("box", "Box entries"),
                        ("chance", "Open-play chances (key pass start)"),
                        ("xa", "Open-play xA (key pass start)")]:
        tot = agg[[f"{kind}_{l}" for l in ("left", "centre", "right")]].sum(axis=1)
        for l in ("left", "centre", "right"):
            out[f"{label}: {l}"] = agg[f"{kind}_{l}"] / tot
    print(out.T.map(lambda v: f"{v:.0%}").to_string())

    print("\nVolume per 90 minutes")
    vol = pd.DataFrame({
        "final-third entries": agg[[c for c in agg if c.startswith("final_third")]].sum(axis=1),
        "box entries": agg[[c for c in agg if c.startswith("box_")]].sum(axis=1),
        "open-play crosses": agg.crosses,
    }).div(agg.minutes, axis=0) * 90
    print(vol.round(1).to_string())

    P = pd.DataFrame(player_rows).fillna(0)
    # Count each match by the position played in it, so only winger minutes count
    P = P[P.position.isin(WING)]
    G = P.groupby("tournament")[["minutes", "dribbles_completed", "carries_into_box",
                                 "box_entries", "chances", "xa", "np_xg"]].sum()
    W = (P.groupby(["tournament", "player"])
          .agg(position=("position", lambda s: s.mode().iat[0]),
               minutes=("minutes", "sum"), dribbles=("dribbles", "sum"),
               dribbles_completed=("dribbles_completed", "sum"),
               carries_into_box=("carries_into_box", "sum"),
               box_entries=("box_entries", "sum"), chances=("chances", "sum"),
               xa=("xa", "sum"), np_xg=("np_xg", "sum"))
          .reset_index())
    W = W[W.minutes >= 150].copy()
    for c in ["dribbles_completed", "carries_into_box", "box_entries", "chances", "xa",
              "np_xg"]:
        W[f"{c}_p90"] = W[c] / W.minutes * 90
    W["dribble_success"] = W.dribbles_completed / W.dribbles.replace(0, pd.NA)
    W.to_csv("results/spain_wingers.csv", index=False)
    print("\nSpain's wingers (150+ minutes in the cleaned window), per 90")
    W["tournament"] = pd.Categorical(W.tournament, ORDER, ordered=True)
    print(W.sort_values(["tournament", "minutes"], ascending=[True, False])[
        ["tournament", "player", "position", "minutes", "dribbles_completed_p90",
         "dribble_success", "carries_into_box_p90", "box_entries_p90", "chances_p90",
         "xa_p90", "np_xg_p90"]].round(2).to_string(index=False))

    print("\nWinger group per tournament (every winger minute), per 90 of winger minutes")
    G = G.loc[ORDER]
    for c in ["dribbles_completed", "carries_into_box", "box_entries", "chances", "xa",
              "np_xg"]:
        G[c] = G[c] / G.minutes * 90
    print(G.round(2).to_string())
    G.to_csv("results/spain_winger_group.csv")
    L["box_per_final_third"] = (
        L[[c for c in L if c.startswith("box_")]].sum(axis=1)
        / L[[c for c in L if c.startswith("final_third")]].sum(axis=1))
    eff = (L.groupby("tournament")[[c for c in L if c.startswith("box_") and c != "box_per_final_third"]]
           .sum().sum(axis=1)
           / L.groupby("tournament")[[c for c in L if c.startswith("final_third")]]
           .sum().sum(axis=1)).loc[ORDER]
    print("\nBox entries per final-third entry:", ", ".join(f"{t} {v:.0%}" for t, v in eff.items()))


if __name__ == "__main__":
    main()

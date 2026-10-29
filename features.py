"""
Team features for one match (after the cleaning rules in common.py).

All event locations are from the perspective of the team performing the event:
pitch 120 x 80, attacking left to right.
"""

import numpy as np

from common import clean_events, ts_seconds

SET_PIECES = {"Corner", "Free Kick", "Throw-in", "Goal Kick", "Kick Off"}
LONG_BALL = 32  # yards, about 30 metres


def possession_time(events):
    """Seconds of possession per team, from StatsBomb possession sequences."""
    spans = {}
    for e in events:
        key = (e["period"], e["possession"])
        t = ts_seconds(e)
        team = e["possession_team"]["id"]
        lo, hi, _ = spans.get(key, (t, t, team))
        spans[key] = (min(lo, t), max(hi, t), team)
    out = {}
    for lo, hi, team in spans.values():
        out[team] = out.get(team, 0) + (hi - lo)
    return out


def is_ball_win(e):
    t = e["type"]["name"]
    if t == "Ball Recovery":
        return not e.get("ball_recovery", {}).get("recovery_failure", False)
    if t == "Interception":
        return e["interception"]["outcome"]["name"] in {"Won", "Success", "Success In Play",
                                                         "Success Out"}
    if t == "Duel" and e["duel"].get("type", {}).get("name") == "Tackle":
        return e["duel"].get("outcome", {}).get("name") in {"Won", "Success",
                                                            "Success In Play", "Success Out"}
    return False


def team_match_features(events, team_id, opp_id):
    ev, minutes, cut = clean_events(events)
    own = [e for e in ev if e.get("team", {}).get("id") == team_id]
    opp = [e for e in ev if e.get("team", {}).get("id") == opp_id]

    def passes(lst):
        return [e for e in lst if e["type"]["name"] == "Pass"]

    def open_play(lst):
        return [e for e in lst if e["pass"].get("type", {}).get("name") not in SET_PIECES]

    p_own, p_opp = passes(own), passes(opp)
    op_own, op_opp = open_play(p_own), open_play(p_opp)
    ptime = possession_time(ev)

    # Field tilt: share of open-play passes in the final third
    ft_own = sum(e["location"][0] >= 80 for e in op_own)
    ft_opp = sum(e["location"][0] >= 80 for e in op_opp)

    # PPDA: opponent open-play passes in their own defensive 60% / our
    # tackles, interceptions and fouls in that zone (lower = more pressing)
    opp_zone = sum(e["location"][0] < 72 for e in op_opp)
    def_acts = 0
    for e in own:
        if "location" not in e or e["location"][0] < 48:
            continue
        n = e["type"]["name"]
        if n in ("Interception", "Foul Committed") or (
                n == "Duel" and e.get("duel", {}).get("type", {}).get("name") == "Tackle"):
            def_acts += 1

    # Ball wins and where they happen
    wins = [e for e in own if is_ball_win(e)]
    high_wins = sum(e["location"][0] >= 80 for e in wins)

    # Own possessions: passes per possession and forward speed
    poss = {}
    for e in ev:
        if e["possession_team"]["id"] == team_id:
            poss.setdefault((e["period"], e["possession"]), []).append(e)
    ppp, speeds = [], []
    for pe in poss.values():
        mine = [e for e in pe if e.get("team", {}).get("id") == team_id]
        ppp.append(sum(e["type"]["name"] == "Pass" for e in mine))
        xs = [e["location"][0] for e in mine if "location" in e]
        dur = ts_seconds(pe[-1]) - ts_seconds(pe[0])
        if len(mine) >= 3 and dur > 0 and xs:
            speeds.append((max(xs) - xs[0]) / dur)

    lengths = [e["pass"]["length"] for e in op_own]

    def np_shots(lst):
        return [e for e in lst if e["type"]["name"] == "Shot"
                and e["shot"].get("type", {}).get("name") != "Penalty"]

    s_own, s_opp = np_shots(own), np_shots(opp)
    goals_for = sum(e["type"]["name"] == "Shot" and e["shot"]["outcome"]["name"] == "Goal"
                    for e in own) + sum(e["type"]["name"] == "Own Goal For" for e in own)
    goals_against = sum(e["type"]["name"] == "Shot" and e["shot"]["outcome"]["name"] == "Goal"
                        for e in opp) + sum(e["type"]["name"] == "Own Goal For" for e in opp)

    return {
        "minutes": minutes,
        "red_card_cut": cut,
        "pass_share": len(p_own) / max(len(p_own) + len(p_opp), 1),
        "time_share": ptime.get(team_id, 0) / max(ptime.get(team_id, 0)
                                                  + ptime.get(opp_id, 0), 1),
        "field_tilt": ft_own / max(ft_own + ft_opp, 1),
        "pass_completion": np.mean(["outcome" not in e["pass"] for e in op_own]),
        "passes_per_possession": np.mean(ppp) if ppp else np.nan,
        "build_up_speed": np.mean(speeds) if speeds else np.nan,
        "long_ball_share": np.mean([l >= LONG_BALL for l in lengths]) if lengths else np.nan,
        "ppda": opp_zone / max(def_acts, 1),
        "high_ball_wins": high_wins,
        "ball_wins": len(wins),
        "np_shots": len(s_own),
        "np_xg": sum(e["shot"].get("statsbomb_xg", 0) for e in s_own),
        "np_shots_against": len(s_opp),
        "np_xg_against": sum(e["shot"].get("statsbomb_xg", 0) for e in s_opp),
        "goals_for": goals_for,
        "goals_against": goals_against,
    }

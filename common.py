"""
Shared data loading and cleaning rules for the Spain project.

Cleaning rules, applied the same way in every part:
  1. First 90 minutes only (periods 1 and 2): extra time and penalty
     shootouts are excluded.
  2. 11 against 11 only: if a red card is shown in the first 90 minutes,
     the match is cut at that moment for both teams.
"""

import json
import os
import time
import urllib.request

BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
EVENT_DIR = "data/events"
TOURNAMENTS = {  # label: (competition name, season name)
    "Euro 2020": ("UEFA Euro", "2020"),
    "World Cup 2022": ("FIFA World Cup", "2022"),
    "Euro 2024": ("UEFA Euro", "2024"),
}
RED = {"Red Card", "Second Yellow"}


def get_json(url, retries=6):
    """Download JSON, waiting and retrying if GitHub rate-limits (HTTP 429)."""
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt * 2)


def tournament_matches(label):
    comp, season = TOURNAMENTS[label]
    c = [x for x in get_json(f"{BASE}/competitions.json")
         if x["competition_name"] == comp and x["season_name"] == season][0]
    return get_json(f"{BASE}/matches/{c['competition_id']}/{c['season_id']}.json")


def load_events(match_id):
    """Events for one match, downloaded once and cached in data/events/."""
    os.makedirs(EVENT_DIR, exist_ok=True)
    path = os.path.join(EVENT_DIR, f"{match_id}.json")
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(get_json(f"{BASE}/events/{match_id}.json"), f)
    with open(path) as f:
        return json.load(f)


def clock(e):
    """Match clock in minutes (StatsBomb 2nd-half minutes already start at 45)."""
    return e["minute"] + e["second"] / 60


def ts_seconds(e):
    """Seconds since the start of the event's period, from the timestamp."""
    h, m, s = e["timestamp"].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def clean_events(events):
    """Apply the cleaning rules. Returns (kept events, minutes of play kept)."""
    reg = [e for e in events if e["period"] in (1, 2)]
    cut = None
    for e in reg:
        card = (e.get("foul_committed", {}).get("card", {}).get("name")
                or e.get("bad_behaviour", {}).get("card", {}).get("name"))
        if card in RED:
            cut = clock(e)
            break
    if cut is not None:
        reg = [e for e in reg if clock(e) < cut]
    end = max(clock(e) for e in reg)
    return reg, end, cut

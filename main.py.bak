#!/usr/bin/env python3
"""Forecast Roblox Up-and-Coming top-10 (make.fun bounty).

Method: empirical place-migration matrix estimated from the given chart history,
split into three 24-hour horizon buckets and averaged (the scored window is 72
hourly reads, so each bucket weighs one third). For every game currently on the
chart we take its marginal probability of occupying each of the top-10 places;
per place we name every candidate with meaningful mass and scale the named mass
to 0.5, leaving the rest unnamed for games that may enter the chart from outside.
Python 3.13, standard library only, deterministic.
"""
import json
import math
import os
from collections import defaultdict

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
MAX_RANK = 15          # model ranks 1..15; anything else is "off chart"
BUCKETS = ((0, 24), (24, 48), (48, 72))   # hours ahead
SCALE = 0.5            # total named probability per place
MIN_P = 0.0005         # below this a candidate is not named
PLACES = 10


def dt_hours(a: str, b: str) -> float:
    from datetime import datetime
    ta = datetime.fromisoformat(a.replace("Z", "+00:00"))
    tb = datetime.fromisoformat(b.replace("Z", "+00:00"))
    return (tb - ta).total_seconds() / 3600.0


def main() -> None:
    with open(os.path.join(INPUT_DIR, "task.json")) as f:
        task = json.load(f)
    places = min(int(task.get("places", PLACES)), PLACES)
    snaps = [json.loads(l) for l in open(os.path.join(INPUT_DIR, "history.ndjson")) if l.strip()]
    snaps.sort(key=lambda s: s["at"])

    last = snaps[-1]
    chart = [r["universe_id"] for r in sorted(last["up_and_coming"], key=lambda x: x["rank"])]
    top = chart[:MAX_RANK]

    # migration counts per horizon bucket: from-place -> to-place (MAX_RANK+1 = off chart)
    OFF = MAX_RANK + 1
    mig = {b: defaultdict(lambda: defaultdict(float)) for b in BUCKETS}
    for i, s in enumerate(snaps):
        a0 = [r["universe_id"] for r in sorted(s["up_and_coming"], key=lambda x: x["rank"])]
        for s2 in snaps:
            d = dt_hours(s["at"], s2["at"])
            if d <= 0:
                continue
            act = [r["universe_id"] for r in sorted(s2["up_and_coming"], key=lambda x: x["rank"])]
            for b in BUCKETS:
                if not (b[0] < d <= b[1]):
                    continue
                for p, uid in enumerate(a0, 1):
                    if p > MAX_RANK:
                        break
                    if uid in act[:MAX_RANK]:
                        q = act.index(uid) + 1
                    else:
                        q = OFF
                    mig[b][p][min(q, OFF)] += 1.0

    # per bucket transition rows (normalised); buckets with no data fall back to persistence
    rows = {}
    for b in BUCKETS:
        rows[b] = {}
        for p in range(1, MAX_RANK + 1):
            tot = sum(mig[b][p].values())
            if tot <= 0:
                rows[b][p] = {q: (1.0 if q == p else 0.0) for q in range(1, OFF + 1)}
            else:
                rows[b][p] = {q: mig[b][p][q] / tot for q in range(1, OFF + 1)}

    # marginal probability per place: average of the three bucket rows
    marg = {q: defaultdict(float) for q in range(1, places + 1)}
    for b in BUCKETS:
        for p, uid in enumerate(top, 1):
            for q in range(1, places + 1):
                marg[q][uid] += rows[b][p][q] / len(BUCKETS)

    probabilities = []
    top10 = chart[:places]
    for q in range(1, places + 1):
        cand = sorted(marg[q].items(), key=lambda x: -x[1])
        cand = [(u, v) for u, v in cand if v > MIN_P]
        s = sum(v for _, v in cand)
        if s > SCALE and s > 0:
            cand = [(u, v * SCALE / s) for u, v in cand]
        for uid, pv in cand:
            probabilities.append({"universe_id": uid, "place": q, "p": round(pv, 10)})

    out = {"probabilities": probabilities, "top10": top10}
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, task.get("output", "forecast.json")), "w") as f:
        f.write(json.dumps(out) + "\n")


if __name__ == "__main__":
    main()

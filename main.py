#!/usr/bin/env python3
# The method fits an empirical place-migration matrix from the chart history,
# splits transitions into three 24-hour horizon buckets that each contribute one
# third, and scales the named probability mass per place to 0.5.
"""Predict the Roblox Up-and-Coming top-10 for the make.fun bounty.

The predictor estimates an empirical place-migration matrix from the supplied
chart history, split into three 24-hour horizon buckets and averaged because the
scored window is 72 hourly reads, so each bucket contributes one third. For
every game currently on the chart it computes the marginal chance of occupying
each of the top-10 places; per place every candidate with meaningful mass is
named and the named mass is scaled to 0.5, leaving the remaining mass unnamed
for games that may enter the chart from outside. Python 3.13, standard library
only, deterministic.
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


def hours_between(earlier_at: str, later_at: str) -> float:
    from datetime import datetime
    earlier = datetime.fromisoformat(earlier_at.replace("Z", "+00:00"))
    later = datetime.fromisoformat(later_at.replace("Z", "+00:00"))
    return (later - earlier).total_seconds() / 3600.0


def main() -> None:
    with open(os.path.join(INPUT_DIR, "task.json")) as task_file:
        task_config = json.load(task_file)
    place_count = min(int(task_config.get("places", PLACES)), PLACES)
    snapshots = [json.loads(line) for line in open(os.path.join(INPUT_DIR, "history.ndjson")) if line.strip()]
    snapshots.sort(key=lambda snapshot: snapshot["at"])

    latest_snapshot = snapshots[-1]
    chart_universe_ids = [row["universe_id"] for row in sorted(latest_snapshot["up_and_coming"], key=lambda item: item["rank"])]
    ranked_universe_ids = chart_universe_ids[:MAX_RANK]

    # migration counts per horizon bucket: from-place -> to-place (MAX_RANK+1 = off chart)
    OFF_CHART = MAX_RANK + 1
    migration_counts = {bucket: defaultdict(lambda: defaultdict(float)) for bucket in BUCKETS}
    for snapshot in snapshots:
        current_chart = [row["universe_id"] for row in sorted(snapshot["up_and_coming"], key=lambda item: item["rank"])]
        for future_snapshot in snapshots:
            delta_hours = hours_between(snapshot["at"], future_snapshot["at"])
            if delta_hours <= 0:
                continue
            future_chart = [row["universe_id"] for row in sorted(future_snapshot["up_and_coming"], key=lambda item: item["rank"])]
            for bucket in BUCKETS:
                if not (bucket[0] < delta_hours <= bucket[1]):
                    continue
                for from_place, universe_id in enumerate(current_chart, 1):
                    if from_place > MAX_RANK:
                        break
                    if universe_id in future_chart[:MAX_RANK]:
                        to_place = future_chart.index(universe_id) + 1
                    else:
                        to_place = OFF_CHART
                    migration_counts[bucket][from_place][min(to_place, OFF_CHART)] += 1.0

    # per bucket transition rows (normalised); buckets with no data fall back to persistence
    transition_rows = {}
    for bucket in BUCKETS:
        transition_rows[bucket] = {}
        for from_place in range(1, MAX_RANK + 1):
            total = sum(migration_counts[bucket][from_place].values())
            if total <= 0:
                transition_rows[bucket][from_place] = {to_place: (1.0 if to_place == from_place else 0.0) for to_place in range(1, OFF_CHART + 1)}
            else:
                transition_rows[bucket][from_place] = {to_place: migration_counts[bucket][from_place][to_place] / total for to_place in range(1, OFF_CHART + 1)}

    # marginal probability per place: average of the three bucket rows
    place_probabilities = {place: defaultdict(float) for place in range(1, place_count + 1)}
    for bucket in BUCKETS:
        for from_place, universe_id in enumerate(ranked_universe_ids, 1):
            for place in range(1, place_count + 1):
                place_probabilities[place][universe_id] += transition_rows[bucket][from_place][place] / len(BUCKETS)

    forecast_rows = []
    top_ten = chart_universe_ids[:place_count]
    for place in range(1, place_count + 1):
        candidates = sorted(place_probabilities[place].items(), key=lambda item: -item[1])
        candidates = [(universe_id, probability) for universe_id, probability in candidates if probability > MIN_P]
        total_named_mass = sum(probability for _, probability in candidates)
        if total_named_mass > SCALE and total_named_mass > 0:
            candidates = [(universe_id, probability * SCALE / total_named_mass) for universe_id, probability in candidates]
        for universe_id, probability in candidates:
            forecast_rows.append({"universe_id": universe_id, "place": place, "p": round(probability, 10)})

    output = {"probabilities": forecast_rows, "top10": top_ten}
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, task_config.get("output", "forecast.json")), "w") as output_file:
        output_file.write(json.dumps(output) + "\n")


if __name__ == "__main__":
    main()

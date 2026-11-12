# roblox-upcoming-forecast

Forecaster for Roblox's Up-and-Coming chart: predicts, with calibrated probabilities, which games hold each of the top 10 places over the next 72 hours.

## Method

Empirical place-migration matrix estimated from the chart history provided at run time, split into three 24-hour horizon buckets and averaged (the scored window is 72 hourly reads, so each bucket weighs one third). Each game currently on the chart gets a marginal probability of occupying each top-10 place; per place, candidates with meaningful mass are named and scaled to 0.5, leaving the rest unnamed for games that may enter the chart from outside.

## Run

```sh
mkdir -p out
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Reads `input/history.ndjson` (chart snapshots) and `input/task.json`, writes `out/forecast.json`.

Python 3.13, standard library only, deterministic.

---
<sub>Entered on [make.fun](https://make.fun/bounty/roblox-up-and-coming-forecast-01) · AI agents build software for cash rewards</sub>

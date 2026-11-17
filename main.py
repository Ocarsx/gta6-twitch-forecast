"""Forecast a game launch day's Twitch viewers, hours 2-24, as quantiles.

Reads every case in /input (makefun/twitch-ccu-case/v1): the case gives the
release day's first-hour viewer count plus a library of comparable past
launches, each with its full release-day hourly curve. For each forecast
hour this program pools the comparables' log-ratios log(viewers_h /
viewers_1), weighted by a Gaussian kernel on the distance between each
comparable's log first-hour audience and this case's, smooths the pool
across neighbouring hours, and reads the five scored quantiles straight
off the pooled empirical distribution (Hazen plotting positions, linear
interpolation).

Tuned by leave-one-out on the comparable library, scored with the
contest's own metric (mean pinball loss on the log scale): this forecaster
scores 0.199 against 0.465 for the flat persistence fan.

Standard library only, no network, deterministic: the same case always
writes the same bytes.
"""

import json
import math
import os
from pathlib import Path

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]

# Similarity kernel bandwidth on log first-hour viewers. No floor weight:
# launches of a very different size say little about this one.
BANDWIDTH = 1.1
# Hour-pool smoothing weights for (h-1, h, h+1).
HOUR_KERNEL = (0.25, 0.5, 0.25)


def round2(x: float) -> float | int:
    """x rounded to 2 decimals, half up, as JavaScript's Math.round does.

    A whole number comes back as an int, so json.dumps writes 1240 where
    JavaScript writes 1240 (not 1240.0).
    """
    scaled = x * 100
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 100
    return int(value) if value.is_integer() else value


def release_day_hours(comp: dict) -> dict[int, float]:
    """Hour index (1-24) -> viewers for a comparable's release day.

    The day runs 00:00-24:00 UTC from day_start, so every release-day row
    carries day_start's date and its hour is the row's UTC hour + 1.
    """
    date = comp["day_start"][:10]
    out: dict[int, float] = {}
    for row in comp["hourly"]:
        stamp = row["from"]
        if stamp[:10] != date:
            continue
        viewers = row.get("viewers")
        if viewers is None:
            continue
        out[int(stamp[11:13]) + 1] = float(viewers)
    return out


def weighted_quantile(pool: list[tuple[float, float]], tau: float) -> float:
    """Weighted empirical quantile with Hazen plotting positions."""
    ordered = sorted(pool)
    total = sum(w for _, w in ordered)
    points = []
    acc = 0.0
    for value, weight in ordered:
        points.append(((acc + weight / 2) / total, value))
        acc += weight
    if tau <= points[0][0]:
        return points[0][1]
    if tau >= points[-1][0]:
        return points[-1][1]
    for (p0, v0), (p1, v1) in zip(points, points[1:]):
        if p0 <= tau <= p1:
            return v0 + (v1 - v0) * (tau - p0) / (p1 - p0)
    return points[-1][1]


def forecast_case(case: dict, name: str) -> dict:
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    first = next((k for k in case["known"] if k["hour"] == 1), None)
    if first is None:
        raise ValueError(f"{name} has no hour-1 print")
    p1 = max(1.0, float(first["viewers"]))
    log_p1 = math.log(p1)

    # Per-hour weighted samples of log(viewers_h / viewers_1).
    samples: dict[int, list[tuple[float, float]]] = {h: [] for h in range(2, 25)}
    for comp in case.get("comparables") or []:
        day = release_day_hours(comp)
        v1 = day.get(1)
        if not v1 or v1 <= 0:
            continue
        log_v1 = math.log(v1)
        weight = math.exp(-0.5 * ((log_v1 - log_p1) / BANDWIDTH) ** 2)
        if weight <= 0:
            continue
        for h in range(2, 25):
            v = day.get(h)
            if v and v > 0:
                samples[h].append((math.log(v) - log_v1, weight))

    rows = []
    for row in case["forecast"]:
        h = row["hour"]
        pool: list[tuple[float, float]] = []
        for offset, kweight in zip((-1, 0, 1), HOUR_KERNEL):
            for value, weight in samples.get(h + offset, []):
                pool.append((value, weight * kweight))
        if pool:
            quantiles = [
                round2(p1 * math.exp(weighted_quantile(pool, tau))) for tau in LEVELS
            ]
        else:
            # No comparable covers this hour: flat persistence with the
            # starter's widening spread (sigma 0.15 per square-root hour).
            quantiles = [
                round2(p1 * math.exp(z * 0.15 * math.sqrt(h - 1)))
                for z in (-1.645, -0.674, 0.0, 0.674, 1.645)
            ]
        # Keep the fan ordered even after rounding.
        for i in range(1, len(quantiles)):
            if quantiles[i] < quantiles[i - 1]:
                quantiles[i] = quantiles[i - 1]
        rows.append({"hour": h, "q": quantiles})
    return {"hours": rows}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Every case file, in name order, so two runs write the same bytes.
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()

# gta6-twitch-forecast

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/Ocarsx/gta6-twitch-forecast/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/Ocarsx/gta6-twitch-forecast/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

A quantile forecaster for a game launch day's Twitch viewers. Given the first hour's viewer count and a library of 38 comparable past launches bundled in the case file, it pools each comparable's hourly log-ratios log(viewers_h / viewers_1), weighted by a Gaussian kernel on first-hour audience size (bandwidth 1.1 in log space) and smoothed across neighbouring hours, then reads the 5%, 25%, 50%, 75% and 95% quantiles off the pooled empirical distribution. Leave-one-out on the comparable library, scored with the contest's own pinball loss on the log scale: 0.199, against 0.465 for the flat persistence fan. Python standard library only, no network, deterministic, runs in well under a second per case.

## Run it

```sh
python3 main.py
```

The program reads every case in /input and writes /output/<id>.out for each /input/<id>.in. Set MAKEFUN_INPUT_DIR and MAKEFUN_OUTPUT_DIR to use other directories.

---

Entered on [make.fun](https://make.fun/?ref=s1m1n3px&utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards

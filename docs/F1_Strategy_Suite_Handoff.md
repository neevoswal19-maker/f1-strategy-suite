# F1 Strategy Intelligence Suite — Project Handoff

Handoff notes for continuing this project in Claude Code. Written 26 Oct 2026.

**Project line (from the brief):** Strategy & Pit-Wall Simulation. Model optimal pit windows and tyre strategies using Monte Carlo simulations and lap pace projections. Python, NumPy, Pandas, Scikit-learn, FastF1, OpenF1 API. Part of an "F1 Strategy Intelligence Suite".

**Owner:** Neev, an AI/ML student and developer. The project runs in **Google Colab**. Neev originally wanted code delivered as chat cells to type in himself, and later asked for a ready `.ipynb`.

---

## 1. Current status

- **Latest deliverable:** `F1_Strategy_Intelligence_Suite.ipynb`, with 21 code cells, a heading above each one, an intro cell, and a final "Settings you can change / Limitations" text cell. The full source for every cell is in section 9 of this file.
- **Tested only against synthetic data.** The cloud sandbox couldn't reach FastF1, Jolpica (Ergast), OpenF1 or Open-Meteo, so every cell was run through a mock harness instead (see section 7). **It has not yet been run on real data.** The first real Colab run is the next thing to do.
- **Not done:** editing the copy already open in Neev's Colab tab. The Chrome extension was unreachable. Neev can upload the new `.ipynb` instead (File → Upload notebook).

## 2. How the project evolved (requests, in order)

1. **Base project:** load a race with FastF1, clean laps, fit an ML tyre-degradation/pace model, search every legal strategy, run Monte Carlo races, find pit windows, add a pit-wall "box now or stay out?" call, and compare against real strategies from OpenF1.
2. **Race picker in the first cell:** pick a season and see the calendar marked `done` or `UPCOMING`. For an upcoming race, say so and project from the last race held at that circuit (up to 3 seasons back).
3. **Wet races:** random rain per simulated race, a track-wetness model, slick/inter/wet crossovers, reactive weather pit calls, safety cars more likely in the wet, a rain forecast for upcoming races (Open-Meteo), and a fallback to a dry race for slick pace when the chosen race was mostly wet.
4. **Final cells plus a text cell** at the end listing the settings you can change and the limitations.
5. **Colab `.ipynb` file.**
6. **Bug report:** "Why does it ask me for the race winner on an upcoming race?" The driver prompt came before the code knew the race was upcoming, so "race winner" meant the winner of the earlier race used as a proxy. Fixed by moving the prompt after the winner prediction (Cell 7) with a sensible default.
7. **Race winner prediction**, which must only show **after practice and qualifying** and use data from those sessions. Same for **sprints**: unlocks after sprint qualifying.
8. Asked Claude to edit the open Colab notebook in Chrome. Not done because the extension was unreachable.
9. This handoff file.

## 3. Pipeline (cell by cell)

| Cell | Title | What it does | Key outputs |
|---|---|---|---|
| 1 | Setup + race picker | Installs FastF1, imports, config. Asks for season and race, prints the calendar with done/UPCOMING. For upcoming races, finds the last race at the same circuit (3 seasons back) | `YEAR`, `event`, `UPCOMING`, `race_utc`, `DATA_YEAR`, `DATA_ROUND`, `RACE_TITLE`, `NOW` |
| 2 | Load race data | Loads the race (FastF1). If over 40% of laps were on wet tyres, loads an earlier dry race at the same circuit for slick pace | `race`, `race_laps`, `session`, `laps` (pace source), `TOTAL_LAPS`, `WAS_WET` |
| 3 | Rain chance | Upcoming race: Open-Meteo forecast for the race window. Past wet race: rain in every sim. Past dry race: what-if `RAIN_DEFAULT` | `P_RAIN` |
| 4 | Race history + driver form (Ergast) | Race results for YEAR-4..YEAR via FastF1's Ergast interface (Jolpica). For upcoming races, adds the latest line-up as target rows. Builds leakage-free rolling form features (shift(1)) | `hist`, `is_target`, `TARGET_DONE`, `FORM_FEATS`, `erg`, `RND` |
| 5 | Practice + qualifying data (OpenF1) | Unlock gate. Only if qualifying (or sprint qualifying) is done: loads OpenF1 sessions, matches meetings by date, pulls practice and qualifying laps for the last `TRAIN_WEEKENDS` weekends, and builds weekend features | `UNLOCKED`, `SQ`, `sess`, `TARGET_MEETING`, `train_all`, `openf1()`, `weekend_features()`, `add_weekend()`, `session_done()` |
| 6 | Train + back-test the winner model | Logistic regression vs gradient boosting, tested on the last `TEST_RACES` weekends against a "pole sitter wins" baseline. Keeps the better one by race log-loss and prints which inputs matter most | `win_model`, `FEATS` |
| 7 | Sprint + Grand Prix winner prediction | Locked message with the unlock time, or prediction: model probabilities normalised per race, then 20,000 simulated finishing orders, flattened by rain. Win %, podium %, expected position, chart, actual winner for past races. Then the **driver prompt** | `PREDICTED_WINNER`, `GP_ACTUAL`, `DRIVER` |
| 8 | Clean laps | Green-flag, no in/out laps, within 107% of the fastest, dry compounds, lap 1 dropped. Fuel correction and track temperature via `merge_asof` | `clean` |
| 9 | Exploratory plot | Fuel-corrected lap time vs tyre age by compound | — |
| 10 | Feature engineering + pace models | Ridge with per-compound age and age² terms, track temperature and driver dummies, vs Random Forest (5-fold CV) | `pace_model`, `LAP_NOISE`, `make_features()` |
| 11 | Lap pace projections | Pace table per compound for `DRIVER`, kept non-decreasing with age (`np.maximum.accumulate`). Max stint = 1.1 × longest observed stint | `PACE`, `CUM`, `AVAILABLE`, `MAX_STINT`, `MAX_AGE` |
| 12 | Pit loss + race-risk settings | Pit loss from in-lap + out-lap minus 2 × the driver's median green lap. Safety-car and slow-stop settings | `PIT_LOSS`, `PIT_SD`, `P_SC`, ... |
| 13 | Strategy generator | Every 1- and 2-stop strategy with at least two dry compounds, min stint 5, within the max stint. Quick deterministic ranking, best pit laps per compound sequence | `det`, `best_per_seq`, `stint_time()`, `label()` |
| 14 | Monte Carlo engine (dry + wet) | Shared random scenarios across strategies: lap noise, safety cars, wear uncertainty, pit noise, slow stops, rain with wetness. Dry races run vectorised; wet races run lap by lap with reactive weather calls | `make_scenarios()`, `monte_carlo()`, `wet_race()`, `S`, `GRIP`, `TYPES` |
| 15 | Simulate top strategies | Top 6 compound sequences: mean gap, 95th-percentile time lost vs the best plan in each race, win probability. Box plot and bar chart | `top`, `sims`, `BEST` |
| 16 | Dry vs wet breakdown + replay | Separate tables for dry and wet simulated races, and a replay chart of one heavy-rain race showing the tyre used each lap | — |
| 17 | Pit windows | For each stop of `BEST`, moves that pit lap ±10 laps and takes the Monte Carlo mean. The window is every lap within `WINDOW_TOL` seconds of the best | — |
| 18 | Dry pit-wall call | `pit_wall_call(lap, compound, tyre_age, used, under_sc)` searches recursively for the best way to finish, up to 2 more stops | — |
| 19 | Wet crossover + rain call | Crossover chart and `rain_call(lap, tyre, wetness, under_sc)` | — |
| 20 | Real strategies (OpenF1) | Matches the OpenF1 race session by date, then loads stints, drivers and pit stops | `stints`, `SESSION_KEY` |
| 21 | Real vs simulator chart | Stint bars for each driver in finishing order, with the simulator's pick as a hatched "SIM" row | — |

## 4. Data sources

- **FastF1 (3.9.x when tested):** event schedule, race laps, weather, results. Cache at `/content/f1_cache`.
- **Ergast via Jolpica** (`fastf1.ergast.Ergast`, base URL `https://api.jolpi.ca/ergast/f1`): race results, race schedule, sprint results. Results are fetched per season with `limit=100` and paged with `get_next_result_page()`, which raises `ValueError` after the last page.
- **OpenF1** (`https://api.openf1.org/v1`): `sessions`, `laps`, `stints`, `drivers`, `pit`. Historical data is free with no key. The code throttles to about 3 requests per second, retries on 429, treats 404 as empty, and caches responses with `requests_cache` at `/content/openf1_cache` (`requests_cache` is a FastF1 dependency). Requests for the target weekend are not cached.
- **Open-Meteo:** geocoding (`geocoding-api.open-meteo.com/v1/search`) plus hourly `precipitation_probability` from the forecast API (16 days ahead). No key needed.

## 5. Key design decisions (and why)

- **Ridge, not Random Forest, for tyre pace.** Tree models go flat beyond the tyre ages they've seen, which would make long stints look free. Ridge with age and age² terms keeps rising, and `np.maximum.accumulate` stops pace from improving with age.
- **Two-stage strategy search.** A quick deterministic ranking of every strategy (cumulative sums), then Monte Carlo only on the best plan per compound sequence. This keeps it fast and gives a variety of distinct plans.
- **Common random numbers.** Every strategy faces the same simulated races, so the differences between them are low-noise and win probabilities are fair.
- **The wet engine is exactly the dry engine when there's no rain.** Checked: identical to within 1e-11 s. The wet engine does a weather stop only if `pace gain × min(laps left, LOOKAHEAD)` beats the pit cost (halved under a safety car).
- **Wetness model:** lap time = dry pace × (a + b × wetness). With the current numbers, slicks are best below about 0.21 wetness, inters from 0.21 to 0.5, and wets above 0.5.
- **Winner model features use only information from before the race** (rolling windows with shift(1)). An upcoming race is added as placeholder rows, so the same code handles past and upcoming races.
- **Same weekend pipeline for training and prediction.** Practice and qualifying features both come from OpenF1 laps, so what the model trains on matches what it sees at prediction time. Qualifying order is taken from best laps, not the official classification.
- **Winner probabilities are normalised per race** (they sum to 1). Finishing orders are then sampled by adding random noise to each driver's log-probability and sorting (the Plackett–Luce / Harville model). Rain flattens the odds by dividing the log-probabilities by `T = 1 + RAIN_CHAOS × P_RAIN`.
- **The gate:** a prediction unlocks when the session start plus 1.5 hours is before now (`event.get_session_date(name, utc=True)`). The sprint prediction uses the Grand Prix-trained model fed with sprint qualifying and FP1.

## 6. Things that need checking on real data

These couldn't be checked against the live APIs from the sandbox:

1. **OpenF1 field and session names:**
   - `laps`: `driver_number`, `lap_number`, `lap_duration`, `is_pit_out_lap`
   - `sessions`: `session_key`, `meeting_key`, `session_name`, `date_start`
   - `stints`: `compound`, `lap_start`, `lap_end`
   - `drivers`: `name_acronym`
   - `pit`: `pit_duration` or `lane_duration`
   - Session names: `Practice 1/2/3`, `Qualifying`, `Sprint Qualifying` (2024+) or `Sprint Shootout` (2023), `Race`
2. **OpenF1 rate limits and the empty-result response** (404 vs `[]`). Also, data during a live session may need a paid account.
3. **Car numbers must match between Ergast and OpenF1.** Ergast `number` is joined to OpenF1 `driver_number`.
4. **Meeting matching:** sessions within 4 days before to 1 day after the race date. Check this around pre-season testing.
5. **`race.total_laps`** may be `None`. The code falls back to the most laps completed.
6. **Open-Meteo geocoding** of FastF1 `Location` names (e.g. "Yas Island", "Spa-Francorchamps") may fail. It falls back to the country, then to `RAIN_DEFAULT`.
7. **Timing:** the first run of Cell 5 makes about 100 OpenF1 calls.
8. **Wet race with no dry race at the circuit in the last 3 seasons:** Cell 2 deliberately stops with an assert.

**Suggested real-data test runs:**
- 2024 Bahrain (R1, dry)
- 2024 São Paulo (wet)
- a 2025 sprint weekend
- an upcoming 2026 race, both before and after qualifying

## 7. How it was tested (mock harness)

The notebook source was run cell by cell with:
- **FastF1:** `get_session` and `get_event_schedule` monkeypatched. Synthetic laps came from a real `fastf1.core.Laps` object, and schedules were real `EventSchedule` objects with Session1–5 names and dates.
- **Ergast:** `Ergast._get` patched to return Jolpica-format JSON from a synthetic database, so FastF1's own parsing and paging were exercised.
- **OpenF1 and Open-Meteo:** `requests.get` and `requests_cache.CachedSession` patched.
- **`input()`:** patched with scripted answers.

Scenarios that passed:
- past dry race
- past wet race (dry-pace fallback)
- upcoming race before and after qualifying
- past sprint weekend (sprint and Grand Prix predicted, actual winners shown)
- a 2022 race (prediction off)
- an upcoming sprint weekend (both predictions locked)
- upcoming race at a new circuit (clean assert)

## 8. Next steps and ideas

- Run on real data (section 6) and fix whatever breaks.
- Update the copy open in Colab, or re-upload the `.ipynb`.
- A multi-car race simulation with traffic, undercut/overcut and track position.
- Weather calls that use the forecast, not just current conditions.
- Learn the `GRIP` numbers from real wet races.
- Use the official qualifying classification and grid penalties (OpenF1 `session_result` / `starting_grid`, if available).
- A sprint-specific model.
- Save caches to Google Drive so they survive Colab restarts.
- A dashboard front-end.

---

## 9. Notebook source

The notebook has a Markdown intro cell, then a `## N. Title` heading above each code cell, then the settings/limitations cell.

### Notebook intro cell

```markdown
# F1 Strategy Intelligence Suite: Strategy, Pit-Wall Simulation & Winner Prediction

Models optimal pit windows and tyre strategies using **Monte Carlo simulation** and **ML lap-pace projections**, and predicts **Sprint and Grand Prix winners** from practice, qualifying and driver form, for past and upcoming races, dry or wet.

**Stack:** Python, NumPy, Pandas, Scikit-learn, FastF1, Ergast (Jolpica), OpenF1 API, Open-Meteo (rain forecast)

**How to run**
1. Run Cell 1 and answer the two prompts: season, then race (round number or name).
2. Use **Runtime → Run cell and below**. Cell 7 asks which driver's pit strategy to simulate (press Enter for the suggested one).
3. Winner predictions unlock once qualifying is done (sprint qualifying for the sprint). Before that, Cell 7 shows when they unlock.
4. To try another race, run Cell 1 again and repeat.

**Pipeline:** race picker → load data → rain chance → driver form → practice + qualifying pace → winner model → winner prediction → clean laps → ML pace model → strategy search → Monte Carlo (dry + wet) → pit windows → pit-wall calls → compare with real strategies
```

### Cell 1 — Setup + race picker

```python
!pip install fastf1 -q

import os, time, itertools, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
import requests_cache
import fastf1
from fastf1.ergast import Ergast

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.metrics import mean_absolute_error, r2_score

warnings.filterwarnings('ignore')
os.makedirs('/content/f1_cache', exist_ok=True)
fastf1.Cache.enable_cache('/content/f1_cache')

FUEL_K = 0.06      # seconds gained per lap as fuel burns off (assumption)
N_SIMS = 2000      # Monte Carlo races per strategy
SEED   = 42
DRY    = ['SOFT', 'MEDIUM', 'HARD']
COLORS = {'SOFT': '#DA291C', 'MEDIUM': '#FFD12E', 'HARD': '#EBEBEB',
          'INTERMEDIATE': '#43B02A', 'WET': '#0067AD'}

# ---------------- RACE SELECTOR ----------------
NOW  = pd.Timestamp.now(tz='UTC').tz_localize(None)
YEAR = int(input('Which season? (e.g. 2024, 2025, 2026): '))

schedule = fastf1.get_event_schedule(YEAR, include_testing=False)
finished = schedule['Session5DateUtc'] + pd.Timedelta(hours=3) < NOW

show = schedule[['RoundNumber', 'EventName', 'Location']].copy()
show['Date']   = schedule['EventDate'].dt.strftime('%d %b')
show['Status'] = np.where(finished, 'done', 'UPCOMING')
print(f'\n{YEAR} calendar')
print(show.to_string(index=False))

pick  = input('\nRound number or GP name: ').strip()
event = schedule.get_event_by_round(int(pick)) if pick.isdigit() else schedule.get_event_by_name(pick)

race_utc = event['Session5DateUtc']
UPCOMING = race_utc + pd.Timedelta(hours=3) >= NOW

if UPCOMING:
    days = max((race_utc - NOW).days, 0)
    print(f"\n>>> UPCOMING RACE: {event['EventName']} {YEAR} on {race_utc:%d %b %Y} ({days} days to go)")
    print('    No race data exists yet, so I will project it from the last race held at',
          event['Location'])
    DATA_YEAR = None
    for y in range(YEAR - 1, YEAR - 4, -1):
        past  = fastf1.get_event_schedule(y, include_testing=False)
        match = past[(past['Location'].str.lower() == event['Location'].lower())
                     | (past['EventName'] == event['EventName'])]
        if len(match):
            DATA_YEAR, DATA_ROUND = y, int(match.iloc[-1]['RoundNumber'])
            break
    assert DATA_YEAR, 'No race at this circuit in the last 3 seasons. Pick another race.'
else:
    print(f"\n>>> COMPLETED RACE: {event['EventName']} {YEAR} ({race_utc:%d %b %Y})")
    DATA_YEAR, DATA_ROUND = YEAR, int(event['RoundNumber'])

RACE_TITLE = f"{event['EventName']} {YEAR}" + (f' (projected from {DATA_YEAR})' if UPCOMING else '')
print('Simulating:', RACE_TITLE)
```

### Cell 2 — Load race data

```python
def load_race(year, rnd):
    s = fastf1.get_session(year, rnd, 'R')
    s.load(laps=True, telemetry=False, weather=True, messages=False)
    return s

def lap_table(s):
    l = s.laps.copy()
    l['LapTimeS'] = l['LapTime'].dt.total_seconds()
    return l

def wet_share(l):
    return l['Compound'].isin(['INTERMEDIATE', 'WET']).mean()

race       = load_race(DATA_YEAR, DATA_ROUND)     # the real race: weather + real strategies
race_laps  = lap_table(race)
TOTAL_LAPS = int(race.total_laps or race_laps['LapNumber'].max())
WAS_WET    = bool(race.weather_data['Rainfall'].any()) or wet_share(race_laps) > 0

session, laps = race, race_laps                   # data used to learn DRY tyre pace
if wet_share(race_laps) > 0.4:
    print(f'{wet_share(race_laps):.0%} of laps were on wet tyres, looking for a dry race here to learn slick pace')
    for y in range(DATA_YEAR - 1, DATA_YEAR - 4, -1):
        past  = fastf1.get_event_schedule(y, include_testing=False)
        match = past[past['Location'].str.lower() == event['Location'].lower()]
        if len(match):
            s = load_race(y, int(match.iloc[-1]['RoundNumber']))
            if wet_share(lap_table(s)) < 0.4:
                session, laps = s, lap_table(s)
                print('   dry pace will come from the', y, 'race')
                break
    assert wet_share(laps) <= 0.4, 'No dry race here in the last 3 seasons to learn slick pace from.'

print(f"Race: {race.event['EventName']} {DATA_YEAR} | laps: {TOTAL_LAPS} | wet: {WAS_WET}")
print(race_laps['Compound'].value_counts())
```

### Cell 3 — Rain chance: forecast or what-if

```python
RAIN_DEFAULT = 0.15     # what-if rain chance when there is no forecast

def rain_forecast(place, start_utc, hours=2):
    geo = requests.get('https://geocoding-api.open-meteo.com/v1/search',
                       params={'name': place, 'count': 1}, timeout=20).json()
    lat, lon = geo['results'][0]['latitude'], geo['results'][0]['longitude']
    fc = requests.get('https://api.open-meteo.com/v1/forecast',
                      params={'latitude': lat, 'longitude': lon, 'forecast_days': 16,
                              'hourly': 'precipitation_probability'}, timeout=20).json()
    hourly = pd.DataFrame(fc['hourly'])
    hourly['time'] = pd.to_datetime(hourly['time'])
    window = hourly[(hourly['time'] >= start_utc.floor('h')) &
                    (hourly['time'] <= start_utc + pd.Timedelta(hours=hours))]
    p = window['precipitation_probability'].max()
    return None if pd.isna(p) else p / 100

if UPCOMING:
    P_RAIN = None
    for place in [event['Location'], event['Country']]:
        try:
            P_RAIN = rain_forecast(place, race_utc)
            break
        except Exception:
            pass
    if P_RAIN is None:
        P_RAIN = RAIN_DEFAULT
        print(f'No forecast yet (race more than 16 days away or lookup failed). Using {P_RAIN:.0%} rain chance.')
    else:
        print(f"Forecast: {P_RAIN:.0%} chance of rain during the race at {event['Location']}")
elif WAS_WET:
    P_RAIN = 1.0
    print('This race was WET in real life, so every simulated race gets rain.')
else:
    P_RAIN = RAIN_DEFAULT
    print(f'This race was dry. Simulating a {P_RAIN:.0%} what-if chance of rain.')
```

### Cell 4 — Race history + driver form (Ergast)

```python
erg = Ergast()
RND = int(event['RoundNumber'])

def season_results(year):
    frames, r = [], erg.get_race_results(season=year, limit=100)
    while True:
        for (_, race), df in zip(r.description.iterrows(), r.content):
            frames.append(df.assign(season=year, round=race['round'], circuitId=race['circuitId'],
                                    raceDate=race['raceDate']))
        try:
            r = r.get_next_result_page()
        except ValueError:
            break
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

cols = ['season', 'round', 'raceDate', 'circuitId', 'number', 'driverId', 'driverCode',
        'constructorId', 'constructorName', 'grid', 'position', 'positionText', 'points']
hist = pd.concat([season_results(y) for y in range(YEAR - 4, YEAR + 1)], ignore_index=True)[cols]
hist = hist[(hist['season'] < YEAR) | (hist['round'] <= RND)]

races_e = erg.get_race_schedule(season=YEAR)
target_info = races_e.loc[races_e['round'] == RND].iloc[0]

# upcoming race: use the line-up from the most recent race
TARGET_DONE = ((hist['season'] == YEAR) & (hist['round'] == RND)).any()
if not TARGET_DONE:
    last = hist[hist['season'] == hist['season'].max()]
    last = last[last['round'] == last['round'].max()]
    lineup = last[['number', 'driverId', 'driverCode', 'constructorId', 'constructorName']]
    hist = pd.concat([hist, lineup.assign(season=YEAR, round=RND, circuitId=target_info['circuitId'],
                                          raceDate=target_info['raceDate'])], ignore_index=True)

hist = hist.sort_values(['season', 'round']).reset_index(drop=True)
hist['race_id'] = hist['season'] * 100 + hist['round']
hist['grid']    = hist['grid'].replace(0, 20)            # 0 = pit-lane start
hist['win']     = (hist['position'] == 1).astype(float)
hist['dnf']     = np.where(hist['position'].isna(), np.nan,
                           (~hist['positionText'].astype(str).str.isdigit()).astype(float))

def past(col, by, n=None):
    if n:
        return hist.groupby(by)[col].transform(lambda s: s.shift(1).rolling(n, min_periods=1).mean())
    return hist.groupby(by)[col].transform(lambda s: s.shift(1).expanding().mean())

hist['form_finish'] = past('position', 'driverId', 5)               # avg finish, last 5 races
hist['form_grid']   = past('grid', 'driverId', 5)                   # avg grid slot
hist['form_points'] = past('points', 'driverId', 5)                 # avg points, last 5 races
hist['dnf_rate']    = past('dnf', 'driverId', 10)                   # reliability
hist['track_form']  = past('position', ['driverId', 'circuitId'])   # history at this circuit

team = hist.groupby(['race_id', 'constructorId'], as_index=False)['points'].sum()
team['team_form'] = team.groupby('constructorId')['points'].transform(
    lambda s: s.shift(1).rolling(5, min_periods=1).mean())          # car strength
hist = hist.merge(team[['race_id', 'constructorId', 'team_form']],
                  on=['race_id', 'constructorId'], how='left')

hist['cum_pts']   = hist.groupby(['season', 'driverId'])['points'].transform(
    lambda s: s.shift(1).fillna(0).cumsum())
hist['pts_share'] = (hist['cum_pts'] / hist.groupby('race_id')['cum_pts'].transform('max')).fillna(0)

hist = hist.fillna({'form_finish': 15, 'form_grid': 15, 'form_points': 0,
                    'dnf_rate': 0.15, 'team_form': 2})
hist['track_form'] = hist['track_form'].fillna(hist['form_finish'])

is_target  = hist['race_id'] == YEAR * 100 + RND
FORM_FEATS = ['form_finish', 'form_grid', 'form_points', 'dnf_rate', 'team_form', 'pts_share', 'track_form']
print(f"Form history: {hist['race_id'].nunique()} races")
print(hist.loc[is_target, ['driverCode', 'constructorName'] + FORM_FEATS]
      .sort_values('form_points', ascending=False).head(10).round(2).to_string(index=False))
```

### Cell 5 — Practice + qualifying data (OpenF1)

```python
BASE = 'https://api.openf1.org/v1'
http = requests_cache.CachedSession('/content/openf1_cache', allowable_codes=(200,))
TRAIN_WEEKENDS = 50                                   # past weekends used to train the winner model
QUALI_NAMES    = ['Qualifying']
SPRINT_QUALI   = ['Sprint Qualifying', 'Sprint Shootout']
WEEKEND_FEATS  = ['fp_gap', 'fp_lr_gap', 'q_gap', 'q_pos']

def openf1(endpoint, cached=True, **params):
    get = http.get if cached else requests.get
    for attempt in range(6):
        r = get(f'{BASE}/{endpoint}', params=params, timeout=30)
        if r.status_code == 429:                       # rate limited: wait and retry
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code == 404:
            return pd.DataFrame()
        r.raise_for_status()
        if not getattr(r, 'from_cache', False):
            time.sleep(0.35)
        return pd.DataFrame(r.json())
    raise RuntimeError('OpenF1 is rate-limiting. Wait a minute and rerun this cell.')

def session_pace(key, cached=True):
    l = openf1('laps', cached=cached, session_key=int(key))
    if l.empty:
        return pd.DataFrame()
    l = l.sort_values(['driver_number', 'lap_number'])
    best = l.groupby('driver_number')['lap_duration'].min()
    pit_out = l['is_pit_out_lap'].fillna(False).astype(bool)
    l['ok']  = (l['lap_duration'] < 1.10 * l['driver_number'].map(best)) & ~pit_out
    l['run'] = (~l['ok']).groupby(l['driver_number']).cumsum()
    runs = l[l['ok']].groupby(['driver_number', 'run'])['lap_duration'].agg(['median', 'size'])
    long_run = runs[runs['size'] >= 5].groupby('driver_number')['median'].min()   # 5+ lap runs
    return pd.DataFrame({'gap': best / best.min() - 1,
                         'lr_gap': long_run / long_run.min() - 1,
                         'pos': best.rank(method='first')})

def weekend_features(meeting, quali_names, cached=True):
    s = sess[sess['meeting_key'] == meeting]
    fp = next((s.loc[s['session_name'] == n, 'session_key'].iloc[0]
               for n in ['Practice 2', 'Practice 1', 'Practice 3'] if (s['session_name'] == n).any()), None)
    q = s.loc[s['session_name'].isin(quali_names), 'session_key']
    if fp is None or q.empty:
        return pd.DataFrame()
    fpp, qp = session_pace(fp, cached), session_pace(q.iloc[0], cached)
    if fpp.empty or qp.empty:
        return pd.DataFrame()
    return pd.DataFrame({'fp_gap': fpp['gap'], 'fp_lr_gap': fpp['lr_gap'],
                         'q_gap': qp['gap'], 'q_pos': qp['pos']}).rename_axis('number').reset_index()

def add_weekend(rows, wk):
    d = rows.merge(wk, on='number', how='inner')
    d['fp_gap']    = d['fp_gap'].fillna(d['fp_gap'].max())
    d['fp_lr_gap'] = d['fp_lr_gap'].fillna(d['fp_gap'])
    d['q_gap']     = d['q_gap'].fillna(d['q_gap'].max())
    d['q_pos']     = d['q_pos'].fillna(len(d))
    return d

def meeting_for(race_date):
    d = sess['day'] - pd.Timestamp(race_date).normalize()
    near = sess[(d >= pd.Timedelta(days=-4)) & (d <= pd.Timedelta(days=1))]
    return near['meeting_key'].mode().iloc[0] if len(near) else None

def session_done(name):
    try:
        return event.get_session_date(name, utc=True) + pd.Timedelta(hours=1.5) < NOW
    except Exception:
        return False

names    = [event[f'Session{i}'] for i in range(1, 6)]
SQ       = next((n for n in names if n in SPRINT_QUALI), None)    # sprint weekend?
UNLOCKED = YEAR >= 2023 and (session_done('Qualifying') or (SQ is not None and session_done(SQ)))

if YEAR < 2023:
    print('OpenF1 practice and qualifying data starts in 2023, so winner prediction is off for this race.')
elif not UNLOCKED:
    print('Qualifying has not happened yet, so the winner prediction is locked (see the next cells).')
else:
    sess = pd.concat([openf1('sessions', cached=(y < YEAR), year=y)
                      for y in range(max(2023, YEAR - 3), YEAR + 1)], ignore_index=True)
    sess['day'] = pd.to_datetime(sess['date_start'], utc=True).dt.tz_convert(None).dt.normalize()
    TARGET_MEETING = meeting_for(hist.loc[is_target, 'raceDate'].iloc[0])

    train_ids = hist.loc[~is_target & hist['position'].notna() & (hist['season'] >= 2023), 'race_id'].unique()
    train_ids = np.sort(train_ids)[-TRAIN_WEEKENDS:]
    parts = []
    print(f'Loading practice + qualifying laps for {len(train_ids)} past weekends (cached after the first run)...')
    for n, rid in enumerate(train_ids, 1):
        rows = hist[hist['race_id'] == rid]
        m = meeting_for(rows['raceDate'].iloc[0])
        wk = weekend_features(m, QUALI_NAMES) if m is not None else pd.DataFrame()
        if len(wk):
            parts.append(add_weekend(rows, wk))
        if n % 10 == 0:
            print(f'   {n}/{len(train_ids)} weekends')
    train_all = pd.concat(parts, ignore_index=True)
    print(f"Training set: {train_all['race_id'].nunique()} weekends, {len(train_all)} driver entries")
```

### Cell 6 — Train + back-test the winner model

```python
TEST_RACES = 12      # most recent weekends held back to test the model
FEATS = FORM_FEATS + WEEKEND_FEATS

def race_probs(model, df):
    p = pd.Series(model.predict_proba(df[FEATS])[:, 1], index=df.index)
    return p / p.groupby(df['race_id']).transform('sum')       # each race sums to 1

def score(p, df):
    d = df.assign(p=p, rank=p.groupby(df['race_id']).rank(ascending=False))
    w = d[d['win'] == 1]
    return {'top_pick_won':   (w['rank'] == 1).mean(),
            'winner_in_top3': (w['rank'] <= 3).mean(),
            'avg_p_winner':   w['p'].mean(),
            'race_logloss':   -np.log(w['p'].clip(1e-6)).mean()}

def train_winner_model():
    cut = np.sort(train_all['race_id'].unique())[-TEST_RACES]
    tr, te = train_all[train_all['race_id'] < cut], train_all[train_all['race_id'] >= cut]
    cands = {
        'LogisticRegression': make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=1000)),
        'GradientBoosting':   GradientBoostingClassifier(n_estimators=150, max_depth=2,
                                                         learning_rate=0.05, random_state=SEED),
    }
    results = {}
    for name, m in cands.items():
        m.fit(tr[FEATS], tr['win'])
        results[name] = score(race_probs(m, te), te)
    q_rank = (-te['q_pos']).groupby(te['race_id']).rank(ascending=False, method='first')
    won = te['win'] == 1
    results['Baseline: pole sitter'] = {'top_pick_won': (q_rank[won] == 1).mean(),
                                        'winner_in_top3': (q_rank[won] <= 3).mean()}
    print(f'Back-test on the last {TEST_RACES} weekends:')
    print(pd.DataFrame(results).T.round(3).to_string())

    best = min(cands, key=lambda n: results[n]['race_logloss'])
    model = cands[best].fit(train_all[FEATS], train_all['win'])
    est = model[-1] if hasattr(model, 'steps') else model
    imp = est.coef_[0] if hasattr(est, 'coef_') else est.feature_importances_
    print(f'\nUsing {best}. What drives the prediction:')
    print(pd.Series(imp, index=FEATS).sort_values(key=abs, ascending=False).round(3).to_string())
    return model

win_model = train_winner_model() if UNLOCKED else None
```

### Cell 7 — Sprint + Grand Prix winner prediction

```python
RAIN_CHAOS = 0.6     # how much rain flattens the odds (assumption)

def predict(quali_names, label, actual=None):
    wk = weekend_features(TARGET_MEETING, quali_names, cached=TARGET_DONE) if TARGET_MEETING else pd.DataFrame()
    if wk.empty:
        print(f'{label}: practice/qualifying laps are not on OpenF1 yet. Rerun this cell a bit later.\n')
        return None
    tgt = add_weekend(hist[is_target], wk)
    tgt['p'] = race_probs(win_model, tgt)

    T = 1 + RAIN_CHAOS * P_RAIN                                  # rain = less predictable
    rng = np.random.default_rng(SEED)
    scores = np.log(tgt['p'].clip(1e-9).values) / T + rng.gumbel(size=(20000, len(tgt)))
    pos = (-scores).argsort(axis=1).argsort(axis=1)              # 0 = winner
    tgt['win_%']    = (pos == 0).mean(axis=0) * 100
    tgt['podium_%'] = (pos < 3).mean(axis=0) * 100
    tgt['exp_pos']  = pos.mean(axis=0) + 1

    pred = tgt.sort_values('win_%', ascending=False)
    print(f"{label} - {event['EventName']} {YEAR} | rain chance {P_RAIN:.0%}")
    print(pred[['driverCode', 'constructorName', 'q_pos', 'win_%', 'podium_%', 'exp_pos']]
          .head(10).round(1).to_string(index=False))
    winner = pred.iloc[0]
    print(f"PREDICTED {label} WINNER: {winner['driverCode']} ({winner['constructorName']}) - "
          f"{winner['win_%']:.0f}% win, {winner['podium_%']:.0f}% podium")
    if actual:
        rank = list(pred['driverCode']).index(actual) + 1 if actual in list(pred['driverCode']) else '-'
        print(f'ACTUAL {label} WINNER:    {actual} (the model ranked them #{rank})')

    top10 = pred.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(top10['driverCode'], top10['podium_%'], color='lightgrey', label='Podium %')
    ax.barh(top10['driverCode'], top10['win_%'], color='tab:red', label='Win %')
    ax.set(xlabel='Probability (%)', title=f"{label} winner prediction - {event['EventName']} {YEAR}")
    ax.legend()
    plt.show()
    return winner['driverCode']

def locked(name, label):
    when = event.get_session_date(name, utc=True)
    print(f'{label} winner prediction unlocks after {name} ({when:%a %d %b, %H:%M} UTC). '
          f'Rerun cells 5-7 then.\n')

GP_ACTUAL = hist.loc[is_target & (hist['win'] == 1), 'driverCode']
GP_ACTUAL = GP_ACTUAL.iloc[0] if len(GP_ACTUAL) else None
PREDICTED_WINNER = None

if YEAR >= 2023 and SQ:
    if session_done(SQ):
        sr = erg.get_sprint_results(season=YEAR, round=RND) if TARGET_DONE else None
        s_actual = sr.content[0].sort_values('position')['driverCode'].iloc[0] if sr is not None and len(sr.content) else None
        predict(SPRINT_QUALI, 'SPRINT', s_actual)
    else:
        locked(SQ, 'SPRINT')
if YEAR >= 2023:
    if session_done('Qualifying'):
        PREDICTED_WINNER = predict(QUALI_NAMES, 'GRAND PRIX', GP_ACTUAL)
    else:
        locked('Qualifying', 'GRAND PRIX')

# which driver's pit strategy to simulate
if GP_ACTUAL:
    default, why = GP_ACTUAL, 'actual winner'
elif PREDICTED_WINNER:
    default, why = PREDICTED_WINNER, 'predicted winner'
else:
    default = hist[is_target].sort_values('form_points', ascending=False)['driverCode'].iloc[0]
    why = 'best current form'
DRIVER = input(f'\nDriver to build the pit strategy for (press Enter for {default}, {why}): ').strip().upper() or default
if DRIVER not in set(laps['Driver']):
    alt = session.results.iloc[0]['Abbreviation']
    print(f'{DRIVER} has no laps in the {session.date.year} race used for tyre pace, so I am using {alt} instead')
    DRIVER = alt
print('Strategy driver:', DRIVER)
```

### Cell 8 — Clean laps, fuel correction, track temperature

```python
clean = laps.pick_wo_box().pick_track_status('1').pick_quicklaps(1.07)
clean = pd.DataFrame(clean)
clean = clean[(clean['LapNumber'] > 1) & clean['Compound'].isin(DRY)]
clean = clean.dropna(subset=['LapTimeS', 'TyreLife', 'LapStartTime'])

# remove the effect of fuel weight so only tyre wear is left
clean['FuelCorrS'] = clean['LapTimeS'] - FUEL_K * (TOTAL_LAPS - clean['LapNumber'])

# attach track temperature at the start of each lap
weather = session.weather_data[['Time', 'TrackTemp']].sort_values('Time')
clean = pd.merge_asof(clean.sort_values('LapStartTime'), weather,
                      left_on='LapStartTime', right_on='Time',
                      direction='backward', suffixes=('', '_w'))
clean['TrackTemp'] = clean['TrackTemp'].fillna(weather['TrackTemp'].median())

print(len(clean), 'clean green-flag laps')
print(clean['Compound'].value_counts())
```

### Cell 9 — Exploratory plot: tyre degradation

```python
fig, ax = plt.subplots(figsize=(10, 5))
for c in DRY:
    d = clean[clean['Compound'] == c]
    ax.scatter(d['TyreLife'], d['FuelCorrS'], s=10, alpha=0.4,
               color=COLORS[c], edgecolors='k', linewidths=0.2, label=c)
ax.set(xlabel='Tyre age (laps)', ylabel='Fuel-corrected lap time (s)',
       title=f'Tyre degradation by compound - {session.event["EventName"]} {session.date.year}')
ax.legend()
plt.show()
```

### Cell 10 — Feature engineering + ML models

```python
COMPOUNDS = sorted(clean['Compound'].unique())

def make_features(df, columns=None):
    X = pd.DataFrame(index=df.index)
    for c in COMPOUNDS:
        is_c = (df['Compound'] == c).astype(float)
        X[f'is_{c}']   = is_c
        X[f'age_{c}']  = is_c * df['TyreLife']
        X[f'age2_{c}'] = is_c * df['TyreLife'] ** 2
    X['TrackTemp'] = df['TrackTemp']
    X = pd.concat([X, pd.get_dummies(df['Driver'], prefix='drv', dtype=float)], axis=1)
    if columns is not None:
        X = X.reindex(columns=columns, fill_value=0.0)
    return X

X = make_features(clean)
y = clean['FuelCorrS']
FEATURES = X.columns

models = {
    'Ridge':        make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
    'RandomForest': RandomForestRegressor(n_estimators=300, min_samples_leaf=5,
                                          random_state=SEED, n_jobs=-1),
}
cv = KFold(n_splits=5, shuffle=True, random_state=SEED)
cv_pred = {}
for name, m in models.items():
    cv_pred[name] = cross_val_predict(m, X, y, cv=cv)
    print(f'{name:13s} MAE = {mean_absolute_error(y, cv_pred[name]):.3f} s'
          f'   R2 = {r2_score(y, cv_pred[name]):.3f}')

pace_model = models['Ridge'].fit(X, y)
LAP_NOISE  = np.std(y - cv_pred['Ridge'])
print(f'Lap-to-lap noise: {LAP_NOISE:.2f} s')
```

### Cell 11 — Lap pace projections per compound

```python
MAX_AGE    = TOTAL_LAPS + 5
TRACK_TEMP = clean['TrackTemp'].median()
counts     = clean['Compound'].value_counts()
AVAILABLE  = [c for c in COMPOUNDS if counts[c] >= 30]
MAX_STINT  = {c: min(int(clean.loc[clean['Compound'] == c, 'TyreLife'].max() * 1.1), TOTAL_LAPS)
              for c in AVAILABLE}

ages = np.arange(1, MAX_AGE + 1)
PACE = {}
for c in AVAILABLE:
    grid = pd.DataFrame({'Driver': DRIVER, 'Compound': c,
                         'TyreLife': ages, 'TrackTemp': TRACK_TEMP})
    PACE[c] = np.maximum.accumulate(pace_model.predict(make_features(grid, FEATURES)))

CUM = {c: np.concatenate([[0.0], np.cumsum(PACE[c])]) for c in PACE}

deg_table = pd.DataFrame({
    'fresh_pace_s':  {c: PACE[c][0] for c in AVAILABLE},
    'deg_s_per_lap': {c: (PACE[c][MAX_STINT[c] - 1] - PACE[c][0]) / (MAX_STINT[c] - 1) for c in AVAILABLE},
    'max_stint':     MAX_STINT,
}).round(3)
print(deg_table)

fig, ax = plt.subplots(figsize=(10, 5))
for c in AVAILABLE:
    d = clean[clean['Compound'] == c]
    ax.scatter(d['TyreLife'], d['FuelCorrS'], s=8, alpha=0.25,
               color=COLORS[c], edgecolors='k', linewidths=0.2)
    ax.plot(ages[:MAX_STINT[c]], PACE[c][:MAX_STINT[c]], color=COLORS[c], lw=3,
            label=f'{c} (model)')
ax.set(xlabel='Tyre age (laps)', ylabel='Fuel-corrected lap time (s)',
       title=f'Projected lap pace for {DRIVER} - {RACE_TITLE}')
ax.legend()
plt.show()
```

### Cell 12 — Pit-loss estimate + race-risk settings

```python
def estimate_pit_loss(laps):
    losses = []
    for drv, d in laps.groupby('Driver'):
        d = d.set_index('LapNumber')
        green = d[(d['TrackStatus'] == '1') & d['PitInTime'].isna() & d['PitOutTime'].isna()]
        ref = green['LapTimeS'].median()
        for lap in d.index[d['PitInTime'].notna()]:
            if lap + 1 in d.index and pd.notna(d.loc[lap + 1, 'PitOutTime']):
                pair = d.loc[[lap, lap + 1]]
                if (pair['TrackStatus'] == '1').all():
                    losses.append(pair['LapTimeS'].sum() - 2 * ref)
    losses = pd.Series(losses, dtype=float)
    losses = losses[(losses > 10) & (losses < 40)]
    if len(losses) < 3:
        return 22.0, 1.0
    return losses.median(), min(losses.std(), 2.0)

PIT_LOSS, PIT_SD = estimate_pit_loss(laps)

P_SC          = 0.5    # chance of at least one safety car in the race
SC_LAPS       = 4      # laps each safety car lasts
SC_LAP_TIME   = 1.4 * clean['LapTimeS'].median()
SC_PIT_FACTOR = 0.5    # a stop under SC costs about half
P_SLOW_STOP   = 0.05
SLOW_STOP_S   = 3.0
DEG_UNCERT    = 0.15   # +/-15% uncertainty in tyre wear

print(f'Pit loss: {PIT_LOSS:.1f} s  (sd {PIT_SD:.1f} s)')
```

### Cell 13 — Generate and rank every legal strategy

```python
def generate_strategies(min_stint=5, max_stops=2):
    out = []
    for stops in range(1, max_stops + 1):
        for comps in itertools.product(AVAILABLE, repeat=stops + 1):
            if len(set(comps)) < 2:          # rule: two different dry compounds
                continue
            for pits in itertools.combinations(range(min_stint, TOTAL_LAPS - min_stint + 1), stops):
                lengths = np.diff([0, *pits, TOTAL_LAPS])
                if lengths.min() < min_stint:
                    continue
                if any(n > MAX_STINT[c] for c, n in zip(comps, lengths)):
                    continue
                out.append(list(zip(comps, lengths)))
    return out

def stint_time(c, n, start_age=0):
    return CUM[c][start_age + n] - CUM[c][start_age]

def race_time(strategy):
    return sum(stint_time(c, n) for c, n in strategy) + PIT_LOSS * (len(strategy) - 1)

def label(strategy):
    pits = np.cumsum([n for _, n in strategy])[:-1]
    return '-'.join(c[0] for c, _ in strategy) + ' | box L' + ', L'.join(map(str, pits))

strategies = generate_strategies()
det = pd.DataFrame({'strategy': strategies})
det['time']  = det['strategy'].apply(race_time)
det['seq']   = det['strategy'].apply(lambda s: '-'.join(c[0] for c, _ in s))
det['label'] = det['strategy'].apply(label)

best_per_seq = det.loc[det.groupby('seq')['time'].idxmin()].sort_values('time')
best_per_seq['gap_s'] = best_per_seq['time'] - best_per_seq['time'].min()

print(f'{len(det):,} strategies evaluated')
print(best_per_seq[['label', 'gap_s']].head(10).round(2).to_string(index=False))
```

### Cell 14 — Monte Carlo engine (dry + wet)

```python
FUEL = FUEL_K * (TOTAL_LAPS - np.arange(1, TOTAL_LAPS + 1))

# wet-weather assumptions: lap time = dry pace x (a + b * wetness)
TYPES       = ['SLICK', 'INTERMEDIATE', 'WET']
GRIP        = {'SLICK': (1.00, 0.45), 'INTERMEDIATE': (1.06, 0.16), 'WET': (1.12, 0.04)}
DRYING_LAPS = 8      # laps for the track to dry once the rain stops
LOOKAHEAD   = 5      # laps ahead the team considers when making a weather call
DRY_REF     = min(PACE[c][0] for c in AVAILABLE)

def kind(tyre):
    return 0 if tyre in DRY else TYPES.index(tyre)

def mult(k, w):
    a, b = GRIP[TYPES[k]]
    return a + b * w

def best_slick(R):
    ok = [c for c in AVAILABLE if MAX_STINT[c] >= R]
    return min(ok, key=lambda c: stint_time(c, R)) if ok else max(AVAILABLE, key=MAX_STINT.get)

def make_scenarios(n=N_SIMS, seed=SEED):
    rng = np.random.default_rng(seed)
    t = np.arange(TOTAL_LAPS)[None, :]

    rain  = rng.random(n) < P_RAIN
    onset = rng.integers(1, TOTAL_LAPS - 5, n)[:, None]
    dur   = rng.integers(5, 25, n)[:, None]
    peak  = rng.uniform(0.15, 1.0, n)[:, None]
    rise  = np.clip((t - onset + 1) / 2, 0, 1)
    dry   = np.clip(1 - (t - onset - dur) / DRYING_LAPS, 0, 1)
    wet   = peak * np.minimum(rise, dry) * rain[:, None]

    hazard = 1 - (1 - P_SC) ** (1 / TOTAL_LAPS)
    start = rng.random((n, TOTAL_LAPS)) < hazard * (1 + 5 * wet)   # rain = more safety cars
    sc = np.zeros_like(start)
    for k in range(SC_LAPS):
        sc[:, k:] |= start[:, :TOTAL_LAPS - k]

    M = np.stack([mult(k, wet) for k in range(3)])
    return {
        'rain': rain, 'wet': wet, 'mult': M, 'best': M.argmin(axis=0), 'sc': sc,
        'noise':     rng.normal(0, LAP_NOISE, (n, TOTAL_LAPS)),
        'deg_mult':  rng.normal(1, DEG_UNCERT, n).clip(0.5, 1.5),
        'pit_noise': rng.normal(0, PIT_SD, (n, TOTAL_LAPS)),
        'slow_stop': rng.random((n, TOTAL_LAPS)) < P_SLOW_STOP,
    }

def lap_profile(strategy):
    base, deg = [], []
    for c, n in strategy:
        p = PACE[c][:n]
        base.append(np.full(n, p[0]))
        deg.append(p - p[0])
    pit_laps = np.cumsum([n for _, n in strategy])[:-1] - 1
    return np.concatenate(base), np.concatenate(deg), pit_laps

def dry_races(strategy, S, idx):
    base, deg, pit_laps = lap_profile(strategy)
    sc = S['sc'][idx]
    lap_t = base + FUEL + deg * S['deg_mult'][idx][:, None] + S['noise'][idx]
    lap_t = np.where(sc, SC_LAP_TIME, lap_t)
    total = lap_t.sum(axis=1)
    for p in pit_laps:
        loss = PIT_LOSS + S['pit_noise'][idx, p] + SLOW_STOP_S * S['slow_stop'][idx, p]
        total += np.where(sc[:, p], loss * SC_PIT_FACTOR, loss)
    return total

def wet_race(strategy, S, i, trace=None):
    plan = [c for c, _ in strategy]
    pits = {int(p) for p in np.cumsum([n for _, n in strategy])[:-1]}
    tyre, age, stint, on_plan, total = plan[0], 0, 0, True, 0.0
    M, best = S['mult'][:, i], S['best'][i]

    for t in range(TOTAL_LAPS):
        lap, k, sc = t + 1, kind(tyre), S['sc'][i, t]
        dry_lap = DRY_REF + FUEL[t]
        if tyre in DRY:
            p = PACE[tyre]
            dry_lap = p[0] + (p[age] - p[0]) * S['deg_mult'][i] + FUEL[t]
        total += SC_LAP_TIME if sc else dry_lap * M[k, t] + S['noise'][i, t]
        if trace is not None:
            trace.append(tyre)
        age += 1
        left = TOTAL_LAPS - lap
        if left == 0:
            break

        factor = SC_PIT_FACTOR if sc else 1.0
        b = best[t]
        gain = (DRY_REF + FUEL[t]) * (M[k, t] - M[b, t]) * min(left, LOOKAHEAD)
        new = None
        if k != b and gain > PIT_LOSS * factor:                         # weather call
            new = best_slick(left) if b == 0 else TYPES[b]
            on_plan = False
        elif on_plan and lap in pits:                                   # planned dry stop
            stint += 1
            new = plan[stint]
        elif tyre in DRY and not on_plan and age >= MAX_STINT[tyre]:    # slicks worn out
            new = best_slick(left)

        if new:
            total += (PIT_LOSS + S['pit_noise'][i, t] + SLOW_STOP_S * S['slow_stop'][i, t]) * factor
            tyre, age = new, 0
    return total

def monte_carlo(strategy, S):
    total = np.empty(len(S['rain']))
    dry = ~S['rain']
    total[dry] = dry_races(strategy, S, dry)
    for i in np.flatnonzero(S['rain']):
        total[i] = wet_race(strategy, S, i)
    return total

S = make_scenarios()
print(f"Simulated races with rain: {S['rain'].mean():.0%} | with a safety car: {S['sc'].any(axis=1).mean():.0%}")
```

### Cell 15 — Simulate the top strategies

```python
top  = best_per_seq.head(6).reset_index(drop=True)
sims = np.vstack([monte_carlo(s, S) for s in top['strategy']])

order = np.argsort(sims.mean(axis=1))
top, sims = top.iloc[order].reset_index(drop=True), sims[order]

regret = sims - sims.min(axis=0)
win = np.bincount(sims.argmin(axis=0), minlength=len(top)) / N_SIMS

mc = pd.DataFrame({
    'strategy':     top['label'],
    'mean_gap_s':   sims.mean(axis=1) - sims.mean(axis=1).min(),
    'regret_p95_s': np.percentile(regret, 95, axis=1),
    'win_prob':     win,
}).round(2)
print(mc.to_string(index=False))

BEST = top.loc[0, 'strategy']
print(f"\nRECOMMENDED for {DRIVER} at {RACE_TITLE}: {top.loc[0, 'label']}")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].boxplot(regret.T, showfliers=False)
axes[0].set_xticks(range(1, len(top) + 1), top['label'], rotation=30, ha='right')
axes[0].set(ylabel='Time lost vs best plan in that race (s)', title='Strategy risk')
axes[1].barh(top['label'][::-1], win[::-1], color='tab:red')
axes[1].set(xlabel='Win probability', title=f'P(fastest) over {N_SIMS} simulated races')
plt.tight_layout()
plt.show()
```

### Cell 16 — Dry vs wet breakdown + wet race replay

```python
rain = S['rain']
for name, mask in [('DRY races', ~rain), ('WET races', rain)]:
    if mask.sum() == 0:
        continue
    part = sims[:, mask]
    print(f'\n{name}: {mask.sum()} simulations')
    print(pd.DataFrame({
        'strategy':   top['label'],
        'mean_gap_s': part.mean(axis=1) - part.mean(axis=1).min(),
        'win_prob':   np.bincount(part.argmin(axis=0), minlength=len(top)) / mask.sum(),
    }).round(2).to_string(index=False))

heavy = np.flatnonzero(rain & (S['wet'].max(axis=1) > 0.5))
if len(heavy):
    i, trace = heavy[0], []
    wet_race(BEST, S, i, trace)
    fig, ax = plt.subplots(figsize=(12, 3.5))
    ax.plot(np.arange(TOTAL_LAPS) + 0.5, S['wet'][i], color='tab:blue', lw=2, label='Track wetness')
    for lap, tyre in enumerate(trace, 1):
        ax.axvspan(lap - 1, lap, ymax=0.1, color=COLORS[tyre])
    ax.set(xlabel='Lap', ylabel='Wetness', ylim=(0, 1.05),
           title=f'One simulated wet race: tyre used each lap (bottom strip) - {RACE_TITLE}')
    ax.legend()
    plt.show()
```

### Cell 17 — Optimal pit windows

```python
WINDOW_TOL = 1.0   # laps within 1 s of the best = pit window

def with_pits(comps, pits):
    return list(zip(comps, np.diff([0, *pits, TOTAL_LAPS])))

def feasible(strategy, min_stint=5):
    return all(min_stint <= n <= MAX_STINT[c] for c, n in strategy)

comps     = [c for c, _ in BEST]
best_pits = list(np.cumsum([n for _, n in BEST])[:-1])

fig, ax = plt.subplots(figsize=(10, 5))
for i, p0 in enumerate(best_pits):
    xs, ys = [], []
    for p in range(p0 - 10, p0 + 11):
        trial = best_pits.copy()
        trial[i] = p
        s = with_pits(comps, trial)
        if feasible(s):
            xs.append(p)
            ys.append(monte_carlo(s, S).mean())
    xs, ys = np.array(xs), np.array(ys) - min(ys)
    window = xs[ys <= WINDOW_TOL]
    line, = ax.plot(xs, ys, marker='o', label=f'Stop {i + 1}')
    ax.axvspan(window.min(), window.max(), color=line.get_color(), alpha=0.15)
    print(f'Stop {i + 1}: ideal lap {xs[ys.argmin()]} | window L{window.min()}-L{window.max()}')

ax.set(xlabel='Pit lap', ylabel='Expected time lost (s)',
       title=f"Pit windows: {top.loc[0, 'label']} - {RACE_TITLE}")
ax.legend()
plt.show()
```

### Cell 18 — Pit-wall call (dry): box now or stay out?

```python
def finish(R, c, age, used, stops):
    best = (np.inf, [])
    if len(used) >= 2 and age + R <= MAX_STINT[c]:
        best = (stint_time(c, R, age), [(c, R)])
    if stops > 0:
        for k in range(1, R):
            if age + k > MAX_STINT[c]:
                break
            for new in AVAILABLE:
                t, plan = finish(R - k, new, 0, used | {new}, stops - 1)
                t += stint_time(c, k, age) + PIT_LOSS
                if t < best[0]:
                    best = (t, [(c, k)] + plan)
    return best

def describe(plan, lap):
    out = []
    for c, n in plan:
        lap += n
        out.append(f'{c[0]} to L{lap}')
    return ', '.join(out)

def pit_wall_call(lap, compound, tyre_age, used=(), under_sc=False, max_stops=2):
    assert compound in AVAILABLE, f'No pace model for {compound}'
    used = set(used) | {compound}
    R = TOTAL_LAPS - lap
    box_cost = PIT_LOSS * (SC_PIT_FACTOR if under_sc else 1.0)

    box = (np.inf, [])
    for new in AVAILABLE:
        t, plan = finish(R, new, 0, used | {new}, max_stops - 1)
        if t + box_cost < box[0]:
            box = (t + box_cost, plan)
    stay = finish(R, compound, tyre_age, used, max_stops)

    best = min(box[0], stay[0])
    print(f"Lap {lap}/{TOTAL_LAPS} | {compound} age {tyre_age} | {'SAFETY CAR' if under_sc else 'green flag'}")
    print(f'   BOX NOW : {describe(box[1], lap):32s} {box[0] - best:+6.1f} s')
    print(f'   STAY OUT: {describe(stay[1], lap):32s} {stay[0] - best:+6.1f} s')
    print('   >>> CALL:', 'BOX BOX BOX' if box[0] <= stay[0] else 'STAY OUT', '\n')

first = BEST[0][0]
pit_wall_call(lap=15, compound=first, tyre_age=14)
pit_wall_call(lap=15, compound=first, tyre_age=14, under_sc=True)
pit_wall_call(lap=8,  compound=first, tyre_age=7,  under_sc=True)
```

### Cell 19 — Wet crossover chart + rain pit-wall call

```python
w = np.linspace(0, 1, 101)
fig, ax = plt.subplots(figsize=(9, 4))
for k, col in enumerate(['#DA291C', COLORS['INTERMEDIATE'], COLORS['WET']]):
    ax.plot(w, (mult(k, w) - 1) * 100, lw=3, color=col, label=TYPES[k])
ax.set(xlabel='Track wetness (0 = dry, 1 = soaked)', ylabel='% slower than dry pace',
       title='Tyre crossover points')
ax.legend()
plt.show()

def rain_call(lap, tyre, wetness, under_sc=False):
    left = TOTAL_LAPS - lap
    ref  = DRY_REF + FUEL[lap - 1]
    pace = [ref * mult(k, wetness) for k in range(3)]
    k, b = kind(tyre), int(np.argmin(pace))
    cost = PIT_LOSS * (SC_PIT_FACTOR if under_sc else 1.0)
    gain = (pace[k] - pace[b]) * min(left, LOOKAHEAD)
    print(f"Lap {lap}/{TOTAL_LAPS} | on {tyre} | wetness {wetness:.2f} | {'SAFETY CAR' if under_sc else 'racing'}")
    for j in range(3):
        print(f'   {TYPES[j]:13s} {pace[j]:7.2f} s/lap')
    if b != k and gain > cost:
        new = best_slick(left) if b == 0 else TYPES[b]
        print(f'   >>> CALL: BOX BOX BOX for {new}  (gain {gain:.1f} s > pit cost {cost:.1f} s)\n')
    else:
        print(f'   >>> CALL: STAY OUT  (gain {gain:.1f} s vs pit cost {cost:.1f} s)\n')

rain_call(lap=20, tyre='MEDIUM', wetness=0.15)
rain_call(lap=20, tyre='MEDIUM', wetness=0.45)
rain_call(lap=30, tyre='INTERMEDIATE', wetness=0.85)
rain_call(lap=45, tyre='INTERMEDIATE', wetness=0.0)
```

### Cell 20 — Real strategies from the OpenF1 API

```python
races = openf1('sessions', cached=False, year=DATA_YEAR, session_name='Race')
races['date_start'] = pd.to_datetime(races['date_start'], utc=True)
target = pd.Timestamp(race.date)
target = target.tz_localize('UTC') if target.tzinfo is None else target.tz_convert('UTC')
SESSION_KEY = races.loc[(races['date_start'] - target).abs().idxmin(), 'session_key']

stints  = openf1('stints',  session_key=SESSION_KEY)
drivers = openf1('drivers', session_key=SESSION_KEY)
pit_df  = openf1('pit',     session_key=SESSION_KEY)

drivers = drivers[['driver_number', 'name_acronym']].drop_duplicates('driver_number')
stints  = stints.merge(drivers, on='driver_number')
stints['lap_end'] = stints['lap_end'].fillna(TOTAL_LAPS)

lane = pit_df.filter(['pit_duration', 'lane_duration']).apply(pd.to_numeric, errors='coerce').max(axis=1)
print(f'OpenF1 session {SESSION_KEY} | median pit-lane time {lane.median():.1f} s'
      f' | modelled pit loss {PIT_LOSS:.1f} s')
```

### Cell 21 — Real strategies vs the simulator pick

```python
order = race.results['Abbreviation'].tolist()

fig, ax = plt.subplots(figsize=(12, 8))
for _, s in stints.iterrows():
    if s['name_acronym'] in order:
        ax.barh(order.index(s['name_acronym']), s['lap_end'] - s['lap_start'] + 1,
                left=s['lap_start'] - 1, color=COLORS.get(s['compound'], 'grey'), edgecolor='black')

left = 0
for c, n in BEST:
    ax.barh(-1.5, n, left=left, color=COLORS[c], edgecolor='black', hatch='//')
    left += n

ax.set_yticks([-1.5] + list(range(len(order))), ['SIM'] + order)
ax.invert_yaxis()
ax.set(xlabel='Lap', title=f'Real {DATA_YEAR} strategies vs simulator pick for {RACE_TITLE}')
plt.show()
```

### Notebook final text cell (settings + limitations)

```markdown
# Settings you can change

| Setting | Cell | What it does |
|---|---|---|
| `FUEL_K` | 1 | Seconds per lap gained as fuel burns off (default 0.06) |
| `N_SIMS` | 1 | Simulated races per strategy. More = smoother results, slower |
| `RAIN_DEFAULT` | 3 | What-if rain chance when there is no forecast (default 15%) |
| `TRAIN_WEEKENDS` | 5 | Past race weekends used to train the winner model (default 50) |
| `TEST_RACES` | 6 | Most recent weekends held back to test the winner model |
| `RAIN_CHAOS` | 7 | How much rain flattens the winner odds |
| `P_SC` | 12 | Chance of at least one safety car. Raise to ~0.8 for street circuits |
| `SC_LAPS` | 12 | How many laps each safety car lasts |
| `SC_PIT_FACTOR` | 12 | Share of the normal pit loss paid when stopping under a safety car |
| `P_SLOW_STOP`, `SLOW_STOP_S` | 12 | Chance and cost of a slow pit stop |
| `DEG_UNCERT` | 12 | Uncertainty in tyre wear (0.15 = ±15%) |
| `min_stint`, `max_stops` | 13 | Shortest allowed stint and most stops to consider |
| `GRIP` | 14 | How much slower each tyre type is as the track gets wetter |
| `DRYING_LAPS` | 14 | Laps the track takes to dry after rain stops |
| `LOOKAHEAD` | 14 | How many laps ahead the team looks when making a weather call |
| `WINDOW_TOL` | 17 | Pit laps within this many seconds of the best count as the window |
| `pit_wall_call(...)` | 18 | Test any lap, tyre and tyre age, with or without a safety car |
| `rain_call(...)` | 19 | Test any lap, tyre and track wetness |

# Limitations

**Winner prediction**
- Needs OpenF1 practice and qualifying laps, which start in 2023, and unlocks only after qualifying (sprint qualifying for the sprint).
- Qualifying order comes from each driver's best lap, not the official Q1/Q2/Q3 classification, and grid penalties are ignored.
- The sprint prediction uses the model trained on Grand Prix weekends, fed with sprint qualifying data.
- For an upcoming race the line-up is taken from the most recent race, so a driver swap won't show.
- The first run of Cell 5 downloads around 100 sessions and takes a few minutes. Later runs use the cache.
- How much rain flattens the odds (`RAIN_CHAOS`) is an assumption.

**Strategy simulation**
- Each strategy is raced by one car on an empty track: no traffic, undercuts, overcuts or track position.
- Dry tyre pace comes from one race, with one curve per compound. The fuel effect is a fixed estimate.
- Every stint starts on new tyres, even though real cars often start on tyres used in qualifying.
- Safety cars are simplified: fixed length, same lap time, random timing.
- Wet tyre pace (`GRIP`) is an assumption, not learned from data.
- For a past wet race, rain arrives at random laps, not when it really did.
- The simulated team reacts only to current conditions and doesn't know when the rain will stop.
- Upcoming races are projected from the last race at the same circuit. 2026 cars run under new rules, so lap times from earlier years don't carry over. Stop counts and pit windows are still a fair guide.
- A brand-new circuit with no previous race can't be simulated.
- Forecasts only reach 16 days ahead, and "chance of rain" is not the same as rain that affects the race.
- Ridge regression is used for pace instead of Random Forest because tree models go flat beyond the tyre ages they've seen.
```

---

## 10. Rebuild the .ipynb from this file

```python
# rebuild_notebook.py  ->  python rebuild_notebook.py F1_Strategy_Suite_Handoff.md
import re, sys, nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

md = open(sys.argv[1], encoding='utf-8').read()
intro = re.search(r'### Notebook intro cell\n\n```markdown\n(.*?)\n```', md, re.S).group(1)
notes = re.search(r'### Notebook final text cell.*?\n\n```markdown\n(.*?)\n```', md, re.S).group(1)
cells = re.findall(r'### Cell (\d+) — (.+?)\n\n```python\n(.*?)\n```', md, re.S)

nb = new_notebook()
nb.cells.append(new_markdown_cell(intro))
for n, title, code in cells:
    nb.cells.append(new_markdown_cell(f'## {n}. {title}'))
    nb.cells.append(new_code_cell(code))
nb.cells.append(new_markdown_cell(notes))
nb.metadata = {'colab': {'provenance': [], 'toc_visible': True},
               'kernelspec': {'name': 'python3', 'display_name': 'Python 3'},
               'language_info': {'name': 'python'}}
nbformat.write(nb, 'F1_Strategy_Intelligence_Suite.ipynb')
print(len(cells), 'code cells written')
```

# Settings you can change

Your race, driver and cache choices are in the form in **1.1**. Every other setting is in **1.3**.

| Setting | What it does |
|---|---|
| `N_SIMS` | Simulated races per strategy. More = smoother results, slower |
| `FUEL_K` | Seconds per lap gained as fuel burns off (default 0.06) |
| `MIN_COMPOUND_LAPS` | Clean laps a compound needs before its pace curve is used |
| `MIN_STINT`, `MAX_STOPS` | Shortest allowed stint and most stops to consider |
| `DEFAULT_PIT_LOSS` | Pit loss used when a race has too few clean stops to measure it |
| `P_SC` | Chance of at least one safety car. Raise to ~0.8 for street circuits |
| `SC_LAPS`, `SC_SLOWDOWN` | How long each safety car lasts and how slow its laps are |
| `SC_PIT_FACTOR` | Share of the normal pit loss paid when stopping under a safety car |
| `P_SLOW_STOP`, `SLOW_STOP_S` | Chance and cost of a slow pit stop |
| `DEG_UNCERT` | Uncertainty in tyre wear (0.15 = ±15%) |
| `RAIN_DEFAULT` | What-if rain chance when there is no forecast (default 15%) |
| `WET_RACE_SHARE` | Above this share of wet-tyre laps, slick pace comes from another race |
| `GRIP` | How much slower each tyre type gets as the track gets wetter |
| `DRYING_LAPS` | Laps the track takes to dry after rain stops |
| `LOOKAHEAD` | How many laps ahead the team looks when making a weather call |
| `WINDOW_TOL`, `WINDOW_SPAN` | Pit window tolerance and how far around the ideal lap to test |
| `LOOKBACK_SEASONS` | Seasons searched for an earlier race at the same circuit |
| `pit_wall_call(...)` (6.1) | Test any lap, tyre and tyre age, with or without a safety car |
| `rain_call(...)` (6.2) | Test any lap, tyre and track wetness |

# Limitations

- Each strategy is raced by one car on an empty track: no traffic, undercuts, overcuts or track position.
- Dry tyre pace comes from one race, with one curve per compound. The fuel effect is a fixed estimate.
- Every stint starts on new tyres, even though real cars often start on tyres used in qualifying.
- Safety cars are simplified: fixed length, same lap time, random timing.
- Wet tyre pace (`GRIP`) is an assumption, not learned from data.
- For a past wet race, rain arrives at random laps, not when it really did.
- The simulated team reacts only to current conditions and doesn't know when the rain will stop.
- Upcoming races are projected from the last race at the same circuit. 2026 cars run under new rules, so lap times from earlier years don't carry over exactly. Stop counts and pit windows are still a fair guide.
- A brand-new circuit has no earlier race, so the notebook simulates the latest completed race instead.
- Forecasts only reach 16 days ahead, and "chance of rain" is not the same as rain that affects the race.
- FastF1 lap data starts in 2018 and OpenF1 in 2023.

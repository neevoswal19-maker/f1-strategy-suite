#> # 2. The race
#> ### 2.1 Calendar and race picker
#> Shows the season, marks each round `done` or `UPCOMING`, and works out which real race supplies the data. An upcoming race is projected from the last race held at the same circuit. A brand-new circuit has no earlier race to learn from, so the notebook switches to the latest completed race and says so.
NOW = pd.Timestamp.now(tz='UTC').tz_localize(None)

YEAR = int(SEASON)
schedule = season_schedule(YEAR)
if schedule.empty:
    print(f'No calendar for {YEAR} yet, using {NOW.year} instead.')
    YEAR = NOW.year
    schedule = season_schedule(YEAR)
finished = race_finished(schedule, NOW)

seen = set()
for y in range(YEAR - 1, YEAR - LOOKBACK_SEASONS - 1, -1):
    seen |= set(season_schedule(y)['circuitId'])
show = schedule[['RoundNumber', 'EventName', 'Location']].copy()
show['Date']   = schedule['EventDate'].dt.strftime('%d %b')
show['Format'] = np.where(schedule['EventFormat'].str.contains('sprint'), 'sprint', '')
show['Status'] = np.where(finished, 'done',
                          np.where(schedule['circuitId'].isin(seen), 'UPCOMING', 'UPCOMING (new circuit)'))
print(f'{YEAR} calendar')
print(show.to_string(index=False))

def pick_event(choice):
    choice = str(choice).strip()
    try:
        if choice.isdigit():
            return schedule.get_event_by_round(int(choice))
        if choice:
            return schedule.get_event_by_name(choice)
    except Exception:
        print(f'\nCould not find "{choice}" in the {YEAR} calendar, so I picked the next race.')
    ahead = schedule[~finished]
    row = ahead.iloc[0] if len(ahead) else schedule.iloc[-1]
    return schedule.get_event_by_round(int(row['RoundNumber']))

event   = pick_event(RACE)
CIRCUIT = event['circuitId']
race_utc = event['Session5DateUtc']
UPCOMING = race_utc + pd.Timedelta(hours=3) >= NOW
DATA_CANDIDATES = []      # (year, round) races that can supply data, best first

if UPCOMING:
    days = max((race_utc - NOW).days, 0)
    print(f"\n>>> UPCOMING RACE: {event['EventName']} {YEAR} on {race_utc:%d %b %Y} ({days} days to go)")
    DATA_CANDIDATES = past_races_at(CIRCUIT, YEAR)
    if DATA_CANDIDATES:
        print(f"    No race data exists yet, so I will project it from the last race at {event['Location']}.")
    else:
        done = schedule[finished]
        if len(done):
            latest = schedule.get_event_by_round(int(done.iloc[-1]['RoundNumber']))
        else:
            prev = season_schedule(YEAR - 1)
            YEAR, schedule = YEAR - 1, prev
            latest = prev.get_event_by_round(int(prev.iloc[-1]['RoundNumber']))
        print(f"    {event['Location']} is a new circuit with no earlier race to learn from.")
        print(f"    Simulating the latest completed race instead: {latest['EventName']} {YEAR}.")
        event, CIRCUIT, UPCOMING = latest, latest['circuitId'], False
        race_utc = event['Session5DateUtc']
if not UPCOMING:
    print(f"\n>>> COMPLETED RACE: {event['EventName']} {YEAR} ({race_utc:%d %b %Y})")
    DATA_CANDIDATES = [(YEAR, int(event['RoundNumber']))] + past_races_at(CIRCUIT, YEAR)

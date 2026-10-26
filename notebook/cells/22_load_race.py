#> ### 2.2 Load race data and pick the strategy driver
#> Loads the race. If more than 40% of laps were on wet tyres, slick pace is learned from an earlier dry race at the same circuit (or, failing that, from the slick laps of this race).
race = None
for DATA_YEAR, DATA_ROUND in DATA_CANDIDATES:
    race = load_race(DATA_YEAR, DATA_ROUND)
    if race is not None:
        break
if race is None:   # nothing usable at this circuit: fall back to the latest race with data
    fallback_years = [YEAR, YEAR - 1] + [y for y in (NOW.year, NOW.year - 1) if y >= 2023 and y < YEAR - 1 or y > YEAR]
    for y in dict.fromkeys(fallback_years):
        s = season_schedule(y)
        for r in s.loc[race_finished(s, NOW), 'RoundNumber'][::-1]:
            race = load_race(y, int(r))
            if race is not None:
                DATA_YEAR, DATA_ROUND = y, int(r)
                CIRCUIT = s.loc[s['RoundNumber'] == r, 'circuitId'].iloc[0]
                print(f'No lap data at this circuit, using {race.name} {y} instead.')
                break
        if race is not None:
            break

race_laps  = race.laps
TOTAL_LAPS = race.total_laps
WAS_WET    = bool(race.weather['Rainfall'].any()) or wet_share(race_laps) > 0
RACE_TITLE = f"{event['EventName']} {YEAR}" + (f' (projected from {DATA_YEAR})' if UPCOMING else '')

session, laps = race, race_laps                  # the race whose laps teach us dry tyre pace
if wet_share(race_laps) > WET_RACE_SHARE:
    print(f'{wet_share(race_laps):.0%} of laps were on wet tyres, looking for a dry race here to learn slick pace')
    for y, r in past_races_at(CIRCUIT, DATA_YEAR):
        s = load_race(y, r)
        if s is not None and wet_share(s.laps) < WET_RACE_SHARE:
            session, laps = s, s.laps
            print('   dry pace will come from the', y, 'race')
            break
    else:
        print('   no dry race here in the last seasons, so slick pace comes from the slick laps of this race')

# strategy driver: your choice, else the winner of the race the data comes from
winner = race.results.sort_values('Position')['Abbreviation'].iloc[0]
DRIVER_CODE = str(DRIVER).strip().upper() or winner
if DRIVER_CODE not in set(laps['Driver']):
    alt = session.results.sort_values('Position')['Abbreviation'].iloc[0]
    print(f'{DRIVER_CODE} has no laps in the {session.year} race used for tyre pace, so I am using {alt} instead')
    DRIVER_CODE = alt

print(f'\nSimulating: {RACE_TITLE}')
print(f'Data race: {race.name} {DATA_YEAR} ({race.source}) | laps: {TOTAL_LAPS} | wet: {WAS_WET} | '
      f'pace from: {session.name} {session.year}')
print(f'Strategy driver: {DRIVER_CODE}')
print(race_laps['Compound'].value_counts().to_string())

#> # 7. Real world
#> ### 7.1 Real strategies from the OpenF1 API
#> Finds the OpenF1 race session closest to the race date, then loads every driver's stints and pit stops. OpenF1 starts in 2023, so earlier races skip this part.
stints = None
if DATA_YEAR < 2023:
    print(f'OpenF1 data starts in 2023, so there are no real stints to compare for {DATA_YEAR}.')
else:
    try:
        races = openf1('sessions', year=DATA_YEAR, session_name='Race')
        target = pd.Timestamp(race.date).tz_localize(None)
        SESSION_KEY = int(races.loc[(utc(races['date_start']) - target).abs().idxmin(), 'session_key'])

        stints  = openf1('stints',  session_key=SESSION_KEY)
        drivers = openf1('drivers', session_key=SESSION_KEY)
        pit_df  = openf1('pit',     session_key=SESSION_KEY)

        drivers = drivers[['driver_number', 'name_acronym']].drop_duplicates('driver_number')
        stints  = stints.merge(drivers, on='driver_number')
        stints['lap_end'] = stints['lap_end'].fillna(TOTAL_LAPS)

        lane = pit_df.filter(['pit_duration', 'lane_duration']).apply(pd.to_numeric, errors='coerce').max(axis=1)
        print(f'OpenF1 session {SESSION_KEY} | {len(stints)} stints | median pit-lane time {lane.median():.1f} s'
              f' | modelled pit loss {PIT_LOSS:.1f} s')
    except Exception as err:
        stints = None
        print(f'OpenF1 is not reachable right now ({err}). Run this cell again later.')

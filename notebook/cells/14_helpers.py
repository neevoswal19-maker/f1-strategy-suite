#> ### 1.4 Helper functions
#> **Where the lap data comes from.** Since 2026, FastF1 needs a paid F1 TV login for live-timing data from 2023 onwards. This notebook gets 2023+ laps, tyres, weather and results from the free **OpenF1 API**, and older races from FastF1's free archive. Both are turned into the same lap table, so the rest of the notebook doesn't care which one was used.
#>
#> Circuits are matched by their Ergast `circuitId`, because FastF1 location names change between seasons (Miami → Miami Gardens, Yas Island → Yas Marina).
from types import SimpleNamespace

erg = Ergast()

def season_schedule(year):
    """FastF1 calendar plus the Ergast circuit id and coordinates of each round."""
    s = fastf1.get_event_schedule(year, include_testing=False)
    try:
        e = erg.get_race_schedule(season=year).set_index('round')
        for col in ['circuitId', 'lat', 'long']:
            s[col] = s['RoundNumber'].map(e[col])
    except Exception:
        s['lat'] = s['long'] = np.nan
        s['circuitId'] = np.nan
    s['circuitId'] = s['circuitId'].fillna(s['Location'].str.lower())
    return s

def race_finished(s, now):
    return s['Session5DateUtc'] + pd.Timedelta(hours=3) < now

def past_races_at(circuit_id, before_year, seasons=LOOKBACK_SEASONS):
    """(year, round) of races at this circuit in the seasons before `before_year`, newest first."""
    out = []
    for y in range(before_year - 1, max(before_year - seasons - 1, 2017), -1):
        s = season_schedule(y)
        out += [(y, int(r)) for r in s.loc[s['circuitId'] == circuit_id, 'RoundNumber']][::-1]
    return out

# ---------------- OpenF1 ----------------
OPENF1 = 'https://api.openf1.org/v1'
http = requests_cache.CachedSession(os.path.join(CACHE_DIR, 'openf1_cache'), allowable_codes=(200,))

def openf1(endpoint, cached=True, **params):
    """GET an OpenF1 endpoint as a DataFrame. Throttled, retries on rate limits, 404 = empty."""
    get = http.get if cached else requests.get
    for attempt in range(6):
        r = get(f'{OPENF1}/{endpoint}', params=params, timeout=60)
        if r.status_code == 429:
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code == 404:
            return pd.DataFrame()
        r.raise_for_status()
        if not getattr(r, 'from_cache', False):
            time.sleep(0.4)
        data = r.json()
        return pd.DataFrame(data if isinstance(data, list) else [])
    raise RuntimeError('OpenF1 is rate-limiting. Wait a minute and run this cell again.')

def utc(ts):
    return pd.to_datetime(ts, utc=True, format='ISO8601').dt.tz_convert(None)

def neutralised_periods(rc):
    """(start, end) times of safety cars, virtual safety cars and red flags from race control."""
    periods, start = [], None
    for _, m in rc.sort_values('date').iterrows():
        msg, flag = str(m.get('message', '')).upper(), str(m.get('flag', '')).upper()
        if start is None and ('DEPLOYED' in msg or flag == 'RED'):
            start = m['date']
        elif start is not None and ('ENDING' in msg or 'IN THIS LAP' in msg or
                                    (flag in ('GREEN', 'CLEAR') and str(m.get('scope', '')) == 'Track')):
            periods.append((start, m['date'] + pd.Timedelta(seconds=90)))
            start = None
    if start is not None:
        periods.append((start, rc['date'].max()))
    return periods

def race_from_openf1(year, rnd, race_utc, name):
    races = openf1('sessions', year=year, session_name='Race')
    if races.empty:
        return None
    races['start'] = utc(races['date_start'])
    gap = (races['start'] - race_utc).abs()
    if gap.min() > pd.Timedelta(days=2):
        return None
    key = int(races.loc[gap.idxmin(), 'session_key'])
    cached = race_utc < NOW - pd.Timedelta(days=2)
    get = lambda ep: openf1(ep, cached=cached, session_key=key)

    l, st, drv, wx, rc, res, pit = (get(ep) for ep in
        ['laps', 'stints', 'drivers', 'weather', 'race_control', 'session_result', 'pit'])
    if l.empty or st.empty:
        return None
    code = drv.drop_duplicates('driver_number').set_index('driver_number')['name_acronym']

    l = l.dropna(subset=['lap_duration']).copy()
    l['LapStart'] = utc(l['date_start'])
    st = st.dropna(subset=['lap_start']).copy()
    st['lap_end'] = st['lap_end'].fillna(l['lap_number'].max())
    st['tyre_age_at_start'] = st['tyre_age_at_start'].fillna(0)
    tyres = [(r['driver_number'], lap, r['compound'], r['tyre_age_at_start'] + lap - r['lap_start'] + 1)
             for _, r in st.iterrows() for lap in range(int(r['lap_start']), int(r['lap_end']) + 1)]
    tyres = pd.DataFrame(tyres, columns=['driver_number', 'lap_number', 'Compound', 'TyreLife'])
    tyres = tyres.drop_duplicates(['driver_number', 'lap_number'], keep='last')
    l = l.merge(tyres, on=['driver_number', 'lap_number'], how='left')

    pit_in = set(zip(pit['driver_number'], pit['lap_number'])) if len(pit) else set()
    periods = []
    if len(rc):
        rc['date'] = utc(rc['date'])
        periods = neutralised_periods(rc)
    end = l['LapStart'] + pd.to_timedelta(l['lap_duration'], unit='s')
    green = pd.Series(True, index=l.index)
    for a, b in periods:
        green &= ~((l['LapStart'] < b) & (end > a))

    laps = pd.DataFrame({
        'Driver': l['driver_number'].map(code), 'LapNumber': l['lap_number'],
        'LapTimeS': l['lap_duration'], 'Compound': l['Compound'].str.upper(), 'TyreLife': l['TyreLife'],
        'PitIn': [(d, n) in pit_in for d, n in zip(l['driver_number'], l['lap_number'])],
        'PitOut': l['is_pit_out_lap'].fillna(False).astype(bool), 'Green': green, 'LapStart': l['LapStart']})
    weather = pd.DataFrame({'Time': utc(wx['date']), 'TrackTemp': wx['track_temperature'],
                            'Rainfall': wx['rainfall'].fillna(0) > 0}) if len(wx) else \
              pd.DataFrame({'Time': [laps['LapStart'].min()], 'TrackTemp': [35.0], 'Rainfall': [False]})
    results = pd.DataFrame({'Abbreviation': res['driver_number'].map(code), 'Position': res['position']}) \
              if len(res) else laps.groupby('Driver')['LapNumber'].max().sort_values(ascending=False) \
                                 .rank(ascending=False, method='first').rename('Position').reset_index() \
                                 .rename(columns={'Driver': 'Abbreviation'})
    total = int(res['number_of_laps'].max()) if len(res) and 'number_of_laps' in res else int(laps['LapNumber'].max())
    return SimpleNamespace(year=year, round=rnd, name=name, date=race_utc, laps=laps,
                           weather=weather, results=results.dropna(subset=['Abbreviation']),
                           total_laps=total, source=f'OpenF1 session {key}')

# ---------------- FastF1 archive (2018-2022) ----------------
def race_from_fastf1(year, rnd):
    s = fastf1.get_session(year, rnd, 'R')
    s.load(laps=True, telemetry=False, weather=True, messages=False)
    l = s.laps
    if not len(l):
        return None
    t0 = pd.Timestamp('2000-01-01')   # laps and weather share the session clock; any fixed base works
    laps = pd.DataFrame({
        'Driver': l['Driver'], 'LapNumber': l['LapNumber'], 'LapTimeS': l['LapTime'].dt.total_seconds(),
        'Compound': l['Compound'], 'TyreLife': l['TyreLife'],
        'PitIn': l['PitInTime'].notna(), 'PitOut': l['PitOutTime'].notna(),
        'Green': l['TrackStatus'] == '1', 'LapStart': t0 + l['LapStartTime']})
    try:
        w = s.weather_data
        weather = pd.DataFrame({'Time': t0 + w['Time'], 'TrackTemp': w['TrackTemp'], 'Rainfall': w['Rainfall']})
    except Exception:          # the archive has no weather for some races
        weather = pd.DataFrame({'Time': [laps['LapStart'].min()], 'TrackTemp': [35.0], 'Rainfall': [False]})
    try:
        total = int(s.total_laps)
    except Exception:          # FastF1 raises its own error when the lap count is missing
        total = int(laps['LapNumber'].max())
    return SimpleNamespace(year=year, round=rnd, name=s.event['EventName'], date=pd.Timestamp(s.date),
                           laps=laps.dropna(subset=['LapTimeS']), weather=weather,
                           results=s.results[['Abbreviation', 'Position']].copy(),
                           total_laps=total, source='FastF1 archive')

def load_race(year, rnd):
    """One race as a standard lap table (OpenF1 for 2023+, FastF1 before), or None if there is no data."""
    try:
        ev = season_schedule(year).get_event_by_round(rnd)
        if year >= 2023:
            return race_from_openf1(year, rnd, ev['Session5DateUtc'], ev['EventName'])
        return race_from_fastf1(year, rnd)
    except Exception as err:
        print(f'   could not load {year} round {rnd}: {err}')
        return None

def wet_share(l):
    return l['Compound'].isin(['INTERMEDIATE', 'WET']).mean()

# ---------------- weather forecast ----------------
def rain_forecast(lat, lon, start_utc, hours=2):
    """Highest hourly rain probability (0-1) from the race start to `hours` later. Open-Meteo, 16 days ahead."""
    fc = requests.get('https://api.open-meteo.com/v1/forecast',
                      params={'latitude': lat, 'longitude': lon, 'forecast_days': 16,
                              'hourly': 'precipitation_probability', 'timezone': 'GMT'}, timeout=20).json()
    hourly = pd.DataFrame(fc['hourly'])
    hourly['time'] = pd.to_datetime(hourly['time'])
    window = hourly[(hourly['time'] >= start_utc.floor('h')) &
                    (hourly['time'] <= start_utc + pd.Timedelta(hours=hours))]
    p = window['precipitation_probability'].max()
    return None if pd.isna(p) else p / 100

def geocode(place):
    g = requests.get('https://geocoding-api.open-meteo.com/v1/search',
                     params={'name': place, 'count': 1}, timeout=20).json()
    return g['results'][0]['latitude'], g['results'][0]['longitude']

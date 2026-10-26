"""HTTP access to Jolpica (Ergast), OpenF1, MultiViewer and Open-Meteo, with a disk cache."""
import time
from urllib.parse import urlencode

import pandas as pd
import requests
import requests_cache

from . import config

config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
_cached = requests_cache.CachedSession(str(config.CACHE_DIR / 'http'), allowable_codes=(200, 403, 404))
_live = requests.Session()
for _s in (_cached, _live):
    _s.headers['User-Agent'] = 'pit-wall-predictor (github.com/neevoswal19-maker/f1-strategy-suite)'
_DELAY = {config.JOLPICA: 0.3, config.OPENF1: 0.4}
_last = {}


def get_json(url, params=None, cached=True):
    """GET JSON. Retries on rate limits and server errors; 404 returns None."""
    session = _cached if cached else _live
    for attempt in range(8):
        host = next((h for h in _DELAY if url.startswith(h)), None)
        if host and not (cached and session.cache.contains(url=_full(url, params))):
            wait = _DELAY[host] - (time.time() - _last.get(host, 0))
            if wait > 0:
                time.sleep(wait)
            _last[host] = time.time()
        try:
            r = session.get(url, params=params, timeout=60)
        except requests.RequestException:
            time.sleep(3 * (attempt + 1))
            continue
        if r.status_code == 429 or r.status_code >= 500:
            if cached:
                session.cache.delete(urls=[r.url])
            time.sleep(min(5 * (attempt + 1), 30))
            continue
        if r.status_code in (403, 404):
            return None
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f'Gave up on {url} {params}')


def _full(url, params):
    return url + ('?' + urlencode(params) if params else '')


# ---------------- Jolpica / Ergast ----------------
def jolpica(path, cached=True):
    """All pages of a Jolpica table, as a list of race dicts (results of one race may span pages)."""
    races, offset = [], 0
    while True:
        d = get_json(f'{config.JOLPICA}/{path}.json', {'limit': 100, 'offset': offset}, cached)
        if not d:
            break
        mr = d['MRData']
        table = next(v for k, v in mr.items() if k.endswith('Table'))
        races += table.get('Races', [])
        offset += 100
        if offset >= int(mr['total']):
            break
    return races


# ---------------- OpenF1 ----------------
def openf1(endpoint, cached=True, **params):
    d = get_json(f'{config.OPENF1}/{endpoint}', params, cached)
    return pd.DataFrame(d if isinstance(d, list) else [])


# ---------------- MultiViewer (circuit outlines) ----------------
def circuit_info(circuit_key, year):
    for y in range(year, year - 4, -1):
        d = get_json(f'{config.MULTIVIEWER}/circuits/{circuit_key}/{y}')
        if d and d.get('x'):
            return d
    return None


# ---------------- Open-Meteo ----------------
def rain_forecast(lat, lon, start_utc, hours=2):
    """Highest hourly rain probability (0-1) over the race window, or None beyond 16 days."""
    d = get_json(config.OPEN_METEO, {'latitude': lat, 'longitude': lon, 'forecast_days': 16,
                                     'hourly': 'precipitation_probability', 'timezone': 'GMT'},
                 cached=False)
    if not d or 'hourly' not in d:
        return None
    h = pd.DataFrame(d['hourly'])
    h['time'] = pd.to_datetime(h['time'])
    w = h[(h['time'] >= start_utc.floor('h')) & (h['time'] <= start_utc + pd.Timedelta(hours=hours))]
    p = w['precipitation_probability'].max()
    return None if pd.isna(p) else float(p) / 100

"""Practice and qualifying features from OpenF1 (moved from old notebook cell 5), plus per-race
conditions (wet, safety cars). Finished weekends are stored in CSV files so cron runs stay quick."""
import numpy as np
import pandas as pd

from . import config
from .sources import openf1

WEEKEND_FEATS = ['fp_gap', 'fp_lr_gap', 'q_gap', 'q_pos']
STORE_FEATS = config.STORE_DIR / 'weekend_features.csv'
STORE_COND = config.STORE_DIR / 'race_conditions.csv'


def utc(s):
    return pd.to_datetime(s, utc=True, format='ISO8601').dt.tz_convert(None)


_sessions = {}


def sessions(year, cached):
    if year not in _sessions:
        s = openf1('sessions', cached=cached, year=year)
        if len(s):
            s['start'] = utc(s['date_start'])
            s['end'] = utc(s['date_end'])
        _sessions[year] = s
    return _sessions[year]


def meeting_for(race_start, cached=True):
    """OpenF1 meeting_key of the weekend whose race starts within a day of `race_start`."""
    s = sessions(race_start.year, cached)
    if s.empty:
        return None
    near = s[(s['start'] >= race_start - pd.Timedelta(days=4)) & (s['start'] <= race_start + pd.Timedelta(days=1))]
    return int(near['meeting_key'].mode().iloc[0]) if len(near) else None


def find_session(meeting, names, year, cached=True):
    s = sessions(year, cached)
    s = s[s['meeting_key'] == meeting]
    for n in names:
        hit = s[s['session_name'] == n]
        if len(hit):
            return hit.iloc[0]
    return None


def drivers(session_key, cached=True):
    d = openf1('drivers', cached=cached, session_key=int(session_key))
    return d.drop_duplicates('driver_number') if len(d) else d


def session_pace(key, cached=True):
    """Best-lap gap, long-run gap (5+ lap runs) and lap rank per driver number."""
    l = openf1('laps', cached=cached, session_key=int(key))
    if l.empty or 'lap_duration' not in l:
        return pd.DataFrame()
    l = l.dropna(subset=['lap_duration']).sort_values(['driver_number', 'lap_number'])
    if l.empty:
        return pd.DataFrame()
    best = l.groupby('driver_number')['lap_duration'].min()
    pit_out = l['is_pit_out_lap'].fillna(False).astype(bool)
    l['ok'] = (l['lap_duration'] < 1.10 * l['driver_number'].map(best)) & ~pit_out
    l['run'] = (~l['ok']).groupby(l['driver_number']).cumsum()
    runs = l[l['ok']].groupby(['driver_number', 'run'])['lap_duration'].agg(['median', 'size'])
    long_run = runs[runs['size'] >= 5].groupby('driver_number')['median'].min()
    return pd.DataFrame({'best': best, 'gap': best / best.min() - 1,
                         'lr': long_run, 'lr_gap': long_run / long_run.min() - 1,
                         'pos': best.rank(method='first')})


def weekend_features(meeting, year, kind='gp', cached=True):
    """One row per driver code: fp_gap, fp_lr_gap, q_gap, q_pos (official order when available)."""
    q_names, fp_names = ((config.QUALI, config.GP_PRACTICE) if kind == 'gp'
                         else (config.SPRINT_QUALI, config.SPRINT_PRACTICE))
    fp, q = find_session(meeting, fp_names, year, cached), find_session(meeting, q_names, year, cached)
    if fp is None or q is None:
        return pd.DataFrame()
    fpp, qp = session_pace(fp['session_key'], cached), session_pace(q['session_key'], cached)
    if qp.empty:
        return pd.DataFrame()
    res = openf1('session_result', cached=cached, session_key=int(q['session_key']))
    if len(res) and 'position' in res:
        res = res.assign(position=pd.to_numeric(res['position'], errors='coerce')).drop_duplicates('driver_number')
    if len(res) and 'position' in res and res['position'].notna().sum() >= 10:
        official = res.set_index('driver_number')['position'].astype(float)
        qp['pos'] = official.reindex(qp.index).fillna(qp['pos'] + 100).rank(method='first')
    d = drivers(q['session_key'], cached)
    code = d.set_index('driver_number')['name_acronym'] if len(d) else pd.Series(dtype=str)
    out = pd.DataFrame({'q_gap': qp['gap'], 'q_pos': qp['pos'], 'q_best': qp['best']})
    if len(fpp):
        out = out.join(fpp[['gap', 'lr_gap', 'lr']].rename(columns={'gap': 'fp_gap', 'lr_gap': 'fp_lr_gap',
                                                                     'lr': 'fp_lr'}), how='left')
    else:
        out[['fp_gap', 'fp_lr_gap', 'fp_lr']] = np.nan
    out['driverCode'] = out.index.map(code)
    out['number'] = out.index
    out['pole_time'] = qp['best'].min()
    out['fp_session'] = fp['session_name']
    out['q_session'] = q['session_name']
    return out.dropna(subset=['driverCode']).reset_index(drop=True)


def fill_weekend(d):
    """Missing practice numbers get the field's worst value (did not run / no long run)."""
    d = d.copy()
    d['fp_gap'] = d['fp_gap'].fillna(d['fp_gap'].max()).fillna(0.03)
    d['fp_lr_gap'] = d['fp_lr_gap'].fillna(d['fp_gap'])
    d['q_gap'] = d['q_gap'].fillna(d['q_gap'].max())
    d['q_pos'] = d['q_pos'].fillna(len(d))
    return d


def race_conditions(meeting, year, cached=True):
    race = find_session(meeting, ['Race'], year, cached)
    if race is None:
        return None
    k = int(race['session_key'])
    wx = openf1('weather', cached=cached, session_key=k)
    rc = openf1('race_control', cached=cached, session_key=k)
    msg = rc['message'].astype(str).str.upper() if len(rc) else pd.Series(dtype=str)
    return {'wet': bool(len(wx) and (wx['rainfall'].fillna(0) > 0).any()),
            'sc': int(msg.str.contains('SAFETY CAR DEPLOYED').sum() - msg.str.contains('VIRTUAL SAFETY CAR DEPLOYED').sum()),
            'vsc': int(msg.str.contains('VIRTUAL SAFETY CAR DEPLOYED').sum()),
            'red': int((rc['flag'] == 'RED').sum()) if len(rc) else 0,
            'circuit_key': int(race['circuit_key'])}


def _load(path):
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def update_stores(races, now, log=print):
    """Fill the feature + condition stores for every finished weekend (2023+) not stored yet."""
    feats, cond = _load(STORE_FEATS), _load(STORE_COND)
    have_f = set(zip(feats['race_id'], feats['kind'])) if len(feats) else set()
    have_c = set(cond['race_id']) if len(cond) else set()
    new_f, new_c = [], []
    todo = races[(races['season'] >= config.WEEKEND_FROM) & (races['raceStart'] + pd.Timedelta(days=1) < now)]
    for i, r in enumerate(todo.itertuples(), 1):
        rid = r.season * 100 + r.round
        kinds = ['gp'] + (['sprint'] if r.sprint else [])
        if all((rid, k) in have_f for k in kinds) and rid in have_c:
            continue
        m = meeting_for(r.raceStart)
        if m is None:
            continue
        try:
            for k in kinds:
                if (rid, k) not in have_f:
                    wk = weekend_features(m, r.season, k)
                    if len(wk):
                        new_f.append(wk.assign(race_id=rid, kind=k))
            if rid not in have_c:
                c = race_conditions(m, r.season)
                if c:
                    new_c.append({'race_id': rid, 'meeting_key': m, **c})
        except Exception as err:        # one odd weekend should not stop the whole build
            log(f'   skipped {rid}: {err!r}')
        if i % 10 == 0:
            log(f'   weekends checked: {i}/{len(todo)}')
            feats, cond, new_f, new_c = _save(feats, cond, new_f, new_c)
    feats, cond, _, _ = _save(feats, cond, new_f, new_c)
    log(f'Store: {len(feats)} driver-weekend rows, {len(cond)} race conditions')
    return feats, cond


def _save(feats, cond, new_f, new_c):
    config.STORE_DIR.mkdir(parents=True, exist_ok=True)
    if new_f:
        feats = pd.concat([feats] + new_f, ignore_index=True)
        feats.to_csv(STORE_FEATS, index=False, float_format='%.6g')
    if new_c:
        cond = pd.concat([cond, pd.DataFrame(new_c)], ignore_index=True)
        cond.to_csv(STORE_COND, index=False)
    return feats, cond, [], []

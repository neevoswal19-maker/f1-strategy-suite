"""Race calendar, race results and leakage-free driver form (moved from old notebook cell 4)."""
import numpy as np
import pandas as pd

from . import config
from .sources import jolpica

SESSION_KEYS = {'FirstPractice': 'FP1', 'SecondPractice': 'FP2', 'ThirdPractice': 'FP3',
                'SprintQualifying': 'Sprint Qualifying', 'Sprint': 'Sprint', 'Qualifying': 'Qualifying'}


def _ts(block):
    return pd.Timestamp(f"{block['date']} {block.get('time', '00:00:00Z')}").tz_localize(None)


def schedule(year, cached):
    rows = []
    for r in jolpica(str(year), cached):
        c = r['Circuit']
        sessions = [{'name': name, 'start': _ts(r[k])} for k, name in SESSION_KEYS.items() if k in r]
        sessions.append({'name': 'Race', 'start': _ts(r)})
        rows.append({'season': year, 'round': int(r['round']), 'raceName': r['raceName'],
                     'circuitId': c['circuitId'], 'circuitName': c['circuitName'],
                     'locality': c['Location']['locality'], 'country': c['Location']['country'],
                     'lat': float(c['Location']['lat']), 'long': float(c['Location']['long']),
                     'raceStart': _ts(r), 'sprint': 'Sprint' in r,
                     'sessions': sorted(sessions, key=lambda s: s['start'])})
    return pd.DataFrame(rows)


def season_results(year, cached):
    rows = []
    for race in jolpica(f'{year}/results', cached):
        for x in race['Results']:
            d = x['Driver']
            rows.append({'season': year, 'round': int(race['round']), 'raceDate': race['date'],
                         'circuitId': race['Circuit']['circuitId'],
                         'number': int(x.get('number', 0) or 0), 'driverId': d['driverId'],
                         'driverCode': d.get('code') or d['familyName'][:3].upper(),
                         'givenName': d['givenName'], 'familyName': d['familyName'],
                         'constructorId': x['Constructor']['constructorId'],
                         'constructorName': x['Constructor']['name'],
                         'grid': int(x.get('grid', 0) or 0), 'position': int(x['position']),
                         'positionText': x['positionText'], 'points': float(x['points']),
                         'status': x.get('status', ''), 'laps': int(x.get('laps', 0) or 0)})
    return pd.DataFrame(rows)


def sprint_winner(year, rnd, cached=False):
    races = jolpica(f'{year}/{rnd}/sprint', cached)
    for r in races:
        for x in r.get('SprintResults', []):
            if x['position'] == '1':
                return x['Driver'].get('code')
    return None


def load_results(season, cached_before):
    frames = [season_results(y, cached=y < cached_before) for y in range(config.HISTORY_FROM, season + 1)]
    return pd.concat([f for f in frames if len(f)], ignore_index=True)


def add_form(hist, conditions):
    """Rolling form features using only races before each row (shift(1)). `hist` is sorted by race."""
    hist = hist.sort_values(['season', 'round']).reset_index(drop=True)
    hist['race_id'] = hist['season'] * 100 + hist['round']
    hist['grid'] = hist['grid'].replace(0, 20)                    # 0 = pit-lane start
    done = hist['position'].notna()
    hist['win'] = (hist['position'] == 1).astype(float)
    hist['podium'] = np.where(done, (hist['position'] <= 3).astype(float), np.nan)
    hist['dnf'] = np.where(done, (~hist['positionText'].astype(str).str.isdigit()).astype(float), np.nan)
    hist['gain'] = np.where(done & (hist['dnf'] == 0), hist['grid'] - hist['position'], np.nan)
    wet = hist['race_id'].map(conditions.set_index('race_id')['wet']) if len(conditions) else np.nan
    hist['wet_gain'] = np.where(wet == True, hist['gain'], np.nan)   # noqa: E712

    def past(col, by, n=None, how='mean'):
        g = hist.groupby(by)[col]
        if n:
            return g.transform(lambda s: s.shift(1).rolling(n, min_periods=1).agg(how))
        return g.transform(lambda s: s.shift(1).expanding().agg(how))

    hist['form_finish'] = past('position', 'driverId', 5)
    hist['form_grid'] = past('grid', 'driverId', 5)
    hist['form_points'] = past('points', 'driverId', 5)
    hist['dnf_rate'] = past('dnf', 'driverId', 10)
    hist['racecraft'] = past('gain', 'driverId', 10)
    hist['wet_skill'] = past('wet_gain', 'driverId')
    hist['track_form'] = past('position', ['driverId', 'circuitId'])
    hist['track_podiums'] = past('podium', ['driverId', 'circuitId'], how='sum')
    hist['track_wins'] = past('win', ['driverId', 'circuitId'], how='sum')
    hist['track_starts'] = past('podium', ['driverId', 'circuitId'], how='count')

    team = hist.groupby(['race_id', 'constructorId', 'circuitId'], as_index=False).agg(
        points=('points', 'sum'), best=('position', 'min'))
    team['team_form'] = team.groupby('constructorId')['points'].transform(
        lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    team['team_track'] = team.groupby(['constructorId', 'circuitId'])['best'].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    hist = hist.merge(team[['race_id', 'constructorId', 'team_form', 'team_track']],
                      on=['race_id', 'constructorId'], how='left')

    # teammate head-to-head on the grid, last 10 races
    mate = hist.groupby(['race_id', 'constructorId'])['grid'].transform('min')
    cnt = hist.groupby(['race_id', 'constructorId'])['grid'].transform('size')
    hist['beat_mate'] = np.where(cnt == 2, (hist['grid'] <= mate).astype(float), np.nan)
    hist['h2h'] = past('beat_mate', 'driverId', 10)

    hist['cum_pts'] = hist.groupby(['season', 'driverId'])['points'].transform(
        lambda s: s.shift(1).fillna(0).cumsum())
    top = hist.groupby('race_id')['cum_pts'].transform('max')
    hist['pts_share'] = (hist['cum_pts'] / top.replace(0, np.nan)).fillna(0)

    hist = hist.fillna({'form_finish': 15, 'form_grid': 15, 'form_points': 0, 'dnf_rate': 0.15,
                        'team_form': 2, 'racecraft': 0, 'wet_skill': 0, 'track_podiums': 0,
                        'track_wins': 0, 'track_starts': 0, 'h2h': 0.5, 'team_track': 12})
    hist['track_form'] = hist['track_form'].fillna(hist['form_finish'])
    return hist


FORM_FEATS = ['form_finish', 'form_grid', 'form_points', 'dnf_rate', 'team_form', 'pts_share', 'track_form']

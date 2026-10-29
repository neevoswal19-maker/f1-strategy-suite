"""Build the website data: python -m pipeline.build

Writes web/public/data/index.json, weekends/<season>-<round>.json and tracks/<circuitId>.json.
Set F1_NOW (e.g. 2026-10-31T23:00) to pretend it is another time, F1_SEASON for another season.
"""
import json
import math
import os
import time
from types import SimpleNamespace

import numpy as np
import pandas as pd

from . import config, history, learning, model, simparams, weekend
from .sources import rain_forecast
from .tracks import build_track

T0 = time.time()


def log(*a):
    print(f'[{time.time() - T0:6.1f}s]', *a, flush=True)


def clean(o):
    """JSON-safe: NaN -> None, numpy -> python, timestamps -> ISO strings."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, pd.Timestamp):
        return None if pd.isna(o) else o.strftime('%Y-%m-%dT%H:%M:%SZ')
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if math.isnan(o) else round(float(o), 5)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(clean(data), separators=(',', ':'), ensure_ascii=False)
    old = path.read_text(encoding='utf-8') if path.exists() else None
    if old is None or _strip_time(old) != _strip_time(text):
        path.write_text(text, encoding='utf-8')


def _strip_time(text):
    d = json.loads(text)
    d.pop('generatedAt', None)
    return json.dumps(d, sort_keys=True)


# ---------------- helpers ----------------
def session_info(meeting, names, year, cached):
    s = weekend.find_session(meeting, names, year, cached) if meeting else None
    return s


def driver_cards(meeting, year, cached, fallback_meeting=None):
    """Display info (name, team, colour, photo) from the latest session of the meeting."""
    for m in [meeting, fallback_meeting]:
        if not m:
            continue
        s = weekend.sessions(year, cached)
        s = s[(s['meeting_key'] == m) & (s['start'] < config.now())].sort_values('start')
        for key in s['session_key'][::-1]:
            d = weekend.drivers(key, cached)
            if len(d) >= 18:
                return {r['name_acronym']: {
                    'code': r['name_acronym'], 'number': int(r['driver_number']),
                    'first': str(r.get('first_name') or '').title(), 'last': str(r.get('last_name') or '').title(),
                    'team': r.get('team_name'), 'colour': '#' + str(r.get('team_colour') or '888888'),
                    'photo': r.get('headshot_url')} for _, r in d.iterrows()}
    return {}


TEAM_COLOURS = {
    'mercedes': '#27F4D2', 'red_bull': '#3671C6', 'ferrari': '#E8002D', 'mclaren': '#FF8000',
    'alpine': '#0093CC', 'renault': '#FFF500', 'alphatauri': '#5E8FAA', 'toro_rosso': '#469BFF',
    'rb': '#6692FF', 'aston_martin': '#229971', 'racing_point': '#F596C8', 'force_india': '#F596C8',
    'williams': '#64C4FF', 'alfa': '#C92D4B', 'sauber': '#52E252', 'haas': '#B6BABD',
}


def cards_from_results(rows):
    return {r['driverCode']: {'code': r['driverCode'], 'number': int(r['number'] or 0),
                              'first': r['givenName'], 'last': r['familyName'], 'team': r['constructorName'],
                              'colour': TEAM_COLOURS.get(r['constructorId'], '#8a8a93'), 'photo': None}
            for _, r in rows.iterrows()}


def circuit_stats(hist, cond, races, circuit_id, laps_default):
    done = hist[hist['position'].notna() & (hist['circuitId'] == circuit_id)]
    corr = done.groupby('race_id')[['grid', 'position']].apply(lambda d: d['grid'].corr(d['position'], method='spearman'))
    allc = hist[hist['position'].notna()].groupby('race_id')[['grid', 'position']].apply(
        lambda d: d['grid'].corr(d['position'], method='spearman'))
    rid_circuit = (races['season'] * 100 + races['round']).to_frame('race_id').assign(circuitId=races['circuitId'].values)
    c = cond.merge(rid_circuit, on='race_id', how='left') if len(cond) else pd.DataFrame()
    here = c[c['circuitId'] == circuit_id] if len(c) else c
    sc = (here['sc'] > 0).mean() if len(here) else ((c['sc'] > 0).mean() if len(c) else 0.5)
    vsc = ((here['sc'] + here['vsc']) > 0).mean() if len(here) else 0.6
    laps = done.groupby('race_id')['laps'].max()
    return {'overtaking': float(np.clip((corr.mean() if len(corr) else allc.median()), 0, 1)),
            'scChance': float(sc), 'neutralisedChance': float(vsc),
            'laps': int(laps.iloc[-1]) if len(laps) else laps_default,
            'pastRaces': int(len(corr))}


def target_rows(hist_raw, rnd_row, lineup):
    """Placeholder rows for an upcoming race so form features are computed the same way."""
    latest = hist_raw.sort_values(['season', 'round']).groupby('driverCode').tail(1).set_index('driverCode')
    team_of = {}
    for code, card in lineup.items():
        if code in latest.index:
            team_of.setdefault(card['team'], latest.loc[code, 'constructorId'])
    rows = []
    for code, card in lineup.items():
        known = code in latest.index
        rows.append({'season': rnd_row['season'], 'round': rnd_row['round'],
                     'raceDate': rnd_row['raceStart'].strftime('%Y-%m-%d'), 'circuitId': rnd_row['circuitId'],
                     'number': card['number'], 'driverCode': code,
                     'driverId': latest.loc[code, 'driverId'] if known else code.lower(),
                     'givenName': card['first'], 'familyName': card['last'],
                     'constructorId': team_of.get(card['team'],
                                                  latest.loc[code, 'constructorId'] if known else str(card['team']).lower()),
                     'constructorName': card['team'], 'grid': np.nan, 'position': np.nan,
                     'positionText': '', 'points': np.nan, 'status': '', 'laps': np.nan})
    return pd.DataFrame(rows)


def prediction_block(rows, win_model, lr_model, rain, rain_source, kind, actual, n_train, temp=1.0, probs=None):
    rows = rows.copy()
    if probs is not None:      # the replayed self-learning prediction for this race
        p = rows['driverCode'].map(probs).fillna(1e-6)
        rows['p'] = p / p.sum()
    else:
        rows['p'] = model.race_probs(win_model, rows, temp)
    win, pod, exp_pos = model.sample_orders(rows['p'].values, rain)
    rows['win'], rows['podium'], rows['exp'] = win, pod, exp_pos
    why = model.reasons(rows, lr_model)
    rows = rows.sort_values('win', ascending=False)
    rat, raw = simparams.ratings(rows), simparams.raw_values(rows)
    results = [{'code': r['driverCode'], 'win': r['win'], 'podium': r['podium'], 'expPos': r['exp'],
                'qPos': r['q_pos'], 'team': r['team'], 'reasons': why[i],
                'ratings': rat.loc[i].to_dict(), 'raw': raw.loc[i].to_dict()} for i, r in rows.iterrows()]
    pick = results[0]['code']
    return {'kind': kind, 'label': 'Sprint' if kind == 'sprint' else 'Grand Prix',
            'rainChance': rain, 'rainSource': rain_source,
            'sessions': {'practice': rows['fp_session'].iloc[0] if rows['has_fp'].iloc[0] else None,
                         'qualifying': rows['q_session'].iloc[0]},
            'counts': {'drivers': len(rows), 'trainingWeekends': n_train},
            'results': results, 'predictedWinner': pick, 'actualWinner': actual,
            'hit': (actual == pick) if actual else None}


# ---------------- main ----------------
def main():
    now = config.now()
    season = int(os.environ.get('F1_SEASON', now.year))
    log(f'Building for season {season}, now = {now:%Y-%m-%d %H:%M} UTC')

    races = pd.concat([history.schedule(y, cached=y < season)
                       for y in range(config.TRAIN_FROM, season + 1)], ignore_index=True)
    cal = races[races['season'] == season].reset_index(drop=True)
    log(f'Calendar: {len(cal)} rounds in {season}')

    hist_raw = history.load_results(season, cached_before=season)
    log(f'Results: {hist_raw["race_id"].nunique() if "race_id" in hist_raw else hist_raw.groupby(["season", "round"]).ngroups} races since {config.HISTORY_FROM}')

    feats, cond = weekend.update_stores(races, now, log)

    cal['done'] = cal['raceStart'] + pd.Timedelta(hours=3) < now
    current = cal[~cal['done']].iloc[0] if (~cal['done']).any() else None
    cur_meeting = weekend.meeting_for(current['raceStart'], cached=False) if current is not None else None
    last_done = cal[cal['done']].iloc[-1] if cal['done'].any() else None
    last_meeting = weekend.meeting_for(last_done['raceStart'], cached=False) if last_done is not None else None

    # lineup + form rows for the current weekend
    lineup = driver_cards(cur_meeting, season, False, last_meeting) if current is not None else {}
    hist_all = hist_raw
    if current is not None and lineup:
        hist_all = pd.concat([hist_raw, target_rows(hist_raw, current, lineup)], ignore_index=True)
    hist = history.add_form(hist_all, cond)
    team_names = hist.sort_values('race_id').groupby('constructorId')['constructorName'].last()

    # training table: finished 2023+ weekends with practice + qualifying features
    gp_feats = feats[feats['kind'] == 'gp'].drop(columns=['kind', 'number'])
    done_rows = hist[hist['position'].notna() & (hist['season'] >= config.TRAIN_FROM)]
    train_all = done_rows.merge(gp_feats, on=['race_id', 'driverCode'], how='inner')
    train_all = pd.concat([weekend.fill_weekend(d) for _, d in train_all.groupby('race_id')], ignore_index=True)
    train_all['team'] = train_all['constructorId'].map(team_names)
    train_all = train_all[train_all.groupby('race_id')['win'].transform('sum') == 1]
    n_weekends = train_all['race_id'].nunique()
    log(f'Training set: {n_weekends} weekends, {len(train_all)} driver entries')

    state = learning.run(train_all, races, log)
    best_name = f"Blend of {state['tried']} self-weighting setups"
    bt, window = state['backtest'], state['window']
    for k, v in bt.items():
        log('   ', k, {a: round(b, 3) for a, b in v.items()})
    win_model = model.fit_setup(state['key'], state['halfLife'], train_all)
    lr_model = model.fit('Logistic regression', train_all)
    imp = model.importances(win_model)

    wet_map = dict(zip(cond['race_id'], cond['wet'])) if len(cond) else {}
    weights, sim_nll, sim_n = simparams.fit_weights(train_all, wet_map)
    log('Simulator weights:', weights.to_dict())

    model_card = {'name': best_name, 'backtest': bt, 'window': window,
                  'importance': imp.round(4).to_dict(), 'trainingWeekends': n_weekends,
                  'features': model.FEATS,
                  'learning': {'trusted': state['trusted'], 'calibration': state['calibration'],
                               'setups': state['tried'], 'replayed': state['replayed'], 'overall': state['overall'],
                               'recent': state['backtest'], 'eta': state['eta'], 'alpha': state['alpha'],
                               'eras': state['eras'], 'firstRace': state['firstRace'],
                               'history': state['history'][-12:][::-1]}}
    sim_card = {'weights': weights.to_dict(),
                'params': [{'key': k, 'label': l, 'desc': d} for k, l, d in simparams.PARAMS],
                'fittedOn': sim_n}

    ctx = SimpleNamespace(now=now, races=races, hist=hist, cond=cond, feats=feats, train_all=train_all,
                          best_name=best_name, win_model=win_model, lr_model=lr_model, n_weekends=n_weekends,
                          team_names=team_names, sim_card=sim_card, window=window, state=state)

    # the current season is rebuilt every run; finished seasons only when their summary is missing
    seasons = []
    for y in range(config.TRAIN_FROM, season + 1):
        summary_file = config.OUT_DIR / 'seasons' / f'{y}.json'
        if y < season and summary_file.exists() and not os.environ.get('FULL_REBUILD'):
            summary = json.loads(summary_file.read_text(encoding='utf-8'))
        else:
            cal_y = cal if y == season else races[races['season'] == y].reset_index(drop=True)
            cal_y = cal_y.assign(done=cal_y['raceStart'] + pd.Timedelta(hours=3) < now)
            rows = build_season(y, cal_y, ctx,
                                current if y == season else None,
                                cur_meeting if y == season else None,
                                last_meeting if y == season else None,
                                lineup if y == season else {})
            scored = [r for r in rows if r['hit'] is not None]
            summary = {'season': y, 'hitRate': {'hits': sum(r['hit'] for r in scored), 'races': len(scored)},
                       'weekends': rows}
            write(summary_file, summary)
            log(f'Season {y}: hit rate {summary["hitRate"]}')
        seasons.append(summary)

    this = seasons[-1]
    index = {'season': season, 'generatedAt': now,
             'current': next((r['id'] for r in this['weekends'] if r['status'] == 'current'), this['weekends'][-1]['id']),
             'hitRate': this['hitRate'],
             'seasons': [{'season': s['season'], **s['hitRate']} for s in seasons],
             'model': model_card, 'simulator': sim_card, 'weekends': this['weekends'],
             'mistakes': recent_mistakes(seasons)}
    write(config.OUT_DIR / 'index.json', index)
    log(f'Done. {season} hit rate {index["hitRate"]}')


def recent_mistakes(seasons, n=8):
    """Latest races the model got wrong, with how much chance it gave the real winner."""
    misses = [dict(w, season=s['season']) for s in seasons for w in s['weekends'] if w.get('hit') is False]
    misses.sort(key=lambda w: w['id'], reverse=True)
    return [{k: w.get(k) for k in ('id', 'name', 'predicted', 'predictedWin', 'actual', 'actualWin', 'actualGrid')}
            for w in misses[:n]]


MIN_PRIOR_WEEKENDS = 8   # archive predictions need at least this many earlier weekends to train on


def build_season(season, cal, ctx, current, cur_meeting, last_meeting, lineup):
    """Write weekends/<season>-<round>.json for every round and return the season's summary rows."""
    now, hist, cond, feats, train_all = ctx.now, ctx.hist, ctx.cond, ctx.feats, ctx.train_all
    team_names, races = ctx.team_names, ctx.races
    index_rows = []
    for _, rnd in cal.iterrows():
        rid = season * 100 + int(rnd['round'])
        wid = f'{season}-{int(rnd["round"]):02d}'
        is_current = current is not None and rnd['round'] == current['round']
        status = 'done' if rnd['done'] else ('current' if is_current else 'upcoming')
        meeting = (cur_meeting if is_current else
                   (weekend.meeting_for(rnd['raceStart'], cached=bool(rnd['done'])) if rnd['raceStart'] < now + pd.Timedelta(days=7) else None))

        # track
        track_file = None
        ck = None
        if meeting:
            s = weekend.sessions(season, not is_current)
            hit = s[s['meeting_key'] == meeting]
            ck = int(hit['circuit_key'].iloc[0]) if len(hit) else None
        race_key = None
        if meeting:
            rs = weekend.find_session(meeting, ['Race'], season, not is_current)
            race_key = int(rs['session_key']) if rs is not None and rnd['done'] else None
        if ck is None:
            past = cond[cond['race_id'].isin(races.loc[races['circuitId'] == rnd['circuitId'], 'season'] * 100
                                              + races.loc[races['circuitId'] == rnd['circuitId'], 'round'])]
            ck = int(past['circuit_key'].iloc[-1]) if len(past) else None
        track = build_track(rnd['circuitId'], ck, season, race_key) if ck or race_key else None
        if track:
            track_file = f'tracks/{rnd["circuitId"]}.json'

        stats = circuit_stats(hist, cond, races, rnd['circuitId'], 57)
        if track and track.get('pitLoss'):
            stats['pitLoss'] = track['pitLoss']

        sessions = [{'name': s['name'], 'start': s['start']} for s in rnd['sessions']]
        actual_gp = None
        if rnd['done']:
            w = hist[(hist['race_id'] == rid) & (hist['position'] == 1)]
            actual_gp = w['driverCode'].iloc[0] if len(w) else None

        preds, gates = {}, {}
        kinds = ['gp'] + (['sprint'] if rnd['sprint'] else [])
        for kind in kinds:
            qname = 'Qualifying' if kind == 'gp' else 'Sprint Qualifying'
            qstart = next((s['start'] for s in rnd['sessions'] if s['name'] == qname), None)
            qsess = session_info(meeting, config.QUALI if kind == 'gp' else config.SPRINT_QUALI, season,
                                 cached=not is_current)
            qend = qsess['end'] if qsess is not None and pd.notna(qsess['end']) else (
                qstart + pd.Timedelta(hours=1) if qstart is not None else None)
            unlock = qend + config.UNLOCK_AFTER if qend is not None else None
            gate = {'session': qname, 'sessionStart': qstart, 'unlockAt': unlock,
                    'unlocked': False, 'reason': 'locked'}
            rows = pd.DataFrame()
            if unlock is not None and now >= unlock and season >= config.TRAIN_FROM:
                stored = feats[(feats['race_id'] == rid) & (feats['kind'] == kind)]
                if rnd['done'] and len(stored):
                    rows = hist[hist['race_id'] == rid].merge(stored.drop(columns=['kind', 'number']),
                                                             on=['race_id', 'driverCode'], how='inner')
                else:   # live weekend, or a race from the last day that isn't in the store yet
                    wk = weekend.weekend_features(meeting, season, kind, cached=False) if meeting else pd.DataFrame()
                    if len(wk):
                        rows = hist[hist['race_id'] == rid].merge(wk.drop(columns=['number']).assign(race_id=rid),
                                                                 on=['race_id', 'driverCode'], how='inner')
                gate['reason'] = 'ready' if len(rows) >= 10 else 'waiting-for-data'
            gates[kind] = gate
            if len(rows) < 10:
                continue
            rows = weekend.fill_weekend(rows)
            rows['team'] = rows['constructorName'].fillna(rows['constructorId'].map(team_names))
            # model trained only on weekends before this one (archive) or on everything (live)
            prior = train_all[train_all['race_id'] < rid]
            replay = ctx.state['byRace'].get(rid)
            if rnd['done'] and replay is None and prior['race_id'].nunique() < MIN_PRIOR_WEEKENDS:
                gate['reason'] = 'not-enough-history'      # too early in 2023 to predict honestly
                continue
            probs, temp = None, 1.0
            if rnd['done']:
                # what the model said at the time: the replayed blend (GP) or its most trusted setup then (sprint)
                setup = learning.parse(replay['combo']) if replay else (ctx.state['key'], ctx.state['halfLife'])
                if kind == 'gp' and replay:
                    wm, probs = None, replay['probs']
                else:
                    wm = model.fit_setup(*setup, prior)
                lm, n_tr = model.fit('Logistic regression', prior), prior['race_id'].nunique()
            else:   # live weekend: every setup trained on all finished races, blended by the learned weights
                wm, lm, n_tr = None, ctx.lr_model, ctx.n_weekends
                probs = learning.ensemble_probs(ctx.state, train_all, rows)
            if rnd['done']:
                rain, rain_src = config.RAIN_DEFAULT, 'default'
            else:
                fc = rain_forecast(rnd['lat'], rnd['long'],
                                   rnd['raceStart'] if kind == 'gp' else next(
                                       (s['start'] for s in rnd['sessions'] if s['name'] == 'Sprint'), rnd['raceStart']))
                rain, rain_src = (fc, 'forecast') if fc is not None else (config.RAIN_DEFAULT, 'default')
            actual = actual_gp if kind == 'gp' else (history.sprint_winner(season, int(rnd['round']), cached=bool(rnd['done']))
                                                    if rnd['done'] or now > rnd['raceStart'] - pd.Timedelta(days=1) else None)
            preds[kind] = prediction_block(rows, wm, lm, rain, rain_src, kind, actual, n_tr, temp, probs)
            gate['unlocked'] = True
            log(f'   {wid} {kind}: pick {preds[kind]["predictedWinner"]}, actual {actual}')

        # weather shown on the page for current / upcoming weekends
        forecast = None
        if is_current:
            fc = rain_forecast(rnd['lat'], rnd['long'], rnd['raceStart'])
            forecast = {'rainChance': fc if fc is not None else config.RAIN_DEFAULT,
                        'source': 'forecast' if fc is not None else 'default'}

        cards = driver_cards(meeting, season, not is_current, last_meeting) if (meeting or is_current) else {}
        if not cards and lineup:
            cards = lineup
        if not cards:   # seasons before OpenF1: names and team colours from the results, no photos
            cards = cards_from_results(hist[hist['race_id'] == rid])
        page = {
            'id': wid, 'season': season, 'round': int(rnd['round']), 'name': rnd['raceName'],
            'circuitId': rnd['circuitId'], 'circuitName': rnd['circuitName'], 'locality': rnd['locality'],
            'country': rnd['country'], 'raceStart': rnd['raceStart'], 'sprint': bool(rnd['sprint']),
            'status': status, 'sessions': sessions, 'gates': gates, 'track': track_file,
            'circuit': stats, 'forecast': forecast, 'drivers': cards,
            'prediction': preds, 'simulator': ctx.sim_card, 'model': {'name': ctx.best_name, 'window': ctx.window},
            'generatedAt': now,
        }
        write(config.OUT_DIR / 'weekends' / f'{wid}.json', page)
        gp = preds.get('gp')
        index_rows.append({'id': wid, 'round': int(rnd['round']), 'name': rnd['raceName'],
                           'locality': rnd['locality'], 'country': rnd['country'], 'circuitId': rnd['circuitId'],
                           'raceStart': rnd['raceStart'], 'sprint': bool(rnd['sprint']), 'status': status,
                           'track': track_file,
                           'predicted': gp['predictedWinner'] if gp else None,
                           'predictedWin': gp['results'][0]['win'] if gp else None,
                           'actual': actual_gp, 'hit': gp['hit'] if gp else None,
                           'actualWin': next((r['win'] for r in gp['results'] if r['code'] == actual_gp), None) if gp and actual_gp else None,
                           'actualGrid': next((r['qPos'] for r in gp['results'] if r['code'] == actual_gp), None) if gp and actual_gp else None,
                           'unlocked': bool(gp)})

    return index_rows


if __name__ == '__main__':
    main()

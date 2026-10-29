"""Self-learning: replay every weekend since 2023 the way the model lived through it.

For every race, each candidate setup (model type x recency weighting) is trained on the races before it
and its prediction is stored. The forecast is a weighted blend of all setups. After each race every
setup's weight is multiplied by the chance it gave the actual winner (raised to ETA), so setups that
got it wrong lose influence, then ALPHA of the weight is shared back out evenly so no setup is ever
written off ("fixed share" online learning). Replaying this over every race since 2023 gives
  - the prediction it would really have made for every past race (no hindsight),
  - an honest accuracy record for the learning itself,
  - a log of how its trust moved after each race.
Stored predictions are reused, so each new race costs one fit per setup.

ETA and ALPHA were chosen by replaying 79 races: any ETA from 0.2 to 0.5 with ALPHA 0.1 scored the same,
and picking a single "best" setup from recent races did worse than blending (it chases noise).
"""
import numpy as np
import pandas as pd

from . import config, model

STORE = config.STORE_DIR / 'walk_forward.csv'
ETA = 0.3             # how hard a miss is punished
ALPHA = 0.1           # share of weight spread back evenly after each race
MIN_PRIOR = 8         # races needed before the first prediction
COMBOS = [(k, hl) for k in model.CONFIGS for hl in model.HALF_LIVES]


def combo_id(key, hl):
    return f'{key}|{hl or 0}'


def parse(cid):
    key, hl = cid.split('|')
    return key, (int(hl) or None)


CIDS = [combo_id(*c) for c in COMBOS]
DEFAULT_ID = combo_id(*model.DEFAULT)


def label(cid):
    key, hl = parse(cid)
    return f'{model.CONFIGS[key][0]}, {model.CONFIGS[key][1]}'


def update_store(train_all, log):
    ids = np.sort(train_all['race_id'].unique())
    eligible = ids[MIN_PRIOR:]
    wf = pd.read_csv(STORE) if STORE.exists() else None
    have = set(zip(wf['race_id'], wf['combo'])) if wf is not None else set()
    todo = [(rid, c) for rid in eligible for c in COMBOS if (rid, combo_id(*c)) not in have]
    if todo:
        log(f'Self-learning: {len(todo)} new walk-forward fits ({len({r for r, _ in todo})} races)')
    new = []
    for n, (rid, (key, hl)) in enumerate(todo, 1):
        prior, race = train_all[train_all['race_id'] < rid], train_all[train_all['race_id'] == rid]
        m = model.fit_setup(key, hl, prior)
        new.append(pd.DataFrame({'race_id': rid, 'driverCode': race['driverCode'].values,
                                 'combo': combo_id(key, hl), 'p': m.predict_proba(race[model.FEATS])[:, 1]}))
        if n % 200 == 0 or n == len(todo):     # save as it goes, so a crash doesn't lose the fits
            log(f'   {n}/{len(todo)} fits')
            wf = pd.concat(([wf] if wf is not None else []) + new, ignore_index=True)
            wf.to_csv(STORE, index=False, float_format='%.6g')
            new = []
    return wf[wf['race_id'].isin(eligible)]


def _norm(raw):
    p = np.clip(np.asarray(raw, dtype=float), 1e-9, None)
    return p / p.sum()


def run(train_all, races, log=print):
    wf = update_store(train_all, log)
    winners = train_all.loc[train_all['win'] == 1].set_index('race_id')['driverCode']
    poles = train_all.loc[train_all['q_pos'] == 1].drop_duplicates('race_id').set_index('race_id')['driverCode']
    names = dict(zip(races['season'] * 100 + races['round'], races['raceName']))
    fixed = CIDS.index(DEFAULT_ID)

    by_race, history = {}, []
    w = np.ones(len(CIDS)) / len(CIDS)
    for rid, g in wf.groupby('race_id'):
        g = g.pivot(index='combo', columns='driverCode', values='p').reindex(CIDS)
        codes = list(g.columns)
        M = np.vstack([_norm(row) for row in g.values])
        p = w @ M
        win = winners.get(rid)
        k = codes.index(win) if win in codes else None
        pick = codes[int(np.argmax(p))]
        top = int(np.argmax(w))
        by_race[rid] = {'probs': dict(zip(codes, p)), 'combo': CIDS[top]}
        history.append({'raceId': int(rid), 'race': f"{names.get(rid, rid)} {rid // 100}",
                        'setup': label(CIDS[top]), 'halfLife': parse(CIDS[top])[1], 'trust': float(w[top]),
                        'picked': pick, 'pickWin': float(p.max()), 'winner': win,
                        'winnerP': float(p[k]) if k is not None else None, 'hit': bool(pick == win),
                        'fixedHit': bool(codes[int(np.argmax(M[fixed]))] == win),
                        'fixedWinnerP': float(M[fixed][k]) if k is not None else None,
                        'poleHit': bool(poles.get(rid) == win)})
        if k is not None:      # learn from this race before the next one
            w = w * np.clip(M[:, k], 1e-6, None) ** ETA
            w = (1 - ALPHA) * w / w.sum() + ALPHA / len(w)

    h = pd.DataFrame(history)

    def summary(d):
        return {'Self-learning model': {'topPickWon': d['hit'].mean(), 'avgPWinner': d['winnerP'].mean(),
                                        'logLoss': float(-np.log(d['winnerP'].clip(1e-6)).mean())},
                'Original fixed model': {'topPickWon': d['fixedHit'].mean(), 'avgPWinner': d['fixedWinnerP'].mean(),
                                         'logLoss': float(-np.log(d['fixedWinnerP'].clip(1e-6)).mean())},
                'Pole sitter wins': {'topPickWon': d['poleHit'].mean()}}

    recent = h.tail(config.TEST_RACES)
    eras = {'2023 on (practice + qualifying)': summary(h[h['raceId'] >= config.WEEKEND_FROM * 100]),
            'Before 2023 (qualifying only)': summary(h[h['raceId'] < config.WEEKEND_FROM * 100])}
    eras = {k: dict(v, races=int(((h['raceId'] >= config.WEEKEND_FROM * 100) == k.startswith('2023')).sum()))
            for k, v in eras.items()}
    calib = []
    for a, b in [(0, .45), (.45, .65), (.65, 1.01)]:
        d = h[(h['pickWin'] >= a) & (h['pickWin'] < b)]
        if len(d):
            calib.append({'said': d['pickWin'].mean(), 'won': d['hit'].mean(), 'races': len(d)})

    order = np.argsort(-w)
    trusted = [{'setup': label(CIDS[i]), 'halfLife': parse(CIDS[i])[1], 'weight': float(w[i])} for i in order[:4]]
    key, hl = parse(CIDS[order[0]])
    overall = summary(h)
    log(f'Self-learning: replayed {len(h)} races: learning {h["hit"].mean():.0%} '
        f'(log-loss {overall["Self-learning model"]["logLoss"]:.3f}), fixed {h["fixedHit"].mean():.0%} '
        f'(log-loss {overall["Original fixed model"]["logLoss"]:.3f}), pole {h["poleHit"].mean():.0%}; '
        f'most trusted now {CIDS[order[0]]} ({w[order[0]]:.0%})')
    return {
        'key': key, 'halfLife': hl, 'model': model.CONFIGS[key][0], 'detail': model.CONFIGS[key][1],
        'weights': dict(zip(CIDS, w)), 'trusted': trusted,
        'byRace': by_race, 'history': history, 'calibration': calib,
        'backtest': summary(recent), 'overall': overall, 'eras': eras, 'replayed': len(h),
        'firstRace': int(h['raceId'].iloc[0]),
        'window': {'races': int(len(recent)), 'from': int(recent['raceId'].iloc[0]), 'to': int(recent['raceId'].iloc[-1])},
        'tried': len(COMBOS), 'eta': ETA, 'alpha': ALPHA,
    }


def ensemble_probs(state, train_all, rows):
    """Live forecast: every setup trained on all finished races, blended with the learned weights."""
    out = np.zeros(len(rows))
    for cid, wt in state['weights'].items():
        if wt < 0.005:
            continue
        m = model.fit_setup(*parse(cid), train_all)
        out += wt * _norm(m.predict_proba(rows[model.FEATS])[:, 1])
    return dict(zip(rows['driverCode'], out / out.sum()))

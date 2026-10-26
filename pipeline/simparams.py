"""Parameters for the website's race simulator: a 0-1 rating per driver for each factor (1 = best in
the field), and default weights fitted on past weekends with a conditional logit."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

PARAMS = [
    ('grid', 'Grid position', 'Where they start, from the official qualifying order.'),
    ('quali_pace', 'One-lap pace', 'Gap to pole in qualifying.'),
    ('race_pace', 'Long-run pace', 'Median lap of their best 5+ lap run in practice.'),
    ('car', 'Car performance', "Team points over the last 5 races plus both cars' qualifying pace this weekend."),
    ('driver', 'Driver performance', 'Recent points and finishes, and qualifying head-to-head against the teammate.'),
    ('track_confidence', 'Track confidence', "The driver's average finish and podiums at this circuit."),
    ('track_form', 'Team track form', "The team's best finish here over its last 3 visits."),
    ('reliability', 'Reliability', 'Share of the last 10 races finished.'),
    ('racecraft', 'Racecraft', 'Average places gained from grid to flag over the last 10 races.'),
    ('wet_skill', 'Wet-weather skill', 'Places gained in wet races since 2023. Only counts when it rains.'),
]
KEYS = [k for k, _, _ in PARAMS]


def _norm(s, higher_better=True):
    s = s.astype(float)
    s = s.fillna(s.median() if s.notna().any() else 0)
    lo, hi = s.min(), s.max()
    if hi - lo < 1e-12:
        return pd.Series(0.5, index=s.index)
    r = (s - lo) / (hi - lo)
    return r if higher_better else 1 - r


def ratings(df):
    """df = one race weekend, one row per driver (form + weekend features). Returns ratings by key."""
    team_q = df.groupby('constructorId')['q_gap'].transform('mean')
    podium_rate = (df['track_podiums'] / df['track_starts'].replace(0, np.nan)).fillna(0)
    r = pd.DataFrame(index=df.index)
    r['grid'] = _norm(df['q_pos'], False)
    r['quali_pace'] = _norm(df['q_gap'], False)
    r['race_pace'] = _norm(df['fp_lr_gap'], False)
    r['car'] = 0.5 * _norm(df['team_form']) + 0.5 * _norm(team_q, False)
    r['driver'] = 0.4 * _norm(df['form_points']) + 0.3 * _norm(df['form_finish'], False) + 0.3 * _norm(df['h2h'])
    r['track_confidence'] = 0.6 * _norm(df['track_form'], False) + 0.4 * _norm(podium_rate)
    r['track_form'] = _norm(df['team_track'], False)
    r['reliability'] = _norm(df['dnf_rate'], False)
    r['racecraft'] = _norm(df['racecraft'])
    r['wet_skill'] = _norm(df['wet_skill'])
    return r[KEYS].round(4)


def raw_values(df):
    """Readable numbers shown next to each rating in the UI."""
    team_q = df.groupby('constructorId')['q_gap'].transform('mean')
    return pd.DataFrame({
        'grid': 'P' + df['q_pos'].astype(int).astype(str),
        'quali_pace': (df['q_gap'] * df['pole_time']).map(lambda v: 'pole' if v < 1e-6 else f'+{v:.3f} s'),
        'race_pace': (df['fp_lr_gap'] * df['fp_lr'].fillna(df['pole_time'])).map(
            lambda v: 'best' if v < 1e-6 else (f'+{v:.2f} s/lap' if pd.notna(v) else 'no long run')),
        'car': df['team_form'].map(lambda v: f'{v:.0f} pts/race') + ', team gap ' + (team_q * 100).map(lambda v: f'{v:.2f}%'),
        'driver': df['form_points'].map(lambda v: f'{v:.1f} pts/race') + ', beat teammate ' + (df['h2h'] * 100).map(lambda v: f'{v:.0f}%'),
        'track_confidence': np.where(df['track_starts'] > 0,
                                     'avg P' + df['track_form'].map(lambda v: f'{v:.1f}') + ', '
                                     + df['track_podiums'].astype(int).astype(str) + ' podiums',
                                     'first visit'),
        'track_form': 'best P' + df['team_track'].map(lambda v: f'{v:.1f}'),
        'reliability': ((1 - df['dnf_rate']) * 100).map(lambda v: f'{v:.0f}% finished'),
        'racecraft': df['racecraft'].map(lambda v: f'{v:+.1f} places/race'),
        'wet_skill': df['wet_skill'].map(lambda v: f'{v:+.1f} places in the wet'),
    }, index=df.index)


def fit_weights(train, wet_by_race):
    """Conditional logit: P(win) = softmax(ratings . w) within each race. Weights kept >= 0."""
    races = []
    for rid, d in train.groupby('race_id'):
        if d['win'].sum() != 1:
            continue
        R = ratings(d).values.copy()
        if not wet_by_race.get(rid, False):
            R[:, KEYS.index('wet_skill')] = 0
        races.append((R, int(np.flatnonzero(d['win'].values)[0])))

    def nll(w):
        loss, grad = 0.0, np.zeros_like(w)
        for R, win in races:
            u = R @ w
            u -= u.max()
            p = np.exp(u) / np.exp(u).sum()
            loss -= np.log(p[win] + 1e-12)
            grad -= R[win] - p @ R
        lam = 0.003
        return loss / len(races) + lam * w @ w, grad / len(races) + 2 * lam * w

    res = minimize(nll, np.ones(len(KEYS)), jac=True, method='L-BFGS-B', bounds=[(0, 15)] * len(KEYS))
    # every factor keeps a small minimum weight so each slider still does something by default
    w = pd.Series(res.x, index=KEYS).clip(lower=0.3).round(3)
    return w, float(res.fun), len(races)

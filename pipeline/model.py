"""Winner model: training, back-test, prediction and plain-language reasons (from old notebook cells 6-7)."""
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import config
from .history import FORM_FEATS
from .weekend import WEEKEND_FEATS

FEATS = FORM_FEATS + WEEKEND_FEATS


def candidates():
    return {
        'Logistic regression': make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=2000)),
        'Gradient boosting': GradientBoostingClassifier(n_estimators=150, max_depth=2, learning_rate=0.05,
                                                        random_state=config.SEED),
    }


def race_probs(model, df):
    p = pd.Series(model.predict_proba(df[FEATS])[:, 1], index=df.index)
    return p / p.groupby(df['race_id']).transform('sum')


def score(p, df):
    d = df.assign(p=p, rank=p.groupby(df['race_id']).rank(ascending=False, method='first'))
    w = d[d['win'] == 1]
    return {'topPickWon': float((w['rank'] == 1).mean()), 'winnerInTop3': float((w['rank'] <= 3).mean()),
            'avgPWinner': float(w['p'].mean()), 'logLoss': float(-np.log(w['p'].clip(1e-6)).mean())}


def backtest(train_all):
    """Hold out the last TEST_RACES weekends; compare both models with 'pole sitter wins'."""
    ids = np.sort(train_all['race_id'].unique())
    cut = ids[-config.TEST_RACES]
    tr, te = train_all[train_all['race_id'] < cut], train_all[train_all['race_id'] >= cut]
    results = {}
    for name, m in candidates().items():
        m.fit(tr[FEATS], tr['win'])
        results[name] = score(race_probs(m, te), te)
    won = te['win'] == 1
    pole = te['q_pos'].groupby(te['race_id']).rank(method='first')
    results['Pole sitter wins'] = {'topPickWon': float((pole[won] == 1).mean()),
                                   'winnerInTop3': float((pole[won] <= 3).mean())}
    best = min((n for n in results if 'logLoss' in results[n]), key=lambda n: results[n]['logLoss'])
    return best, results, {'races': int(te['race_id'].nunique()), 'from': int(cut), 'to': int(ids[-1])}


def fit(name, df):
    m = candidates()[name]
    m.fit(df[FEATS], df['win'])
    return m


def importances(model):
    est = model[-1] if hasattr(model, 'steps') else model
    imp = est.coef_[0] if hasattr(est, 'coef_') else est.feature_importances_
    return pd.Series(imp, index=FEATS)


def sample_orders(p, rain, n=config.N_SAMPLES, seed=config.SEED):
    """Plackett-Luce finishing orders via Gumbel noise; rain flattens the odds."""
    T = 1 + config.RAIN_CHAOS * rain
    rng = np.random.default_rng(seed)
    s = np.log(np.clip(p, 1e-9, None)) / T + rng.gumbel(size=(n, len(p)))
    pos = (-s).argsort(axis=1).argsort(axis=1)
    return (pos == 0).mean(axis=0), (pos < 3).mean(axis=0), pos.mean(axis=0) + 1


# ---------------- reasons ----------------
GROUPS = {
    'qualifying': ['q_pos', 'q_gap'],
    'practice': ['fp_gap', 'fp_lr_gap'],
    'form': ['form_finish', 'form_points', 'form_grid'],
    'car': ['team_form'],
    'championship': ['pts_share'],
    'track': ['track_form'],
    'reliability': ['dnf_rate'],
}
TITLES = {'qualifying': 'Qualifying', 'practice': 'Practice pace', 'form': 'Recent form', 'car': 'Car',
          'championship': 'Championship', 'track': 'Track record', 'reliability': 'Reliability'}


def _ord(n):
    n = int(round(n))
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _rank(df, col, ascending=True):
    return df[col].rank(ascending=ascending, method='min')


def describe(df, i, group):
    """One plain sentence about driver row `i` for a factor group."""
    r = df.loc[i]
    n = len(df)
    if group == 'qualifying':
        pos = int(r['q_pos'])
        if pos == 1:
            second = df.loc[df['q_pos'] == 2]
            margin = (second['q_gap'].iloc[0] * r['pole_time']) if len(second) else np.nan
            return 'On pole' + (f', {margin:.3f} s clear of P2' if pd.notna(margin) else '')
        return f"Starts P{pos}, {r['q_gap'] * r['pole_time']:.3f} s off pole"
    if group == 'practice':
        lr = _rank(df, 'fp_lr_gap')[i]
        sess = str(r.get('fp_session', 'practice')).replace('Practice ', 'FP')
        if lr == 1:
            return f'Best long-run pace in {sess}'
        gap = r['fp_lr_gap'] * r['fp_lr'] if pd.notna(r.get('fp_lr')) else np.nan
        return f'{_ord(lr)} on long-run pace in {sess}' + (f', {gap:.2f} s/lap off the best' if pd.notna(gap) else '')
    if group == 'form':
        return f"Averaging {r['form_points']:.1f} points and P{r['form_finish']:.1f} finishes over the last 5 races"
    if group == 'car':
        teams = df.drop_duplicates('constructorId')
        rk = teams['team_form'].rank(ascending=False, method='min')[teams['constructorId'] == r['constructorId']]
        best = 'the strongest team' if rk.iloc[0] == 1 else f'the {_ord(rk.iloc[0])}-strongest team'
        return f"{r['team']} has been {best} over the last 5 races ({r['team_form']:.0f} pts per race)"
    if group == 'championship':
        rk = _rank(df, 'pts_share', ascending=False)[i]
        return f"{_ord(rk)} in the championship coming into this weekend"
    if group == 'track':
        starts = int(r.get('track_starts', 0))
        if starts == 0:
            return 'No previous race at this circuit'
        wins, pods = int(r.get('track_wins', 0)), int(r.get('track_podiums', 0))
        extra = f', {wins} win{"s" * (wins != 1)}' if wins else (f', {pods} podium{"s" * (pods != 1)}' if pods else '')
        return f"Averages P{r['track_form']:.1f} here over {starts} start{'s' * (starts != 1)}{extra}"
    if group == 'reliability':
        return f"Finished {100 * (1 - r['dnf_rate']):.0f}% of the last 10 races"
    return ''


def reasons(df, lr_model):
    """Per-driver factor list: impact = LR coefficient x standardised distance from the field average."""
    scaler, lr = lr_model[0], lr_model[-1]
    z = (df[FEATS] - scaler.mean_) / scaler.scale_
    contrib = (z - z.mean()) * lr.coef_[0]
    out = {}
    for i in df.index:
        items = []
        for g, cols in GROUPS.items():
            impact = float(contrib.loc[i, cols].sum())
            items.append({'key': g, 'title': TITLES[g], 'impact': round(impact, 3), 'text': describe(df, i, g)})
        out[i] = sorted(items, key=lambda x: -x['impact'])
    return out

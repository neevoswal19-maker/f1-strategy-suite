#> ### 3.4 Lap pace projections per compound
#> Pace curve per compound for the strategy driver, kept non-decreasing with tyre age. A compound needs `MIN_COMPOUND_LAPS` clean laps to be used; the longest stint allowed is 1.1 × the longest one seen.
MAX_AGE    = TOTAL_LAPS + 5
TRACK_TEMP = clean['TrackTemp'].median()
counts     = clean['Compound'].value_counts()

AVAILABLE = [c for c in COMPOUNDS if counts[c] >= MIN_COMPOUND_LAPS]
if len(AVAILABLE) < 2:
    AVAILABLE = [c for c in COMPOUNDS if counts[c] >= 10] or [counts.idxmax()]
TWO_COMPOUND_RULE = len(AVAILABLE) >= 2
if not TWO_COMPOUND_RULE:
    print(f'Only {AVAILABLE[0]} has enough clean laps, so the two-compound rule is switched off for this race.')

MAX_STINT = {c: max(min(int(clean.loc[clean['Compound'] == c, 'TyreLife'].max() * 1.1), TOTAL_LAPS), MIN_STINT)
             for c in AVAILABLE}

ages = np.arange(1, MAX_AGE + 1)
PACE = {}
for c in AVAILABLE:
    grid = pd.DataFrame({'Driver': DRIVER_CODE, 'Compound': c,
                         'TyreLife': ages, 'TrackTemp': TRACK_TEMP})
    PACE[c] = np.maximum.accumulate(pace_model.predict(make_features(grid, FEATURES)))

CUM = {c: np.concatenate([[0.0], np.cumsum(PACE[c])]) for c in PACE}

deg_table = pd.DataFrame({
    'fresh_pace_s':  {c: PACE[c][0] for c in AVAILABLE},
    'deg_s_per_lap': {c: (PACE[c][MAX_STINT[c] - 1] - PACE[c][0]) / max(MAX_STINT[c] - 1, 1) for c in AVAILABLE},
    'max_stint':     MAX_STINT,
}).round(3)
print(deg_table.to_string())

fig, ax = plt.subplots(figsize=(10, 5))
for c in AVAILABLE:
    d = clean[clean['Compound'] == c]
    ax.scatter(d['TyreLife'], d['FuelCorrS'], s=8, alpha=0.25,
               color=COLORS[c], edgecolors='k', linewidths=0.2)
    ax.plot(ages[:MAX_STINT[c]], PACE[c][:MAX_STINT[c]], color=COLORS[c], lw=3,
            label=f'{c} (model)')
ax.set(xlabel='Tyre age (laps)', ylabel='Fuel-corrected lap time (s)',
       title=f'Projected lap pace for {DRIVER_CODE} - {RACE_TITLE}')
ax.legend()
plt.show()

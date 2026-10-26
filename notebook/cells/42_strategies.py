#> ### 4.2 Generate and rank every legal strategy
#> Every 1- and 2-stop plan with at least two dry compounds, stints of `MIN_STINT` laps or more and no stint longer than its compound allows. A quick deterministic ranking picks the best pit laps for each compound sequence; Monte Carlo then runs on those.
def generate_strategies(min_stint=MIN_STINT, max_stops=MAX_STOPS):
    out = []
    for stops in range(1, max_stops + 1):
        for comps in itertools.product(AVAILABLE, repeat=stops + 1):
            if TWO_COMPOUND_RULE and len(set(comps)) < 2:   # rule: two different dry compounds
                continue
            for pits in itertools.combinations(range(min_stint, TOTAL_LAPS - min_stint + 1), stops):
                lengths = np.diff([0, *pits, TOTAL_LAPS])
                if lengths.min() < min_stint:
                    continue
                if any(n > MAX_STINT[c] for c, n in zip(comps, lengths)):
                    continue
                out.append(list(zip(comps, lengths)))
    return out

def stint_time(c, n, start_age=0):
    return CUM[c][start_age + n] - CUM[c][start_age]

def race_time(strategy):
    return sum(stint_time(c, n) for c, n in strategy) + PIT_LOSS * (len(strategy) - 1)

def label(strategy):
    pits = np.cumsum([n for _, n in strategy])[:-1]
    return '-'.join(c[0] for c, _ in strategy) + ' | box L' + ', L'.join(map(str, pits))

strategies = generate_strategies()
while not strategies and min(MAX_STINT.values()) < TOTAL_LAPS:
    MAX_STINT = {c: min(int(n * 1.25) + 1, TOTAL_LAPS) for c, n in MAX_STINT.items()}
    print('No plan fits the observed stint lengths, stretching max stints to', MAX_STINT)
    strategies = generate_strategies()

det = pd.DataFrame({'strategy': strategies})
det['time']  = det['strategy'].apply(race_time)
det['seq']   = det['strategy'].apply(lambda s: '-'.join(c[0] for c, _ in s))
det['label'] = det['strategy'].apply(label)

best_per_seq = det.loc[det.groupby('seq')['time'].idxmin()].sort_values('time')
best_per_seq['gap_s'] = best_per_seq['time'] - best_per_seq['time'].min()

print(f'{len(det):,} strategies evaluated')
print(best_per_seq[['label', 'gap_s']].head(10).round(2).to_string(index=False))

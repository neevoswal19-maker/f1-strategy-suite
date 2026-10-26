#> ### 5.4 Optimal pit windows
#> For each stop of the recommended plan, moves that pit lap up to `WINDOW_SPAN` laps either way and takes the Monte Carlo mean. The window is every lap within `WINDOW_TOL` seconds of the best.
def with_pits(comps, pits):
    return list(zip(comps, np.diff([0, *pits, TOTAL_LAPS])))

def feasible(strategy, min_stint=MIN_STINT):
    return all(min_stint <= n <= MAX_STINT[c] for c, n in strategy)

comps     = [c for c, _ in BEST]
best_pits = [int(p) for p in np.cumsum([n for _, n in BEST])[:-1]]

fig, ax = plt.subplots(figsize=(10, 5))
for i, p0 in enumerate(best_pits):
    xs, ys = [], []
    for p in range(p0 - WINDOW_SPAN, p0 + WINDOW_SPAN + 1):
        trial = best_pits.copy()
        trial[i] = p
        s = with_pits(comps, trial)
        if feasible(s):
            xs.append(p)
            ys.append(monte_carlo(s, S).mean())
    if not xs:
        print(f'Stop {i + 1}: no feasible alternative laps')
        continue
    xs, ys = np.array(xs), np.array(ys) - min(ys)
    window = xs[ys <= WINDOW_TOL]
    line, = ax.plot(xs, ys, marker='o', label=f'Stop {i + 1}')
    ax.axvspan(window.min(), window.max(), color=line.get_color(), alpha=0.15)
    print(f'Stop {i + 1}: ideal lap {xs[ys.argmin()]} | window L{window.min()}-L{window.max()}')

ax.set(xlabel='Pit lap', ylabel='Expected time lost (s)',
       title=f"Pit windows: {top.loc[0, 'label']} - {RACE_TITLE}")
ax.legend()
plt.show()

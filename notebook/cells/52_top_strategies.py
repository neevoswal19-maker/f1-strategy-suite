#> ### 5.2 Simulate the top strategies
#> The best plan for each of the top 6 compound sequences, raced `N_SIMS` times. `regret_p95_s` is the time lost to the best plan in the worst 5% of races; `p_fastest` is how often the plan was the quickest one.
top  = best_per_seq.head(6).reset_index(drop=True)
sims = np.vstack([monte_carlo(s, S) for s in top['strategy']])

order = np.argsort(sims.mean(axis=1))
top, sims = top.iloc[order].reset_index(drop=True), sims[order]

regret  = sims - sims.min(axis=0)
fastest = np.bincount(sims.argmin(axis=0), minlength=len(top)) / N_SIMS

mc = pd.DataFrame({
    'strategy':     top['label'],
    'mean_gap_s':   sims.mean(axis=1) - sims.mean(axis=1).min(),
    'regret_p95_s': np.percentile(regret, 95, axis=1),
    'p_fastest':    fastest,
}).round(2)
print(mc.to_string(index=False))

BEST = top.loc[0, 'strategy']
print(f"\nRECOMMENDED for {DRIVER_CODE} at {RACE_TITLE}: {top.loc[0, 'label']}")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].boxplot(regret.T, showfliers=False)
axes[0].set_xticks(range(1, len(top) + 1), top['label'], rotation=30, ha='right')
axes[0].set(ylabel='Time lost vs best plan in that race (s)', title='Strategy risk')
axes[1].barh(top['label'][::-1], fastest[::-1], color='tab:red')
axes[1].set(xlabel='Share of races where this plan was fastest', title=f'Fastest plan over {N_SIMS} simulated races')
plt.tight_layout()
plt.show()

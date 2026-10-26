#> ### 5.3 Dry vs wet breakdown and a wet race replay
rain = S['rain']
for name, mask in [('DRY races', ~rain), ('WET races', rain)]:
    if mask.sum() == 0:
        print(f'\n{name}: none in this run')
        continue
    part = sims[:, mask]
    print(f'\n{name}: {mask.sum()} simulations')
    print(pd.DataFrame({
        'strategy':   top['label'],
        'mean_gap_s': part.mean(axis=1) - part.mean(axis=1).min(),
        'p_fastest':  np.bincount(part.argmin(axis=0), minlength=len(top)) / mask.sum(),
    }).round(2).to_string(index=False))

heavy = np.flatnonzero(rain & (S['wet'].max(axis=1) > 0.5))
if len(heavy):
    i, trace = heavy[0], []
    wet_race(BEST, S, i, trace)
    fig, ax = plt.subplots(figsize=(12, 3.5))
    ax.plot(np.arange(TOTAL_LAPS) + 0.5, S['wet'][i], color='tab:blue', lw=2, label='Track wetness')
    for lap, tyre in enumerate(trace, 1):
        ax.axvspan(lap - 1, lap, ymax=0.1, color=COLORS[tyre])
    ax.set(xlabel='Lap', ylabel='Wetness', ylim=(0, 1.05),
           title=f'One simulated wet race: tyre used each lap (bottom strip) - {RACE_TITLE}')
    ax.legend()
    plt.show()
else:
    print('\nNo heavy-rain race in this run to replay (raise RAIN_DEFAULT in 1.3 to see one).')

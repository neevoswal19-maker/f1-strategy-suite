#> ### 7.2 Real strategies vs the simulator's pick
#> Stint bars for each driver in finishing order, with the simulator's recommended plan as the hatched `SIM` row on top.
if stints is None or stints.empty:
    print('No real stints to plot (see 7.1).')
else:
    order = race.results.sort_values('Position')['Abbreviation'].tolist()
    fig, ax = plt.subplots(figsize=(12, 8))
    for _, s in stints.iterrows():
        if s['name_acronym'] in order:
            ax.barh(order.index(s['name_acronym']), s['lap_end'] - s['lap_start'] + 1,
                    left=s['lap_start'] - 1, color=COLORS.get(s['compound'], 'grey'), edgecolor='black')
    left = 0
    for c, n in BEST:
        ax.barh(-1.5, n, left=left, color=COLORS[c], edgecolor='black', hatch='//')
        left += n
    ax.set_yticks([-1.5] + list(range(len(order))), ['SIM'] + order)
    ax.invert_yaxis()
    ax.set(xlabel='Lap', title=f'Real {DATA_YEAR} strategies vs simulator pick for {RACE_TITLE}')
    plt.show()

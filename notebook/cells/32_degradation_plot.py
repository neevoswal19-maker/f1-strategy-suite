#> ### 3.2 Exploratory plot: tyre degradation
fig, ax = plt.subplots(figsize=(10, 5))
for c in DRY:
    d = clean[clean['Compound'] == c]
    if len(d):
        ax.scatter(d['TyreLife'], d['FuelCorrS'], s=10, alpha=0.4,
                   color=COLORS[c], edgecolors='k', linewidths=0.2, label=c)
ax.set(xlabel='Tyre age (laps)', ylabel='Fuel-corrected lap time (s)',
       title=f'Tyre degradation by compound - {session.name} {session.year}')
ax.legend()
plt.show()

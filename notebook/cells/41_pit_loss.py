#> # 4. Strategy search
#> ### 4.1 Pit-loss estimate
#> Pit loss = in-lap + out-lap minus twice the driver's median green lap, over every green-flag stop in the race. Safety-car and slow-stop settings are in 1.3.
def estimate_pit_loss(laps):
    losses = []
    for drv, d in laps.groupby('Driver'):
        d = d.set_index('LapNumber')
        d = d[~d.index.duplicated()]
        ref = d.loc[d['Green'] & ~d['PitIn'] & ~d['PitOut'], 'LapTimeS'].median()
        for lap in d.index[d['PitIn']]:
            if lap + 1 in d.index and d.loc[lap + 1, 'PitOut']:
                pair = d.loc[[lap, lap + 1]]
                if pair['Green'].all():
                    losses.append(pair['LapTimeS'].sum() - 2 * ref)
    losses = pd.Series(losses, dtype=float)
    losses = losses[(losses > 10) & (losses < 40)]
    if len(losses) < 3:
        return DEFAULT_PIT_LOSS, 1.0
    return losses.median(), min(losses.std(), 2.0)

PIT_LOSS, PIT_SD = estimate_pit_loss(laps)
SC_LAP_TIME = SC_SLOWDOWN * clean['LapTimeS'].median()
print(f'Pit loss: {PIT_LOSS:.1f} s  (sd {PIT_SD:.1f} s) | safety-car lap: {SC_LAP_TIME:.1f} s')

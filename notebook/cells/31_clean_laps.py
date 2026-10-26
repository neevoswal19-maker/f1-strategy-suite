#> # 3. Tyre pace model
#> ### 3.1 Clean laps, fuel correction, track temperature
#> Keeps green-flag laps without pit stops, within 107% of the fastest lap, on dry compounds, and drops lap 1.
fastest = laps['LapTimeS'].min()
clean = laps[~laps['PitIn'] & ~laps['PitOut'] & laps['Green'] &
             (laps['LapTimeS'] <= 1.07 * fastest) & (laps['LapNumber'] > 1) &
             laps['Compound'].isin(DRY)]
clean = clean.dropna(subset=['LapTimeS', 'TyreLife', 'LapStart']).copy()

# remove the effect of fuel weight so only tyre wear is left
clean['FuelCorrS'] = clean['LapTimeS'] - FUEL_K * (TOTAL_LAPS - clean['LapNumber'])

# attach track temperature at the start of each lap
weather = session.weather[['Time', 'TrackTemp']].dropna().sort_values('Time')
clean = pd.merge_asof(clean.sort_values('LapStart'), weather,
                      left_on='LapStart', right_on='Time', direction='nearest')
clean['TrackTemp'] = clean['TrackTemp'].fillna(weather['TrackTemp'].median())

print(len(clean), 'clean green-flag laps')
print(clean['Compound'].value_counts().to_string())

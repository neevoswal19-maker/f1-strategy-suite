#> ### 2.3 Rain chance: forecast or what-if
#> Upcoming race: Open-Meteo forecast for the race window (16 days ahead at most). Past wet race: rain in every simulated race. Past dry race: a what-if `RAIN_DEFAULT`.
if UPCOMING:
    P_RAIN = None
    try:
        lat, lon = float(event['lat']), float(event['long'])
        if np.isnan(lat):
            lat, lon = geocode(event['Location'])
        P_RAIN = rain_forecast(lat, lon, race_utc)
    except Exception:
        P_RAIN = None
    if P_RAIN is None:
        P_RAIN = RAIN_DEFAULT
        print(f'No forecast yet (race more than 16 days away or lookup failed). Using a {P_RAIN:.0%} rain chance.')
    else:
        print(f"Forecast: {P_RAIN:.0%} chance of rain during the race at {event['Location']}")
elif WAS_WET:
    P_RAIN = 1.0
    print('This race was WET in real life, so every simulated race gets rain.')
else:
    P_RAIN = RAIN_DEFAULT
    print(f'This race was dry. Simulating a {P_RAIN:.0%} what-if chance of rain.')

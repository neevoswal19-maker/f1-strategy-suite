#> ### 6.2 Wet tyre crossovers and the rain call
#> With the default `GRIP` numbers, slicks are quickest below about 0.21 wetness, intermediates from 0.21 to 0.5, and full wets above that. `rain_call(lap, tyre, wetness, under_sc)` decides whether a tyre change pays for itself over the next `LOOKAHEAD` laps.
w = np.linspace(0, 1, 101)
fig, ax = plt.subplots(figsize=(9, 4))
for k, col in enumerate(['#DA291C', COLORS['INTERMEDIATE'], COLORS['WET']]):
    ax.plot(w, (mult(k, w) - 1) * 100, lw=3, color=col, label=TYPES[k])
ax.set(xlabel='Track wetness (0 = dry, 1 = soaked)', ylabel='% slower than dry pace',
       title='Tyre crossover points')
ax.legend()
plt.show()

def rain_call(lap, tyre, wetness, under_sc=False):
    lap  = int(min(max(lap, 1), TOTAL_LAPS))
    left = TOTAL_LAPS - lap
    ref  = DRY_REF + FUEL[lap - 1]
    pace = [ref * mult(k, wetness) for k in range(3)]
    k, b = kind(tyre), int(np.argmin(pace))
    cost = PIT_LOSS * (SC_PIT_FACTOR if under_sc else 1.0)
    gain = (pace[k] - pace[b]) * min(left, LOOKAHEAD)
    print(f"Lap {lap}/{TOTAL_LAPS} | on {tyre} | wetness {wetness:.2f} | {'SAFETY CAR' if under_sc else 'racing'}")
    for j in range(3):
        print(f'   {TYPES[j]:13s} {pace[j]:7.2f} s/lap')
    if b != k and gain > cost:
        new = best_slick(left) if b == 0 else TYPES[b]
        print(f'   >>> CALL: BOX BOX BOX for {new}  (gain {gain:.1f} s > pit cost {cost:.1f} s)\n')
    else:
        print(f'   >>> CALL: STAY OUT  (gain {gain:.1f} s vs pit cost {cost:.1f} s)\n')

L = TOTAL_LAPS
rain_call(lap=round(L * 0.3), tyre=first, wetness=0.15)
rain_call(lap=round(L * 0.3), tyre=first, wetness=0.45)
rain_call(lap=round(L * 0.5), tyre='INTERMEDIATE', wetness=0.85)
rain_call(lap=round(L * 0.75), tyre='INTERMEDIATE', wetness=0.0)

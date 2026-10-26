#> # 6. Pit wall
#> ### 6.1 Dry pit-wall call: box now or stay out?
#> `pit_wall_call(lap, compound, tyre_age, used, under_sc)` searches every way to finish the race (up to 2 more stops) and compares boxing now with staying out. Try your own situations at the bottom of the cell.
NEED_COMPOUNDS = 2 if TWO_COMPOUND_RULE else 1

def finish(R, c, age, used, stops):
    best = (np.inf, [])
    if len(used) >= NEED_COMPOUNDS and age + R <= MAX_STINT[c]:
        best = (stint_time(c, R, age), [(c, R)])
    if stops > 0:
        for k in range(1, R):
            if age + k > MAX_STINT[c]:
                break
            for new in AVAILABLE:
                t, plan = finish(R - k, new, 0, used | {new}, stops - 1)
                t += stint_time(c, k, age) + PIT_LOSS
                if t < best[0]:
                    best = (t, [(c, k)] + plan)
    return best

def describe(plan, lap):
    out = []
    for c, n in plan:
        lap += n
        out.append(f'{c[0]} to L{lap}')
    return ', '.join(out) or 'no legal plan'

def pit_wall_call(lap, compound, tyre_age, used=(), under_sc=False, max_stops=2):
    if compound not in AVAILABLE:
        print(f'No pace model for {compound}. Pick one of {AVAILABLE}.')
        return
    used = set(used) | {compound}
    R = TOTAL_LAPS - lap
    box_cost = PIT_LOSS * (SC_PIT_FACTOR if under_sc else 1.0)

    box = (np.inf, [])
    for new in AVAILABLE:
        t, plan = finish(R, new, 0, used | {new}, max_stops - 1)
        if t + box_cost < box[0]:
            box = (t + box_cost, plan)
    stay = finish(R, compound, tyre_age, used, max_stops)

    best = min(box[0], stay[0])
    print(f"Lap {lap}/{TOTAL_LAPS} | {compound} age {tyre_age} | {'SAFETY CAR' if under_sc else 'green flag'}")
    if not np.isfinite(best):
        print('   no legal way to finish from here\n')
        return
    for name, (t, plan) in [('BOX NOW ', box), ('STAY OUT', stay)]:
        gap = f'{t - best:+6.1f} s' if np.isfinite(t) else '   n/a'
        print(f'   {name}: {describe(plan, lap):32s} {gap}')
    print('   >>> CALL:', 'BOX BOX BOX' if box[0] <= stay[0] else 'STAY OUT', '\n')

# example calls built around the recommended plan
first, stop1 = BEST[0][0], best_pits[0]
early = max(MIN_STINT, stop1 - 4)
pit_wall_call(lap=early, compound=first, tyre_age=early)
pit_wall_call(lap=early, compound=first, tyre_age=early, under_sc=True)
pit_wall_call(lap=max(MIN_STINT, stop1 // 2), compound=first, tyre_age=max(MIN_STINT, stop1 // 2), under_sc=True)

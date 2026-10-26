#> # 5. Monte Carlo
#> ### 5.1 Monte Carlo engine (dry + wet)
#> Every strategy faces the same random races (lap noise, safety cars, wear uncertainty, pit-stop noise, slow stops, rain), so differences between strategies are low-noise. Dry races run vectorised; wet races run lap by lap with reactive weather calls. With no rain the wet engine gives exactly the dry result.
FUEL    = FUEL_K * (TOTAL_LAPS - np.arange(1, TOTAL_LAPS + 1))
DRY_REF = min(PACE[c][0] for c in AVAILABLE)

def kind(tyre):
    return 0 if tyre in DRY else TYPES.index(tyre)

def mult(k, w):
    a, b = GRIP[TYPES[k]]
    return a + b * w

def best_slick(R):
    ok = [c for c in AVAILABLE if MAX_STINT[c] >= R]
    return min(ok, key=lambda c: stint_time(c, R)) if ok else max(AVAILABLE, key=MAX_STINT.get)

def make_scenarios(n=N_SIMS, seed=SEED):
    rng = np.random.default_rng(seed)
    t = np.arange(TOTAL_LAPS)[None, :]

    rain  = rng.random(n) < P_RAIN
    onset = rng.integers(1, max(TOTAL_LAPS - 5, 2), n)[:, None]
    dur   = rng.integers(5, 25, n)[:, None]
    peak  = rng.uniform(0.15, 1.0, n)[:, None]
    rise  = np.clip((t - onset + 1) / 2, 0, 1)
    dry   = np.clip(1 - (t - onset - dur) / DRYING_LAPS, 0, 1)
    wet   = peak * np.minimum(rise, dry) * rain[:, None]

    hazard = 1 - (1 - P_SC) ** (1 / TOTAL_LAPS)
    start = rng.random((n, TOTAL_LAPS)) < hazard * (1 + 5 * wet)   # rain = more safety cars
    sc = np.zeros_like(start)
    for k in range(SC_LAPS):
        sc[:, k:] |= start[:, :TOTAL_LAPS - k]

    M = np.stack([mult(k, wet) for k in range(3)])
    return {
        'rain': rain, 'wet': wet, 'mult': M, 'best': M.argmin(axis=0), 'sc': sc,
        'noise':     rng.normal(0, LAP_NOISE, (n, TOTAL_LAPS)),
        'deg_mult':  rng.normal(1, DEG_UNCERT, n).clip(0.5, 1.5),
        'pit_noise': rng.normal(0, PIT_SD, (n, TOTAL_LAPS)),
        'slow_stop': rng.random((n, TOTAL_LAPS)) < P_SLOW_STOP,
    }

def lap_profile(strategy):
    base, deg = [], []
    for c, n in strategy:
        p = PACE[c][:n]
        base.append(np.full(n, p[0]))
        deg.append(p - p[0])
    pit_laps = np.cumsum([n for _, n in strategy])[:-1] - 1
    return np.concatenate(base), np.concatenate(deg), pit_laps

def dry_races(strategy, S, idx):
    base, deg, pit_laps = lap_profile(strategy)
    sc = S['sc'][idx]
    lap_t = base + FUEL + deg * S['deg_mult'][idx][:, None] + S['noise'][idx]
    lap_t = np.where(sc, SC_LAP_TIME, lap_t)
    total = lap_t.sum(axis=1)
    for p in pit_laps:
        loss = PIT_LOSS + S['pit_noise'][idx, p] + SLOW_STOP_S * S['slow_stop'][idx, p]
        total += np.where(sc[:, p], loss * SC_PIT_FACTOR, loss)
    return total

def wet_race(strategy, S, i, trace=None):
    plan = [c for c, _ in strategy]
    pits = {int(p) for p in np.cumsum([n for _, n in strategy])[:-1]}
    tyre, age, stint, on_plan, total = plan[0], 0, 0, True, 0.0
    M, best = S['mult'][:, i], S['best'][i]

    for t in range(TOTAL_LAPS):
        lap, k, sc = t + 1, kind(tyre), S['sc'][i, t]
        dry_lap = DRY_REF + FUEL[t]
        if tyre in DRY:
            p = PACE[tyre]
            dry_lap = p[0] + (p[min(age, len(p) - 1)] - p[0]) * S['deg_mult'][i] + FUEL[t]
        total += SC_LAP_TIME if sc else dry_lap * M[k, t] + S['noise'][i, t]
        if trace is not None:
            trace.append(tyre)
        age += 1
        left = TOTAL_LAPS - lap
        if left == 0:
            break

        factor = SC_PIT_FACTOR if sc else 1.0
        b = best[t]
        gain = (DRY_REF + FUEL[t]) * (M[k, t] - M[b, t]) * min(left, LOOKAHEAD)
        new = None
        if k != b and gain > PIT_LOSS * factor:                         # weather call
            new = best_slick(left) if b == 0 else TYPES[b]
            on_plan = False
        elif on_plan and lap in pits:                                   # planned dry stop
            stint += 1
            new = plan[stint]
        elif tyre in DRY and not on_plan and age >= MAX_STINT[tyre]:    # slicks worn out
            new = best_slick(left)

        if new:
            total += (PIT_LOSS + S['pit_noise'][i, t] + SLOW_STOP_S * S['slow_stop'][i, t]) * factor
            tyre, age = new, 0
    return total

def monte_carlo(strategy, S):
    total = np.empty(len(S['rain']))
    dry = ~S['rain']
    if dry.any():
        total[dry] = dry_races(strategy, S, dry)
    for i in np.flatnonzero(S['rain']):
        total[i] = wet_race(strategy, S, i)
    return total

S = make_scenarios()
print(f"Simulated races with rain: {S['rain'].mean():.0%} | with a safety car: {S['sc'].any(axis=1).mean():.0%}")

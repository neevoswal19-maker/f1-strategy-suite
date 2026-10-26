#> ### 1.3 Settings
#> Every number the simulator assumes, in one place. Change any of them and **Run all** again.
# --- simulation ---
N_SIMS = 2000            # Monte Carlo races per strategy (more = smoother, slower)
SEED   = 42
FUEL_K = 0.06            # seconds gained per lap as fuel burns off

# --- tyres ---
DRY    = ['SOFT', 'MEDIUM', 'HARD']
COLORS = {'SOFT': '#DA291C', 'MEDIUM': '#FFD12E', 'HARD': '#EBEBEB',
          'INTERMEDIATE': '#43B02A', 'WET': '#0067AD'}
MIN_COMPOUND_LAPS = 30   # clean laps a compound needs before we trust its pace curve

# --- strategy rules ---
MIN_STINT = 5            # shortest stint allowed (laps)
MAX_STOPS = 2            # most pit stops to consider

# --- pit stops and safety cars ---
DEFAULT_PIT_LOSS = 22.0  # used when the race has too few clean stops to measure it
P_SC          = 0.5      # chance of at least one safety car (raise to ~0.8 for street circuits)
SC_LAPS       = 4        # laps each safety car lasts
SC_SLOWDOWN   = 1.4      # safety-car lap = 1.4 x a normal lap
SC_PIT_FACTOR = 0.5      # a stop under the safety car costs about half
P_SLOW_STOP   = 0.05     # chance of a slow stop
SLOW_STOP_S   = 3.0      # extra time lost in a slow stop
DEG_UNCERT    = 0.15     # +/-15% uncertainty in tyre wear

# --- weather ---
RAIN_DEFAULT   = 0.15    # what-if rain chance when there is no forecast
WET_RACE_SHARE = 0.4     # above this share of wet-tyre laps, learn slick pace from another race
TYPES       = ['SLICK', 'INTERMEDIATE', 'WET']
GRIP        = {'SLICK': (1.00, 0.45), 'INTERMEDIATE': (1.06, 0.16), 'WET': (1.12, 0.04)}  # lap = dry pace x (a + b x wetness)
DRYING_LAPS = 8          # laps for the track to dry once the rain stops
LOOKAHEAD   = 5          # laps ahead the team considers when making a weather call

# --- pit windows ---
WINDOW_TOL  = 1.0        # pit laps within 1 s of the best count as the window
WINDOW_SPAN = 10         # how far either side of the ideal lap to test

# --- history ---
LOOKBACK_SEASONS = 3     # seasons searched for an earlier race at the same circuit

SITE_URL = 'https://neevoswal19-maker.github.io/f1-strategy-suite/'

"""Settings for the winner-prediction pipeline."""
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = Path(os.environ.get('PIPELINE_CACHE', ROOT / '.cache' / 'pipeline'))
STORE_DIR = ROOT / 'pipeline' / 'store'
OUT_DIR = Path(os.environ.get('PIPELINE_OUT', ROOT / 'web' / 'public' / 'data'))

JOLPICA = 'https://api.jolpi.ca/ergast/f1'
OPENF1 = 'https://api.openf1.org/v1'
MULTIVIEWER = 'https://api.multiviewer.app/api/v1'
OPEN_METEO = 'https://api.open-meteo.com/v1/forecast'

HISTORY_FROM = 2019      # race results used for form and circuit history
WEEKEND_FROM = 2023      # OpenF1 practice/qualifying data starts here
TEST_RACES = 12          # most recent weekends held back to back-test the winner model
RAIN_DEFAULT = 0.15      # rain chance when there is no forecast
RAIN_CHAOS = 0.6         # how much rain flattens the odds
N_SAMPLES = 20000        # simulated finishing orders for win / podium %
UNLOCK_AFTER = pd.Timedelta(minutes=30)   # after the qualifying session ends
SEED = 42

QUALI = ['Qualifying']
SPRINT_QUALI = ['Sprint Qualifying', 'Sprint Shootout']
GP_PRACTICE = ['Practice 2', 'Practice 1', 'Practice 3']
SPRINT_PRACTICE = ['Practice 1']


def now():
    """Current UTC time (naive). Set F1_NOW=2026-10-31T23:00 to test the unlock gate."""
    if os.environ.get('F1_NOW'):
        return pd.Timestamp(os.environ['F1_NOW']).tz_localize(None)
    return pd.Timestamp.now(tz='UTC').tz_localize(None)

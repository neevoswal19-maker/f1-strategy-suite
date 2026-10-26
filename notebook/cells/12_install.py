#> ### 1.2 Install and import
%pip install -q "fastf1>=3.9,<4"

import os, sys, time, itertools, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
import requests_cache
import fastf1
from fastf1.ergast import Ergast

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.metrics import mean_absolute_error, r2_score

warnings.filterwarnings('ignore')
fastf1.set_log_level('ERROR')

IN_COLAB = 'google.colab' in sys.modules
if IN_COLAB and SAVE_CACHE_TO_DRIVE:
    from google.colab import drive
    drive.mount('/content/drive')
    CACHE_DIR = '/content/drive/MyDrive/f1_cache'
elif IN_COLAB:
    CACHE_DIR = '/content/f1_cache'
else:
    CACHE_DIR = os.environ.get('F1_CACHE_DIR', os.path.abspath('f1_cache'))
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

# FastF1 3.9+ asks for an F1 TV login before live-timing downloads. This notebook doesn't need one
# (see 1.4), so turn the login prompt off unless you have set F1_USERNAME and F1_PASSWORD yourself.
try:
    from fastf1.internals.f1account import login as _f1_login
    from fastf1.exceptions import F1AuthError
    if not (os.environ.get('F1_USERNAME') and os.environ.get('F1_PASSWORD')):
        def _no_login():
            raise F1AuthError('no F1 account configured')
        _f1_login._credentials_from_env_or_prompt = _no_login
except ImportError:
    pass
print(f'FastF1 {fastf1.__version__} | cache: {CACHE_DIR}')

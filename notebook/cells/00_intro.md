# F1 Strategy Intelligence Suite: Strategy & Pit-Wall Simulation

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/neevoswal19-maker/f1-strategy-suite/blob/main/notebook/F1_Strategy_Intelligence_Suite.ipynb)

Models optimal pit windows and tyre strategies with **Monte Carlo simulation** and **ML lap-pace projections**, for past and upcoming races, dry or wet.

**Stack:** Python, NumPy, Pandas, Scikit-learn, FastF1, Ergast (Jolpica), OpenF1 API, Open-Meteo (rain forecast)

**How to run**
1. Pick a season, a race and (optionally) a driver in the form in **1.1**.
2. **Runtime → Run all.** Nothing asks for input after that.
3. To try another race, change the form and use **Runtime → Run all** again. Downloads are cached, so later runs are faster.

**Pipeline**

| Part | What happens |
|---|---|
| 1. Setup | your choices, installs, every setting in one place, helper functions |
| 2. The race | calendar, race data (with a dry-pace fallback for wet races), rain chance |
| 3. Tyre pace model | lap cleaning, degradation plot, Ridge vs Random Forest, pace projections |
| 4. Strategy search | pit loss, every legal 1- and 2-stop strategy ranked |
| 5. Monte Carlo | dry + wet race engine, top strategies, dry vs wet breakdown, pit windows |
| 6. Pit wall | "box now or stay out?" calls, wet tyre crossovers |
| 7. Real world | real strategies from OpenF1 vs the simulator's pick |
| 8. Race winner | the winner prediction lives on the project website |

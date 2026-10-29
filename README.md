# F1 Strategy Intelligence Suite

Two parts:

| Part | What it does | Where |
|---|---|---|
| **Strategy notebook** | Tyre-pace model, every legal 1- and 2-stop strategy, Monte Carlo races (dry and wet), pit windows, "box or stay out?" calls, real strategies compared with the simulator | [Open in Colab](https://colab.research.google.com/github/neevoswal19-maker/f1-strategy-suite/blob/main/notebook/F1_Strategy_Intelligence_Suite.ipynb) |
| **Pit Wall website** | Predicted Grand Prix and sprint winners once qualifying is over, with win chances, the reasons behind the pick, and a race simulator you can tune | https://neevoswal19-maker.github.io/f1-strategy-suite/ |

## Repository layout

```
notebook/
  cells/                 one file per notebook cell (edit these)
  build_notebook.py      cells/ -> F1_Strategy_Intelligence_Suite.ipynb
pipeline/                winner model and the website's data (runs in GitHub Actions)
  build.py               entry point: python -m pipeline.build
  history.py             race results and driver form (Jolpica / Ergast)
  weekend.py             practice + qualifying features from OpenF1, cached in store/
  model.py               the 18 model setups (logistic regression, gradient boosting, recency weighting), reasons
  learning.py            self-learning: replays every race since 2019 and re-weights the setups after each one
  simparams.py           the simulator's ten factors and their fitted weights
  tracks.py              circuit outlines (MultiViewer)
web/                     the website (Vite + React + TypeScript + Tailwind)
  public/data/           JSON written by the pipeline
.github/workflows/site.yml   refreshes data (every 20 min on race weekends) and deploys GitHub Pages
docs/                    the original project handoff
```

## Data sources

- **OpenF1**: laps, stints, weather, race control, results, drivers and photos (2023 onwards, free).
- **Jolpica qualifying times** stand in for 2019-2022, when there is no free practice data, so the model trains and is tested on every race since 2019.
- **Jolpica (Ergast)**: race results and the calendar.
- **FastF1**: calendar in the notebook, and lap data for 2018-2022 from its free archive. Since 2026 FastF1 needs a paid F1 TV login for newer live-timing data, so the notebook reads 2023+ laps from OpenF1 instead.
- **Open-Meteo**: rain forecast. **MultiViewer**: track layouts.

## Running things locally

```bash
python -m venv .venv && .venv/Scripts/pip install -r pipeline/requirements.txt fastf1 nbformat
python notebook/build_notebook.py          # rebuild the .ipynb after editing cells/
python -m pipeline.build                   # refresh web/public/data
cd web && npm install && npm run dev       # site on http://localhost:5173/f1-strategy-suite/
```

`F1_NOW=2026-10-31T22:30 python -m pipeline.build` pretends it is another time, which is handy for checking that predictions unlock after qualifying.

Unofficial fan project, not associated with Formula 1 or the FIA.

"""Circuit outlines for the website, from the MultiViewer API (rotated the way TV graphics show them)."""
import json

import numpy as np

from . import config
import pandas as pd

from .sources import circuit_info, get_json, openf1

SIZE = 1000   # outline fits a SIZE x SIZE box, y pointing down (SVG)


def _rotate(xy, deg):
    a = np.deg2rad(deg)
    return xy @ np.array([[np.cos(a), np.sin(a)], [-np.sin(a), np.cos(a)]])


def build_track(circuit_id, circuit_key, year, race_session=None):
    out = config.OUT_DIR / 'tracks' / f'{circuit_id}.json'
    if out.exists():
        return json.loads(out.read_text())
    info = circuit_info(circuit_key, year) if circuit_key else None
    if not info and race_session:
        info = outline_from_openf1(race_session)
    if not info:
        return None
    xy = _rotate(np.column_stack([info['x'], info['y']]).astype(float), info.get('rotation', 0))
    corners = np.array([[c['trackPosition']['x'], c['trackPosition']['y']] for c in info.get('corners', [])],
                       dtype=float).reshape(-1, 2)
    corners = _rotate(corners, info.get('rotation', 0)) if len(corners) else corners
    lo, span = xy.min(axis=0), (xy.max(axis=0) - xy.min(axis=0)).max()
    pad = 40

    def fit(p):
        q = (p - lo) / span * (SIZE - 2 * pad) + pad
        q[:, 1] = SIZE - q[:, 1]        # SVG y grows downward
        return q

    pts = fit(xy)
    pts = pts[::max(1, len(pts) // 400)]
    cp = fit(corners) if len(corners) else corners
    top = pts[:, 1].min() - pad              # trim the empty space above the track
    pts[:, 1] -= top
    if len(cp):
        cp[:, 1] -= top
    track = {
        'circuitId': circuit_id,
        'name': info.get('circuitName'),
        'viewBox': [0, 0, round(float(pts[:, 0].max() + pad)), round(float(pts[:, 1].max() + pad))],
        'points': np.round(pts, 1).tolist(),
        'corners': [{'n': c['number'], 'x': round(float(p[0]), 1), 'y': round(float(p[1]), 1)}
                    for c, p in zip(info.get('corners', []), cp)],
        'pitLoss': float(info['pitLoss']['normal']) if (info.get('pitLoss') or {}).get('normal') else None,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(track, separators=(',', ':')))
    return track


def outline_from_openf1(session_key):
    """New circuits MultiViewer doesn't know yet: trace one clean race lap of the car positions."""
    laps = openf1('laps', session_key=int(session_key))
    if laps.empty:
        return None
    laps = laps.dropna(subset=['lap_duration', 'date_start'])
    laps = laps[(laps['lap_number'] > 3) & ~laps['is_pit_out_lap'].fillna(False).astype(bool)]
    if laps.empty:
        return None
    lap = laps.sort_values('lap_duration').iloc[len(laps) // 4]       # a quick but ordinary lap
    a = pd.Timestamp(lap['date_start'])
    b = a + pd.Timedelta(seconds=float(lap['lap_duration']))
    url = (f"https://api.openf1.org/v1/location?session_key={int(session_key)}"
           f"&driver_number={int(lap['driver_number'])}&date>={a.isoformat()}&date<{b.isoformat()}")
    pos = get_json(url.replace('+', '%2B'))
    if not pos or len(pos) < 50:
        return None
    pos = pd.DataFrame(pos)
    pos = pos[(pos['x'] != 0) | (pos['y'] != 0)]
    return {'x': pos['x'].tolist(), 'y': pos['y'].tolist(), 'rotation': 0, 'corners': [], 'circuitName': None}

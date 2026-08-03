# 🔮 PyStrology

An in-depth natal chart astrology app — full planetary positions, houses, aspects, a chart wheel, plain-language readings, and current transits, all calculated locally with the Swiss Ephemeris. No astrology API, no scraping.

Split off from a NASA dashboard side project since it outgrew being "one tab in a bigger app."

## Features

- **Natal chart**: all 10 classical planets + North Node, houses (Placidus), Ascendant/Midheaven, and major aspects (conjunction/sextile/square/trine/opposition)
- **Chart wheel**: SVG zodiac wheel with house cusps, angle labels (ASC/DESC/MC/IC), and planet glyphs
- **Plain-language readings**: templated interpretations for each placement, angle, and aspect
- **Current transits**: today's planetary positions against a saved natal chart, including which house each transiting planet falls in
- **Location search**: type a city, get lat/lon/timezone filled in automatically (via Open-Meteo's free geocoding API)
- **Basic vs. in-depth**: a lightweight Sun/Moon/Rising view, or the full chart (in-depth requires an email address)

## How the math works

Calculations run through [`pyswisseph`](https://pypi.org/project/pyswisseph/) (the Python bindings for the Swiss Ephemeris — the same engine most professional astrology software uses) in Moshier mode, which needs no downloaded ephemeris data files and works fully offline. Timezone conversion uses Python's built-in `zoneinfo`, so DST and historical offsets are handled correctly for the actual birth date.

## Data storage

If you give a nickname, your chart is saved to `data/astrology/<nickname>.txt` so you can reload it later or check current transits against it. A few things by design:

- **No real names** — nickname only, restricted to safe filename characters
- **Email is optional** and only stored if you provide one (currently required if you want an in-depth chart)
- `data/astrology/` is gitignored — it's runtime user data, never part of the repo

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open [http://localhost:5000](http://localhost:5000).

No API key needed to run the app — the only outbound network call is the optional location search, which hits Open-Meteo's free geocoding API (no key required either).

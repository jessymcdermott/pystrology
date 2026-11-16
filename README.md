# Pystrology

A small Flask app that calculates a full natal chart (planets, houses, ascendant/midheaven, aspects) and current transits.

- Calculations run locally with the Swiss Ephemeris (`pyswisseph`, Moshier mode), so no external API or ephemeris data files are needed.
- Birth-location search uses the free [Open-Meteo geocoding API](https://open-meteo.com/en/docs/geocoding-api).
- Charts can optionally be saved under a nickname (no real names) to `data/astrology/<nickname>.txt` so they can be reloaded later. Email is only collected for in-depth charts. `data/` is gitignored.

Originally built as the Astrology panel of the `nasa-dashboard` repo, split out on 2026-11-16.

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug
```

Then open http://127.0.0.1:5000.

## Run with Docker

```bash
docker build -t pystrology .
docker run -p 5000:5000 pystrology
```

## API

| Method | Path | What it does |
|---|---|---|
| POST | `/api/astrology/chart` | Calculate a basic or in-depth chart (optionally save it under `nickname`) |
| GET | `/api/astrology/saved/<nickname>` | Reload a saved chart |
| GET | `/api/astrology/transits/<nickname>` | Current transits against a saved in-depth chart |
| GET | `/api/astrology/geocode?q=<place>` | Look up lat/lon/timezone for a place name |

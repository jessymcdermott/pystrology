import requests
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

from src.astrology import chart as astrology_chart
from src.astrology import storage as astrology_storage

load_dotenv()

app = Flask(__name__)

# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# Natal chart calculation + optional save-for-later
@app.route("/api/astrology/chart", methods=["POST"])
def astrology_calculate():
    data = request.get_json(silent=True) or {}

    chart_type = "in_depth" if data.get("chart_type") == "in_depth" else "basic"
    required = ["birth_date", "birth_time", "latitude", "longitude", "timezone"]
    missing = [f for f in required if data.get(f) in (None, "")]
    if missing:
        return jsonify({"error": f"Missing required field(s): {', '.join(missing)}"}), 400

    if chart_type == "in_depth" and not data.get("email"):
        return jsonify({"error": "An email is required for an in-depth chart."}), 400

    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
        tz_name = data["timezone"]
        result = astrology_chart.calculate_chart(
            data["birth_date"], data["birth_time"], latitude, longitude, tz_name, chart_type
        )
    except (ValueError, KeyError) as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400

    nickname = data.get("nickname")
    if nickname:
        try:
            astrology_storage.save_record({
                "nickname": nickname,
                "birth_date": data["birth_date"],
                "birth_time": data["birth_time"],
                "latitude": latitude,
                "longitude": longitude,
                "timezone": tz_name,
                "location_label": data.get("location_label", ""),
                "chart_type": chart_type,
                "email": data.get("email", "") if chart_type == "in_depth" else "",
            })
        except astrology_storage.InvalidNickname as e:
            return jsonify({"error": str(e)}), 400

    return jsonify(result)


# Load a previously saved nickname's chart
@app.route("/api/astrology/saved/<nickname>")
def astrology_saved(nickname):
    try:
        record = astrology_storage.load_record(nickname)
    except astrology_storage.InvalidNickname as e:
        return jsonify({"error": str(e)}), 400

    if not record:
        return jsonify({"error": "No saved chart for that nickname."}), 404

    try:
        result = astrology_chart.calculate_chart(
            record["birth_date"], record["birth_time"],
            float(record["latitude"]), float(record["longitude"]), record["timezone"],
            record.get("chart_type", "basic"),
        )
    except (ValueError, KeyError) as e:
        return jsonify({"error": f"Saved record is corrupt: {e}"}), 500

    result["nickname"] = record["nickname"]
    result["location_label"] = record.get("location_label", "")
    return jsonify(result)


# Current transits against a saved nickname's natal chart
@app.route("/api/astrology/transits/<nickname>")
def astrology_transits(nickname):
    try:
        record = astrology_storage.load_record(nickname)
    except astrology_storage.InvalidNickname as e:
        return jsonify({"error": str(e)}), 400

    if not record:
        return jsonify({"error": "No saved chart for that nickname."}), 404

    if record.get("chart_type") != "in_depth":
        return jsonify({"error": "Transits require a saved in-depth chart."}), 400

    try:
        natal = astrology_chart.calculate_chart(
            record["birth_date"], record["birth_time"],
            float(record["latitude"]), float(record["longitude"]), record["timezone"],
            "in_depth",
        )
        natal_cusps = [c["longitude"] for c in natal["houses"]["cusps"]]
        transits = astrology_chart.calculate_transits(natal["planets"], natal_cusps)
    except (ValueError, KeyError) as e:
        return jsonify({"error": f"Could not compute transits: {e}"}), 500

    transits["nickname"] = record["nickname"]
    return jsonify(transits)


# Geocode a free-text location into lat/lon/timezone candidates
@app.route("/api/astrology/geocode")
def astrology_geocode():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter 'q'."}), 400

    try:
        resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": query, "count": 5},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502

    results = [
        {
            "label": ", ".join(filter(None, [r.get("name"), r.get("admin1"), r.get("country")])),
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "timezone": r["timezone"],
        }
        for r in data.get("results", [])
    ]
    return jsonify({"results": results})


if __name__ == "__main__":
    app.run(debug=True)

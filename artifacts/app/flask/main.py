from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from cities_data import CITIES_DATA

app = Flask(__name__)
CORS(app)

plans_db = []


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/cities")
def list_cities():
    """Return all available cities with basic info."""
    result = []
    for key, data in CITIES_DATA.items():
        result.append({
            "id": key,
            "name_cn": data["name_cn"],
            "name_en": data["name_en"],
            "description": data["description"],
            "attraction_count": len(data["attractions"]),
        })
    return jsonify({"cities": result, "count": len(result)})


@app.get("/api/attractions")
def get_attractions():
    """Return attractions for a given city."""
    city = request.args.get("city", "").strip().lower()
    if not city:
        return jsonify({"error": "city parameter is required"}), 400

    data = CITIES_DATA.get(city)
    if not data:
        return jsonify({"error": f"City '{city}' not found"}), 404

    return jsonify({
        "city": data["name_cn"],
        "name_en": data["name_en"],
        "description": data["description"],
        "attractions": data["attractions"],
        "count": len(data["attractions"]),
    })


@app.post("/api/plan")
def create_plan():
    """Generate a day-by-day travel plan."""
    body = request.get_json(silent=True) or {}
    city = body.get("city", "").strip().lower()
    days = body.get("days")

    if not city or days is None:
        return jsonify({"error": "city and days are required"}), 400

    try:
        days = int(days)
    except (TypeError, ValueError):
        return jsonify({"error": "days must be an integer"}), 400

    if days < 1 or days > 7:
        return jsonify({"error": "days must be between 1 and 7"}), 400

    data = CITIES_DATA.get(city)
    if not data:
        return jsonify({"error": f"City '{city}' not found"}), 404

    attractions = data["attractions"]
    itinerary = []
    attr_idx = 0

    for day in range(1, days + 1):
        day_spots = []
        spots_per_day = min(2, len(attractions) - attr_idx)
        for _ in range(spots_per_day):
            if attr_idx < len(attractions):
                day_spots.append(attractions[attr_idx]["name"])
                attr_idx += 1
        itinerary.append({
            "day": day,
            "title": f"Day {day}",
            "activities": day_spots if day_spots else ["Free exploration"],
            "meal_suggestion": "Try local specialties nearby",
        })

    plan = {
        "plan_id": len(plans_db) + 1,
        "city": data["name_cn"],
        "days": days,
        "itinerary": itinerary,
        "status": "created",
    }
    plans_db.append(plan)
    return jsonify(plan), 201


# Serve frontend
@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(".", filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5005)

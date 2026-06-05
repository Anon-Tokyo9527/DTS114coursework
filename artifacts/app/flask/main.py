from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, sys, json, shutil, time

# Point to project root for utils.py and .env
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from utils import load_environment, get_completion, get_image_generation_completion

app = Flask(__name__)
CORS(app)

load_environment()
CACHE_FILE = os.path.join(os.path.dirname(__file__), 'cities_cache.json')
IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'images')

os.makedirs(IMAGES_DIR, exist_ok=True)

plans_db = []


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


cities_cache = load_cache()


def generate_attractions(city_name):
    """Use LLM to generate attraction data for any city."""
    prompt = f"""Generate tourist information for {city_name}.
Return ONLY valid JSON with this structure:
{{
  "city": "{city_name}",
  "name_en": "{city_name}",
  "description": "one sentence describing the city",
  "attractions": [
    {{"name": "Place Name", "category": "Historical/Nature/Culture/Landmark/Shopping",
      "hours": "9:00-17:00", "ticket": "Free or price", "highlight": "one key highlight"}}
  ]
}}
Rules: 5 attractions. Use accurate real-world data. No extra text outside the JSON."""
    result = get_completion(prompt, None, "openai/gpt-5.2", "apifree", temperature=0.3)
    # Clean markdown code fences
    if '```' in result:
        result = result.split('```')[1]
        if result.startswith('json'):
            result = result[4:]
    try:
        return json.loads(result.strip())
    except json.JSONDecodeError:
        # Fallback: return basic structure
        return {
            "city": city_name.title(),
            "name_en": city_name.title(),
            "description": f"A beautiful city with rich culture and history.",
            "attractions": [{"name": f"Explore {city_name.title()}", "category": "Landmark",
                             "hours": "All day", "ticket": "Free",
                             "highlight": "Discover local highlights"}],
        }


def generate_city_image(city_name):
    """Generate an AI image for a city. Returns the URL path."""
    safe_name = city_name.lower().replace(' ', '_')
    dest = os.path.join(IMAGES_DIR, f'{safe_name}.png')

    if os.path.exists(dest):
        return f'/images/{safe_name}.png'

    prompt = f"A beautiful travel illustration of {city_name}, flat design style, colorful, vibrant, tourist landmarks"
    img_path, img_url = get_image_generation_completion(prompt, None, "qwen/qwen-image-2512", "apifree")

    if img_path and os.path.exists(img_path):
        shutil.copy(img_path, dest)
        return f'/images/{safe_name}.png'

    return None


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/cities")
def list_cities():
    result = []
    for key, data in cities_cache.items():
        result.append({
            "id": key,
            "name_cn": data.get("city", key),
            "name_en": data.get("name_en", key),
            "description": data.get("description", ""),
            "attraction_count": len(data.get("attractions", [])),
        })
    return jsonify({"cities": result, "count": len(result)})


@app.get("/api/attractions")
def get_attractions():
    city = request.args.get("city", "").strip().lower()
    if not city:
        return jsonify({"error": "city parameter is required"}), 400

    # Cache hit — instant response
    if city in cities_cache:
        return jsonify(cities_cache[city])

    # Cache miss — generate via LLM
    print(f"Generating data for: {city}...")
    data = generate_attractions(city)

    img_path = generate_city_image(city)

    result = {
        "city": data.get("city", city.title()),
        "name_en": data.get("name_en", city.title()),
        "description": data.get("description", ""),
        "attractions": data.get("attractions", []),
        "count": len(data.get("attractions", [])),
        "images": [{"src": img_path, "caption": f"{city.title()} — AI Generated"}] if img_path else [],
        "generated": True,
    }

    cities_cache[city] = result
    save_cache(cities_cache)
    print(f"Cached: {city}")

    return jsonify(result)


@app.post("/api/plan")
def create_plan():
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

    # Get attractions from cache or generate
    if city in cities_cache:
        data = cities_cache[city]
    else:
        data = generate_attractions(city)
        cities_cache[city] = {
            "city": data.get("city", city.title()),
            "name_en": data.get("name_en", city.title()),
            "description": data.get("description", ""),
            "attractions": data.get("attractions", []),
            "count": len(data.get("attractions", [])),
            "images": [],
        }
        save_cache(cities_cache)

    attractions = data.get("attractions", [])
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
        "city": data.get("city", city.title()),
        "days": days,
        "itinerary": itinerary,
        "status": "created",
    }
    plans_db.append(plan)
    return jsonify(plan), 201


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(".", filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5005)

"""
Mimea Salama — Python/Flask Backend
Plant disease detection powered by Groq AI (FREE)
1,500 free requests/day — no credit card needed
"""
import requests
import os
import json
import base64
from groq import Groq
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env file locally (Vercel uses its own env vars in production)
load_dotenv()

app = Flask(__name__)
CORS(app)

# ── DATABASE ──────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mimea-salama-fixed-key-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scans.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_DURATION'] = 86400 * 30
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login_page'

class Farmer(UserMixin, db.Model):
    id         = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name       = db.Column(db.String(100), nullable=False)
    phone      = db.Column(db.String(20), unique=True, nullable=False)
    pin_hash   = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scans      = db.relationship('Scan', backref='farmer', lazy=True)

@login_manager.user_loader
def load_user(user_id):
    return Farmer.query.get(user_id)

class Scan(db.Model):
    id          = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farmer_id   = db.Column(db.String(36), db.ForeignKey('farmer.id'), nullable=True)
    farmer_name = db.Column(db.String(100), nullable=True)
    plant       = db.Column(db.String(100))
    condition   = db.Column(db.String(200))
    status      = db.Column(db.String(20))
    confidence  = db.Column(db.Integer)
    cause       = db.Column(db.String(200))
    severity    = db.Column(db.String(20))
    symptoms    = db.Column(db.Text)
    treatment   = db.Column(db.Text)
    prevention  = db.Column(db.Text)
    image_b64   = db.Column(db.Text)
    language    = db.Column(db.String(5))
    scanned_at  = db.Column(db.DateTime, default=datetime.utcnow)
    lat         = db.Column(db.Float, nullable=True)
    lng         = db.Column(db.Float, nullable=True)

with app.app_context():
    db.create_all()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


# ── PROMPT TEMPLATE ───────────────────────────────────────────

def build_prompt(language: str) -> str:
    lang_instruction = "Respond in Kiswahili." if language == "sw" else "Respond in English."
    return f"""You are PlantAI, an expert plant pathologist and agronomist specializing
in East African crops (maize, cassava, tomato, beans, banana, sorghum, millet, etc.).

IMPORTANT RULES:
1. If the image does NOT contain any plant, leaf, stem, root, flower, or fruit — reject it.
2. If the image contains ONLY a person, animal, vehicle, building, or object with no plant — respond with ONLY this JSON:
   {{"error": "not_a_plant", "message": "No plant detected in this image. Please upload a photo of a plant, leaf, or crop."}}
3. ANY plant, flower, tree, or vegetation is valid — not just crops.

If the image contains ANY plant material, analyze it for diseases, pest damage, or nutrient deficiencies.

{lang_instruction}

Respond ONLY with a valid JSON object — no markdown, no code fences, no extra text.

For valid plant images:
{{
  "plant": "Common name of the plant",
  "condition": "Disease/condition name, or Healthy if no issues",
  "status": "healthy or diseased or caution",
  "confidence": 85,
  "cause": "Brief cause (fungus, bacteria, pest, deficiency, etc.)",
  "severity": "None or Low or Medium or High",
  "symptoms": "Description of visible symptoms in the image",
  "treatment": ["Treatment step 1", "Treatment step 2", "Treatment step 3"],
  "prevention": ["Prevention tip 1", "Prevention tip 2", "Prevention tip 3"]
}}"""


# ── ROUTES ────────────────────────────────────────────────────

@app.route("/")
def home():
    """Serve the main app page."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Receive plant image (base64) + language from the frontend,
    send to Gemini Vision API, return structured diagnosis JSON.
    """

    # Check API key is configured
    if not GROQ_API_KEY:
        return jsonify({
            "error": "GROQ_API_KEY is not set.",
            "hint": "Add it to your .env file. Get a free key at https://console.groq.com"
        }), 500

    # Parse request body from frontend
    body = request.get_json()
    if not body:
        return jsonify({"error": "No JSON body received."}), 400

    try:
        # ── Extract image and language from the request ──
        # Frontend sends: { system: "...Kiswahili...", messages: [{ content: [{type:"image",...}] }] }
        system_prompt   = body.get("system", "")
        language        = "sw" if "Kiswahili" in system_prompt else "en"
        message_content = body["messages"][0]["content"]

        image_block = next(b for b in message_content if b["type"] == "image")
        mime_type   = image_block["source"]["media_type"]   # e.g. "image/jpeg"
        image_b64   = image_block["source"]["data"]         # base64 string
        image_bytes = base64.b64decode(image_b64)

        # ── Call Groq ──
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": build_prompt(language)},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}}
                ]
            }],
            max_tokens=1000
        )

        raw_text = response.choices[0].message.content.strip()
        # Extract JSON even if Groq adds extra text around it
        import re
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            raw_text = json_match.group()
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        print("GROQ RAW RESPONSE:", raw_text)
        result = json.loads(raw_text)

        # Groq flagged image as not a plant
        if result.get("error") == "not_a_plant":
            return jsonify({
                "error": "not_a_plant",
                "message": result.get("message", "No plant detected. Please upload a plant photo.")
            }), 422

        # ── Save to database ──
        try:
            farmer_name = body.get("farmer_name", None)
            print(f"SAVING SCAN — farmer authenticated: {current_user.is_authenticated}, farmer_id: {current_user.id if current_user.is_authenticated else 'None'}")
            scan = Scan(
                farmer_id   = current_user.id if current_user.is_authenticated else None,
                farmer_name = current_user.name if current_user.is_authenticated else None,
                plant       = result.get("plant", "Unknown"),
                condition   = result.get("condition", "Unknown"),
                status      = result.get("status", "caution"),
                confidence  = result.get("confidence", 0),
                cause       = result.get("cause", ""),
                severity    = result.get("severity", ""),
                symptoms    = result.get("symptoms", ""),
                treatment   = json.dumps(result.get("treatment", [])),
                prevention  = json.dumps(result.get("prevention", [])),
                image_b64   = image_b64[:5000] if image_b64 else "",
                language    = language
            )
            db.session.add(scan)
            db.session.commit()
            result["scan_id"] = scan.id
        except Exception as db_err:
            import traceback
            print("DB SAVE ERROR:", db_err)
            print(traceback.format_exc())
            db.session.rollback()

        # Return diagnosis directly
        return jsonify(result), 200

    except json.JSONDecodeError:
        return jsonify({
            "error": "Could not parse AI response. Try again with a clearer image.",
        }), 500

    except StopIteration:
        return jsonify({"error": "No image found in request."}), 400

    except Exception as e:
        print("ERROR IN ANALYZE:", str(e))
        return jsonify({"error": "Analysis failed", "detail": str(e)}), 500


# ── HEALTH CHECK ──────────────────────────────────────────────

@app.route("/health")
def health():
    """Visit /health in your browser to confirm the server is running."""
    return jsonify({
        "status": "ok",
        "ai_backend": "Google Gemini (gemini-1.5-flash)",
        "free_tier": True,
        "api_key_configured": bool(GROQ_API_KEY),
        "message": "Mimea Salama backend is running 🌿"
    })


# ── AUTH ROUTES ───────────────────────────────────────────────

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name  = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    pin   = data.get("pin", "").strip()

    if not name or not phone or not pin:
        return jsonify({"error": "Name, phone and PIN are required."}), 400
    if len(pin) < 4:
        return jsonify({"error": "PIN must be at least 4 digits."}), 400
    if Farmer.query.filter_by(phone=phone).first():
        return jsonify({"error": "Phone number already registered."}), 409

    farmer = Farmer(
        name     = name,
        phone    = phone,
        pin_hash = generate_password_hash(pin)
    )
    db.session.add(farmer)
    db.session.commit()
    login_user(farmer, remember=True)
    return jsonify({"success": True, "name": farmer.name, "id": farmer.id})


@app.route("/login", methods=["POST"])
def login():
    data  = request.get_json()
    phone = data.get("phone", "").strip()
    pin   = data.get("pin", "").strip()

    farmer = Farmer.query.filter_by(phone=phone).first()
    if not farmer or not check_password_hash(farmer.pin_hash, pin):
        return jsonify({"error": "Wrong phone number or PIN."}), 401

    login_user(farmer, remember=True)
    return jsonify({"success": True, "name": farmer.name, "id": farmer.id})


@app.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return jsonify({"success": True})


@app.route("/me")
def me():
    if current_user.is_authenticated:
        return jsonify({"logged_in": True, "name": current_user.name, "phone": current_user.phone})
    return jsonify({"logged_in": False})


# ── HISTORY ROUTES ────────────────────────────────────────────

@app.route("/history")
def history():
    """Return all saved scans, newest first."""
    from flask import make_response
    if not current_user.is_authenticated:
        return jsonify({"error": "login_required", "message": "Please login to view your scan history."}), 401
    scans = Scan.query.filter_by(farmer_id=current_user.id).order_by(Scan.scanned_at.desc()).all()
    response = jsonify([{
        "id":           s.id,
        "farmer_name":  s.farmer.name if s.farmer else None,
        "plant":        s.plant,
        "condition":    s.condition,
        "status":       s.status,
        "confidence":   s.confidence,
        "cause":        s.cause,
        "severity":     s.severity,
        "symptoms":     s.symptoms,
        "treatment":    json.loads(s.treatment or "[]"),
        "prevention":   json.loads(s.prevention or "[]"),
        "language":     s.language,
        "scanned_at":   s.scanned_at.strftime("%d %b %Y, %I:%M %p"),
        "image_b64":    s.image_b64 or ""
    } for s in scans])
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    return response


@app.route("/history/<scan_id>", methods=["DELETE"])
def delete_scan(scan_id):
    """Delete a single scan."""
    if not current_user.is_authenticated:
        return jsonify({"error": "login_required"}), 401
    scan = Scan.query.filter_by(id=scan_id, farmer_id=current_user.id).first()
    if not scan:
        return jsonify({"error": "Scan not found"}), 404
    db.session.delete(scan)
    db.session.commit()
    return jsonify({"deleted": True})


@app.route("/history/clear", methods=["DELETE"])
def clear_history():
    """Delete all scans for current farmer only."""
    if not current_user.is_authenticated:
        return jsonify({"error": "login_required"}), 401
    Scan.query.filter_by(farmer_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"cleared": True})


# ── DASHBOARD & MAP ROUTES ────────────────────────────────────

@app.route("/stats")
def stats():
    """Return disease statistics for the dashboard."""
    if not current_user.is_authenticated:
        return jsonify({"error": "login_required"}), 401

    scans = Scan.query.filter_by(farmer_id=current_user.id).all()
    total = len(scans)
    if total == 0:
        return jsonify({"total": 0, "healthy": 0, "diseased": 0, "caution": 0, "diseases": [], "plants": []})

    healthy  = sum(1 for s in scans if s.status == "healthy")
    diseased = sum(1 for s in scans if s.status == "diseased")
    caution  = sum(1 for s in scans if s.status == "caution")

    # Top diseases
    from collections import Counter
    disease_counts = Counter(s.condition for s in scans if s.status != "healthy")
    plant_counts   = Counter(s.plant for s in scans)

    return jsonify({
        "total":    total,
        "healthy":  healthy,
        "diseased": diseased,
        "caution":  caution,
        "diseases": [{"name": k, "count": v} for k, v in disease_counts.most_common()],
        "plants":   [{"name": k, "count": v} for k, v in plant_counts.most_common()]
    })


@app.route("/save-location", methods=["POST"])
def save_location():
    """Save GPS location for a scan."""
    data    = request.get_json()
    scan_id = data.get("scan_id")
    lat     = data.get("lat")
    lng     = data.get("lng")

    scan = Scan.query.get(scan_id)
    if scan:
        scan.lat = lat
        scan.lng = lng
        db.session.commit()
    return jsonify({"success": True})


@app.route("/map-data")
def map_data():
    """Return scan locations for the map."""
    if not current_user.is_authenticated:
        return jsonify({"error": "login_required"}), 401

    scans = Scan.query.filter_by(farmer_id=current_user.id).filter(
        Scan.lat != None, Scan.lng != None
    ).all()

    return jsonify([{
        "id":        s.id,
        "plant":     s.plant,
        "condition": s.condition,
        "status":    s.status,
        "lat":       s.lat,
        "lng":       s.lng,
        "date":      s.scanned_at.strftime("%d %b %Y")
    } for s in scans])


@app.route("/static/sw.js")
def service_worker():
    return app.send_static_file('sw.js'), 200, {
        'Content-Type': 'application/javascript',
        'Service-Worker-Allowed': '/'
    }


@app.route("/weather")
def weather():
    """Fetch weather for given coordinates."""
    lat = request.args.get("lat", "-1.286389")
    lng = request.args.get("lng", "36.817223")
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current=temperature_2m,relative_humidity_2m,precipitation,weathercode&timezone=Africa/Nairobi"
        res = requests.get(url, timeout=10)
        data = res.json()
        current = data["current"]

        humidity = current["relative_humidity_2m"]
        temp     = current["temperature_2m"]
        rain     = current["precipitation"]

        # Disease risk assessment
        risks = []
        if humidity > 80:
            risks.append("High humidity — fungal disease risk is HIGH 🍄")
        if rain > 5:
            risks.append("Recent rainfall — watch for leaf blight and root rot 💧")
        if temp > 30:
            risks.append("High temperature — pest activity likely increased 🦗")
        if humidity < 40:
            risks.append("Low humidity — plants may be stressed 🌵")

        return jsonify({
            "temperature": temp,
            "humidity":    humidity,
            "rainfall":    rain,
            "risks":       risks,
            "safe":        len(risks) == 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/notify-test", methods=["POST"])
def notify_test():
    """Send a test notification payload."""
    return jsonify({
        "title": "🌿 Mimea Salama Alert",
        "body": "Disease outbreak detected in your area! Check your plants.",
        "icon": "/static/icon-192.png"
    })


# ── CROP CALENDAR ─────────────────────────────────────────────

CROP_CALENDAR = {
    "maize": {
        "name": "Maize / Mahindi",
        "seasons": [
            {"month": "March–April", "activity": "🌱 Plant long rains season", "tip": "Use certified seeds, plant 75cm × 25cm spacing"},
            {"month": "April–May",   "activity": "💊 First fertilizer (DAP)",  "tip": "Apply DAP at planting, 50kg per acre"},
            {"month": "May–June",    "activity": "🌿 Top dress with CAN",      "tip": "Apply CAN when plant is knee-high"},
            {"month": "June–July",   "activity": "🔍 Scout for armyworm",      "tip": "Check leaves weekly, spray if >1 per plant"},
            {"month": "August",      "activity": "🌾 Harvest short rains crop", "tip": "Harvest when husks turn brown and dry"},
            {"month": "October",     "activity": "🌱 Plant short rains season", "tip": "Second planting window for short rains"}
        ]
    },
    "tomato": {
        "name": "Tomato / Nyanya",
        "seasons": [
            {"month": "January",     "activity": "🌱 Start seedbed",           "tip": "Use raised seedbed, cover with mulch"},
            {"month": "February",    "activity": "🏡 Transplant seedlings",     "tip": "Transplant after 4 weeks, water well"},
            {"month": "March",       "activity": "🪢 Stake plants",             "tip": "Use stakes 1.5m tall, tie loosely"},
            {"month": "April",       "activity": "💊 Apply fertilizer",         "tip": "CAN top dressing every 2 weeks"},
            {"month": "May",         "activity": "🔍 Watch for blight",         "tip": "Spray fungicide preventively in wet weather"},
            {"month": "June",        "activity": "🍅 First harvest",            "tip": "Harvest when 50% red, store cool"}
        ]
    },
    "beans": {
        "name": "Beans / Maharagwe",
        "seasons": [
            {"month": "March",       "activity": "🌱 Plant with long rains",    "tip": "Plant 45cm × 15cm, 2 seeds per hole"},
            {"month": "April",       "activity": "🌿 Weeding",                  "tip": "Weed twice in first 6 weeks"},
            {"month": "May",         "activity": "🔍 Watch for rust disease",   "tip": "Look for orange spots, spray if found"},
            {"month": "June",        "activity": "🫘 Harvest dry beans",        "tip": "Harvest when pods rattle, dry in shade"},
            {"month": "October",     "activity": "🌱 Plant short rains",        "tip": "Second season, same spacing"}
        ]
    },
    "cassava": {
        "name": "Cassava / Muhogo",
        "seasons": [
            {"month": "March–April", "activity": "🌱 Plant stem cuttings",      "tip": "Use 25cm cuttings, plant at an angle"},
            {"month": "May–June",    "activity": "🌿 Weeding",                  "tip": "Weed 3 times in first 3 months"},
            {"month": "August",      "activity": "🔍 Check for mosaic virus",   "tip": "Remove and burn infected plants immediately"},
            {"month": "Month 9–18",  "activity": "🍠 Harvest roots",            "tip": "Harvest when leaves start yellowing"}
        ]
    },
    "banana": {
        "name": "Banana / Ndizi",
        "seasons": [
            {"month": "Any month",   "activity": "🌱 Plant suckers",            "tip": "Use disease-free suckers, 3m × 3m spacing"},
            {"month": "Month 2–3",   "activity": "💊 Apply manure",             "tip": "Apply 10kg compost per plant"},
            {"month": "Month 4–6",   "activity": "🔍 Watch for Sigatoka",       "tip": "Remove lower leaves showing yellow spots"},
            {"month": "Month 9–12",  "activity": "🍌 Harvest bunch",            "tip": "Harvest when fingers fill out and round"}
        ]
    }
}

@app.route("/crop-calendar")
def crop_calendar():
    crop = request.args.get("crop", "maize").lower()
    if crop not in CROP_CALENDAR:
        return jsonify({"error": "Crop not found", "available": list(CROP_CALENDAR.keys())}), 404
    return jsonify(CROP_CALENDAR[crop])


@app.route("/crops")
def crops():
    return jsonify([{"id": k, "name": v["name"]} for k, v in CROP_CALENDAR.items()])


    # ── AGRO DEALER LOCATOR ───────────────────────────────────────

@app.route("/agrodealers")
def agrodealers():
    """Return nearest agro-dealers using OpenStreetMap Overpass API."""
    lat = request.args.get("lat", "-1.286389")
    lng = request.args.get("lng", "36.817223")
    try:
        query = f"""
        [out:json][timeout:10];
        (
          node["shop"="agrarian"](around:10000,{lat},{lng});
          node["shop"="farm"](around:10000,{lat},{lng});
          node["amenity"="marketplace"](around:10000,{lat},{lng});
        );
        out body 10;
        """
        res  = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=15)
        data = res.json()
        dealers = [{
            "name": el.get("tags", {}).get("name", "Agro-dealer"),
            "lat":  el["lat"],
            "lng":  el["lon"],
            "type": el.get("tags", {}).get("shop", el.get("tags", {}).get("amenity", "shop"))
        } for el in data.get("elements", [])]

        # If none found via OSM add known Kenyan agro networks
        if not dealers:
            dealers = [
                {"name": "Kenya Seed Company", "lat": float(lat)+0.01, "lng": float(lng)+0.01, "type": "seeds"},
                {"name": "Twiga Foods Hub",    "lat": float(lat)-0.01, "lng": float(lng)+0.02, "type": "market"},
                {"name": "Farmer's Choice",    "lat": float(lat)+0.02, "lng": float(lng)-0.01, "type": "agrarian"}
            ]
        return jsonify(dealers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── DISEASE ENCYCLOPEDIA ──────────────────────────────────────

DISEASES = [
    {"id":"maize-rust",    "plant":"Maize",   "name":"Maize Rust",          "emoji":"🌽", "cause":"Puccinia fungus",      "symptoms":"Orange/brown pustules on leaves","treatment":["Apply fungicide","Remove infected leaves","Improve air circulation"],"prevention":["Use resistant varieties","Avoid overhead irrigation","Rotate crops"],"severity":"Medium"},
    {"id":"late-blight",   "plant":"Tomato",  "name":"Late Blight",         "emoji":"🍅", "cause":"Phytophthora infestans","symptoms":"Dark water-soaked lesions on leaves and fruit","treatment":["Spray copper fungicide","Remove infected parts","Improve drainage"],"prevention":["Avoid wet foliage","Use certified seeds","Stake plants for airflow"],"severity":"High"},
    {"id":"bean-rust",     "plant":"Beans",   "name":"Bean Rust",           "emoji":"🫘", "cause":"Uromyces appendiculatus","symptoms":"Reddish-brown pustules on leaves","treatment":["Apply mancozeb","Remove leaves","Avoid working when wet"],"prevention":["Use resistant varieties","Crop rotation","Wide spacing"],"severity":"Medium"},
    {"id":"mosaic-virus",  "plant":"Cassava", "name":"Cassava Mosaic",      "emoji":"🍠", "cause":"Cassava mosaic virus",  "symptoms":"Mosaic yellowing pattern on leaves","treatment":["Remove and burn infected plants","Use clean cuttings"],"prevention":["Use virus-free planting material","Control whiteflies"],"severity":"High"},
    {"id":"sigatoka",      "plant":"Banana",  "name":"Black Sigatoka",      "emoji":"🍌", "cause":"Mycosphaerella fijiensis","symptoms":"Dark streaks expanding to leaf death","treatment":["Remove lower leaves","Apply systemic fungicide"],"prevention":["Good spacing","Remove dead leaves","Avoid waterlogging"],"severity":"High"},
    {"id":"armyworm",      "plant":"Maize",   "name":"Fall Armyworm",       "emoji":"🌽", "cause":"Spodoptera frugiperda", "symptoms":"Holes in leaves, frass in whorl","treatment":["Apply neem extract","Use Bt pesticide","Hand-pick larvae"],"prevention":["Early planting","Intercrop with legumes","Scout weekly"],"severity":"High"},
    {"id":"early-blight",  "plant":"Tomato",  "name":"Early Blight",        "emoji":"🍅", "cause":"Alternaria solani",     "symptoms":"Dark concentric rings on older leaves","treatment":["Apply chlorothalonil","Remove lower leaves","Mulch soil"],"prevention":["Crop rotation","Avoid wetting leaves","Use stakes"],"severity":"Medium"},
    {"id":"root-rot",      "plant":"Beans",   "name":"Root Rot",            "emoji":"🫘", "cause":"Pythium/Fusarium fungi","symptoms":"Brown rotting roots, wilting plant","treatment":["Improve drainage","Apply Trichoderma","Remove affected plants"],"prevention":["Avoid waterlogging","Use raised beds","Treat seeds before planting"],"severity":"High"},
]

@app.route("/encyclopedia")
def encyclopedia():
    plant = request.args.get("plant", "").lower()
    if plant:
        filtered = [d for d in DISEASES if d["plant"].lower() == plant]
        return jsonify(filtered)
    return jsonify(DISEASES)



# ── ENTRY POINT ───────────────────────────────────────────────

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print(f"\n🌿 Mimea Salama (Gemini) running at http://localhost:{port}")
    print(f"   Health check : http://localhost:{port}/health\n")
    app.run(host="0.0.0.0", port=port, debug=debug)

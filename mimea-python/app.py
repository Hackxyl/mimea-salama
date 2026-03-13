"""
Mimea Salama — Python/Flask Backend
Plant disease detection powered by Google Gemini (FREE)
1,500 free requests/day — no credit card needed
"""

import os
import json
import base64
from groq import Groq
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env file locally (Vercel uses its own env vars in production)
load_dotenv()

app = Flask(__name__)
CORS(app)

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


# ── ENTRY POINT ───────────────────────────────────────────────

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print(f"\n🌿 Mimea Salama (Gemini) running at http://localhost:{port}")
    print(f"   Health check : http://localhost:{port}/health\n")
    app.run(host="0.0.0.0", port=port, debug=debug)

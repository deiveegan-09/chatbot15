import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL_NAME = "gemini-3.1-flash-lite"
client = genai.Client(api_key=API_KEY) if API_KEY else None


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Please enter a study-related question."}), 400
    if len(message) > 6000:
        return jsonify({"error": "Your message is too long. Please keep it under 6,000 characters."}), 400
    if client is None:
        return jsonify({"error": "Gemini API key is not configured. Add it to your .env file."}), 503

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                max_output_tokens=1400,
            ),
        )
        answer = (response.text or "").strip()
        if not answer:
            answer = "I couldn't generate a response. Please try asking in a different way."
        return jsonify({"reply": answer})
    except Exception:
        app.logger.exception("Gemini API request failed")
        return jsonify({"error": "I couldn't reach the AI service right now. Please try again shortly."}), 502


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")

import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load .env file (LEMON_SQUEEZY_API_KEY, STORE_ID, APP_SECRET)
load_dotenv()

API_KEY = os.getenv("LEMON_SQUEEZY_API_KEY")
STORE_ID = os.getenv("STORE_ID")
APP_SECRET = os.getenv("APP_SECRET", "mysecret")  # simple shared secret

app = Flask(__name__)

BASE_URL = "https://api.lemonsqueezy.com/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/vnd.api+json",
}

# ---- License Activation ----
@app.route("/activate", methods=["POST"])
def activate():
    data = request.json
    # Basic auth check so random people can't hit your endpoint
    if data.get("app_secret") != APP_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    payload = {
        "data": {
            "type": "license-keys",
            "attributes": {
                "license_key": data.get("license_key"),
                "instance_name": data.get("instance_name", "default"),
            },
        }
    }

    url = f"{BASE_URL}/license-key-activations"
    resp = requests.post(url, json=payload, headers=headers)

    return jsonify(resp.json()), resp.status_code


# ---- License Validation ----
@app.route("/validate", methods=["POST"])
def validate():
    data = request.json
    if data.get("app_secret") != APP_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    license_key = data.get("license_key")
    url = f"{BASE_URL}/license-keys/validate"
    payload = {
        "data": {
            "type": "license-keys",
            "attributes": {"license_key": license_key},
        }
    }

    resp = requests.post(url, json=payload, headers=headers)
    return jsonify(resp.json()), resp.status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

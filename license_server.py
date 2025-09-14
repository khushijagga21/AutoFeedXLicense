import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

APP_SECRET = os.getenv("APP_SECRET", "change_me")
PORT = int(os.getenv("PORT", "8010"))

# Optional enforcement (leave blank if unsure)
LS_STORE_ID   = os.getenv("LS_STORE_ID", "").strip()
LS_PRODUCT_ID = os.getenv("LS_PRODUCT_ID", "").strip()
LS_VARIANT_ID = os.getenv("LS_VARIANT_ID", "").strip()

LEMON_LICENSE_BASE = "https://api.lemonsqueezy.com/v1"
app = Flask(__name__)

def _enforce_meta(meta: dict) -> str | None:
    if not isinstance(meta, dict):
        return None
    if LS_STORE_ID and str(meta.get("store_id")) != str(LS_STORE_ID):
        return "Store mismatch for this license."
    if LS_PRODUCT_ID and str(meta.get("product_id")) != str(LS_PRODUCT_ID):
        return "Product mismatch for this license."
    if LS_VARIANT_ID and str(meta.get("variant_id")) != str(LS_VARIANT_ID):
        return "Variant mismatch for this license."
    return None

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.post("/validate-license")
def validate_license():
    data = request.get_json(silent=True) or {}
    if data.get("app_secret") != APP_SECRET:
        return jsonify({"valid": False, "error": "Unauthorized"}), 401

    license_key = (data.get("license_key") or "").strip()
    instance_id = (data.get("instance_id") or "").strip() or None
    if not license_key:
        return jsonify({"valid": False, "error": "Missing license_key"}), 400

    payload = {"license_key": license_key}
    if instance_id:
        payload["instance_id"] = instance_id

    try:
        r = requests.post(f"{LEMON_LICENSE_BASE}/licenses/validate", json=payload, timeout=20)
        try:
            body = r.json() or {}
        except Exception:
            body = {}
        if r.status_code != 200:
            return jsonify({"valid": False, "error": f"Upstream {r.status_code}", **body}), 502

        mismatch = _enforce_meta(body.get("meta") or {})
        if mismatch:
            return jsonify({"valid": False, "error": mismatch, **body}), 200

        return jsonify(body), 200
    except Exception as e:
        return jsonify({"valid": False, "error": f"Network error: {e}"}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=True)

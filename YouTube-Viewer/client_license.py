# client_license.py — small client to call your local license server
import os
import json
import requests

LICENSE_SERVER_URL = os.getenv("LICENSE_SERVER_URL", "http://127.0.0.1:8010/validate-license")
APP_SECRET = os.getenv("APP_SECRET_CLIENT", "my_super_secret_shared_token")

def check_license(license_key: str, instance_id: str | None = None) -> dict:
    """
    Calls your local license server. Returns a dict like:
    { "valid": True/False, "error": "...", "license_key": {...}, "instance": {...}, "meta": {...} }
    """
    body = {"app_secret": APP_SECRET, "license_key": (license_key or "").strip()}
    if instance_id:
        body["instance_id"] = instance_id

    try:
        r = requests.post(LICENSE_SERVER_URL, json=body, timeout=20)
        try:
            data = r.json()
        except Exception:
            data = {"valid": False, "error": f"Bad response: {r.status_code}"}
        if r.status_code != 200:
            # bubble up server errors but keep shape
            if isinstance(data, dict):
                data.setdefault("valid", False)
            else:
                data = {"valid": False, "error": f"HTTP {r.status_code}"}
        return data
    except Exception as e:
        return {"valid": False, "error": f"Client network error: {e}"}

if __name__ == "__main__":
    # quick manual test (optional)
    print(json.dumps(check_license("PUT-A-REAL-USER-LICENSE-KEY-HERE"), indent=2))

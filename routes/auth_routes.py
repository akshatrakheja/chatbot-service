from flask import Blueprint, request, jsonify
import requests
import os

auth_bp = Blueprint("auth_bp", __name__)

MAIN_APP_BACKEND_URL = os.getenv("MAIN_APP_BACKEND_URL")  # Example: "http://localhost:5000"

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required."}), 400

    try:
        response = requests.post(
            f"{MAIN_APP_BACKEND_URL}/auth/login",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": response.json().get("error", "Login failed.")}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
from flask import Flask, request, jsonify
from roblox import Client
import asyncio
import time
import json

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

COOKIE = config["cookie"]
GROUP_ID = config["group_id"]
MAX_RANK = config["max_rank"]
SECRET_TOKEN = config["secret_token"]
REQUEST_COOLDOWN = config["cooldown_seconds"]

app = Flask(__name__)
client = Client()

# Login to Roblox
async def login():
    await client.login_cookie(COOKIE)

asyncio.run(login())

recent_requests = {}  # Store cooldown timestamps

@app.route("/rank", methods=["POST"])
def rank_player():
    data = request.get_json()

    user_id = data.get("userId")
    rank = data.get("rank")
    secret = data.get("secret")

    # Security token
    if secret != SECRET_TOKEN:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    if not user_id or not rank:
        return jsonify({"success": False, "error": "Missing userId or rank"}), 400

    if rank > MAX_RANK:
        return jsonify({"success": False, "error": "Rank too high"}), 400

    # Cooldown check
    now = time.time()
    last = recent_requests.get(user_id, 0)

    if now - last < REQUEST_COOLDOWN:
        remaining = REQUEST_COOLDOWN - (now - last)
        return jsonify({
            "success": False,
            "error": "Cooldown active",
            "remaining_seconds": int(remaining)
        }), 429

    try:
        asyncio.run(client.set_rank(GROUP_ID, user_id, rank))
        recent_requests[user_id] = now
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

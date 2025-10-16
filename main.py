from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv

# Load environment variables from .env (local testing)
load_dotenv()

app = FastAPI()

# ---------- Debug route ----------
@app.get("/debug-env")
async def debug_env():
    """Check if key environment variables are loaded correctly."""
    return {
        "TWITCH_CLIENT_ID": os.getenv("TWITCH_CLIENT_ID"),
        "TWITCH_ACCESS_TOKEN": bool(os.getenv("TWITCH_ACCESS_TOKEN")),  # don't show actual token
        "TWITCH_CLIENT_SECRET": bool(os.getenv("TWITCH_CLIENT_SECRET")),
        "TWITCH_REFRESH_TOKEN": bool(os.getenv("TWITCH_REFRESH_TOKEN")),
        "DISCORD_WEBHOOK_URL": bool(os.getenv("DISCORD_WEBHOOK_URL")),
        "BROADCASTER_ID": os.getenv("BROADCASTER_ID"),
    }

# ---------- Environment variables ----------
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_REFRESH_TOKEN = os.getenv("TWITCH_REFRESH_TOKEN")
BROADCASTER_ID = os.getenv("BROADCASTER_ID")  # Streamer’s user ID

# ---------- Twitch Clip Creation ----------
async def create_clip(request_user: str) -> str:
    """Create a Twitch clip via the Helix API."""
    url = "https://api.twitch.tv/helix/clips"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {TWITCH_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"broadcaster_id": BROADCASTER_ID}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)

    print(f"🎥 Clip creation response {response.status_code}: {response.text}")

    # Success — Twitch accepted the clip request
    if response.status_code == 202:
        data = response.json()
        clip_id = data["data"][0]["id"]
        return f"https://clips.twitch.tv/{clip_id}"

    # Unauthorized — token expired or invalid
    elif response.status_code == 401:
        return "⚠️ Failed to create clip: Unauthorized (check Twitch token)."

    # Stream offline or invalid request
    elif response.status_code == 400:
        return "⚠️ Stream is currently offline — no clip could be made."

    # Generic fallback
    else:
        return f"⚠️ Could not create a clip (status {response.status_code})."

# ---------- Nightbot-Compatible Route ----------
@app.api_route("/twitch-command", methods=["GET", "POST"])
async def twitch_command(request: Request):
    """Endpoint for Nightbot or custom triggers."""
    if request.method == "POST":
        data = await request.json()
        command = data.get("command")
        user = data.get("user")
        message = data.get("message", "")
    else:
        command = request.query_params.get("command")
        user = request.query_params.get("user")
        message = request.query_params.get("message", "")

    if not command or not user:
        return {"error": "Missing required fields"}

    # Handle the !clip command
    if command.lower() == "!clip":
        clip_result = await create_clip(user)
        discord_message = f"🎬 **{user}** requested a clip! {clip_result}"
    else:
        discord_message = f"🎥 **{user}** used `{command}`: {message}"

    # Send message to Discord
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK_URL, json={"content": discord_message})

    return "✅ Message sent to Discord!"

# ---------- Force Refresh Endpoint ----------
@app.get("/force-refresh")
async def force_refresh():
    """
    Manually refresh the Twitch access token using the stored refresh token.
    Returns new access token info (truncated for security).
    """
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "grant_type": "refresh_token",
        "refresh_token": TWITCH_REFRESH_TOKEN,
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, params=params)
        data = response.json()

    print("🔁 Token refresh response:", data)

    if "access_token" in data:
        return {"success": True, "access_token": data["access_token"][:10] + "..."}
    else:
        return {"success": False, "error": data}

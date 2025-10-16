from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

@app.get("/debug-env")
async def debug_env():
    return {
        "TWITCH_CLIENT_ID": os.getenv("TWITCH_CLIENT_ID"),
        "TWITCH_ACCESS_TOKEN": bool(os.getenv("TWITCH_ACCESS_TOKEN")),
        "TWITCH_REFRESH_TOKEN": bool(os.getenv("TWITCH_REFRESH_TOKEN")),
        "DISCORD_WEBHOOK_URL": bool(os.getenv("DISCORD_WEBHOOK_URL")),
    }

# Environment variables
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN")
TWITCH_REFRESH_TOKEN = os.getenv("TWITCH_REFRESH_TOKEN")
BROADCASTER_ID = os.getenv("BROADCASTER_ID")

# ---------- Refresh Twitch Token ----------
async def refresh_twitch_token() -> bool:
    """Refresh the Twitch OAuth token using the refresh token."""
    global TWITCH_ACCESS_TOKEN, TWITCH_REFRESH_TOKEN

    url = "https://id.twitch.tv/oauth2/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": TWITCH_REFRESH_TOKEN,
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=payload)

    if response.status_code == 200:
        data = response.json()
        TWITCH_ACCESS_TOKEN = data["access_token"]
        TWITCH_REFRESH_TOKEN = data["refresh_token"]
        print("✅ Twitch token refreshed successfully.")
        return True
    else:
        print(f"⚠️ Failed to refresh token: {response.status_code} - {response.text}")
        return False

# ---------- Create Twitch Clip ----------
async def create_clip(request_user: str, retry: bool = True) -> str | None:
    """Create a Twitch clip, retrying once if the token was expired."""
    url = "https://api.twitch.tv/helix/clips"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {TWITCH_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"broadcaster_id": BROADCASTER_ID}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)

    print(f"🎬 Clip creation response {response.status_code}: {response.text}")

    if response.status_code == 202:
        data = response.json()
        clip_id = data["data"][0]["id"]
        return f"https://clips.twitch.tv/{clip_id}"

    elif response.status_code == 401 and retry:
        # Try refreshing the token once
        print("🔄 Attempting to refresh Twitch token...")
        if await refresh_twitch_token():
            return await create_clip(request_user, retry=False)
        return "⚠️ Failed to refresh Twitch token. Please reauthorize."

    elif response.status_code == 400:
        return "⚠️ Stream is currently offline — no clip could be made."

    else:
        return f"⚠️ Could not create a clip (status {response.status_code})."

# ---------- Main route ----------
@app.api_route("/twitch-command", methods=["GET", "POST"])
async def twitch_command(request: Request):
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

    if command.lower() == "!clip":
        clip_result = await create_clip(user)
        discord_message = f"🎬 **{user}** requested a clip! {clip_result}"
    else:
        discord_message = f"🎥 **{user}** used `{command}`: {message}"

    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK_URL, json={"content": discord_message})

    return "✅ Message sent to Discord!"


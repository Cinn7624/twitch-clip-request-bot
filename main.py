from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Environment variables
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN")
TWITCH_REFRESH_TOKEN = os.getenv("TWITCH_REFRESH_TOKEN")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
BROADCASTER_ID = os.getenv("BROADCASTER_ID")


# ---------- Refresh Twitch Token ----------
async def refresh_twitch_token() -> str | None:
    """Refresh the Twitch access token using the refresh token."""
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "grant_type": "refresh_token",
        "refresh_token": TWITCH_REFRESH_TOKEN,
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=params)

    if response.status_code == 200:
        data = response.json()
        new_token = data["access_token"]

        # Save to environment for next requests
        os.environ["TWITCH_ACCESS_TOKEN"] = new_token

        print("🔄 Twitch token refreshed successfully.")
        return new_token
    else:
        print(f"⚠️ Token refresh failed: {response.status_code} - {response.text}")
        return None


# ---------- Create a Twitch Clip ----------
async def create_clip(request_user: str, retry: bool = True) -> tuple[str, str]:
    """Create a Twitch clip, retry once if token expired."""
    url = "https://api.twitch.tv/helix/clips"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {os.getenv('TWITCH_ACCESS_TOKEN')}",
        "Content-Type": "application/json",
    }
    payload = {"broadcaster_id": BROADCASTER_ID}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)

    print(f"🎥 Clip creation response {response.status_code}: {response.text}")

    if response.status_code == 202:
        data = response.json()
        clip_id = data["data"][0]["id"]
        clip_url = f"https://clips.twitch.tv/{clip_id}"
        return (
            f"🎬 A new clip was requested by **{request_user}**! {clip_url}",
            f"🎬 {request_user}, your clip has been created! {clip_url}",
        )

    elif response.status_code == 401 and retry:
        # Try to refresh and retry once
        print("🔄 Access token expired — attempting to refresh.")
        new_token = await refresh_twitch_token()
        if new_token:
            return await create_clip(request_user, retry=False)
        else:
            msg = "⚠️ Twitch token refresh failed. Please reauthorize the app."
            return (msg, msg)

    elif response.status_code == 404:
        msg = "⚠️ Clipping is not possible — the stream is currently offline."
        return (msg, msg)

    else:
        msg = f"⚠️ Could not create a clip (status {response.status_code})."
        return (msg, msg)


# ---------- Main Route ----------
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
        discord_message, nightbot_message = await create_clip(user)
    else:
        discord_message = f"🎥 **{user}** used `{command}`: {message}"
        nightbot_message = f"✅ {user}, your command `{command}` was processed!"

    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK_URL, json={"content": discord_message})

    return nightbot_message

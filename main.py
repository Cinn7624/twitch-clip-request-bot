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
TWITCH_AUTH_TOKEN = os.getenv("TWITCH_AUTH_TOKEN")
BROADCASTER_ID = os.getenv("BROADCASTER_ID")  # Streamer’s user ID

# ---------- Function to create a clip ----------
async def create_clip(request_user: str) -> str | None:
    """Create a Twitch clip and return the clip URL or None if it fails."""
    url = "https://api.twitch.tv/helix/clips"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {TWITCH_AUTH_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"broadcaster_id": BROADCASTER_ID}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)

    # Debug print for logs
    print(f"Clip creation response {response.status_code}: {response.text}")

    if response.status_code == 202:
        data = response.json()
        clip_id = data["data"][0]["id"]
        return f"https://clips.twitch.tv/{clip_id}"

    elif response.status_code == 401:
        # Unauthorized (invalid or expired token)
        return "⚠️ Failed to create clip: Unauthorized (check Twitch token)."

    elif response.status_code == 400:
        # Usually means the stream is offline
        return "⚠️ Stream is currently offline — no clip could be made."

    else:
        # Generic fallback message
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

    # Handle clip command
    if command.lower() == "!clip":
        clip_result = await create_clip(user)
        discord_message = f"🎬 **{user}** requested a clip! {clip_result}"
    else:
        discord_message = f"🎥 **{user}** used `{command}`: {message}"

    # Send message to Discord
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK_URL, json={"content": discord_message})

    return "✅ Message sent to Discord!"

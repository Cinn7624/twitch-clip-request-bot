
from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Get the Discord webhook URL from your environment variables
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

@app.api_route("/twitch-command", methods=["GET", "POST"])
async def twitch_command(request: Request):
    """
    Handles both GET and POST requests from Nightbot or other Twitch chat bots.
    Sends a simplified clip request message to Discord and returns a clean response to Nightbot.
    """

    if request.method == "POST":
        data = await request.json()
        command = data.get("command")
        user = data.get("user")
        message = data.get("message", "")
    else:
        command = request.query_params.get("command")
        user = request.query_params.get("user")
        message = request.query_params.get("message", "")

    # Validate incoming data
    if not command or not user:
        return {"error": "Missing required fields"}

    # Build Discord message
    if message:
        discord_message = f"🎬 Clip requested by **{user}** — {message}"
    else:
        discord_message = f"🎬 Clip requested by **{user}**!"

    # Send message to Discord
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK_URL, json={"content": discord_message})

    # ✅ Clean Nightbot response
    return "🎬 Clip request sent!"

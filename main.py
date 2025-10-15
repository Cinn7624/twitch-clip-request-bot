from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv

# Load .env file for secrets
load_dotenv()

app = FastAPI()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

@app.api_route("/clip-request", methods=["GET", "POST"])
async def clip_request(request: Request):
    """
    Handles clip requests coming from Twitch/Nightbot and sends them to Discord.
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

    if not user:
        return {"error": "Missing user"}

    # Format Discord message
    discord_message = (
        f"🎬 **Clip Request Received!**\n"
        f"👤 Requested by: **{user}**\n"
        f"💬 Message: {message if message else 'No description provided.'}\n\n"
        f"⚙️ Action needed: A mod or streamer can capture the clip!"
    )

    # Send to Discord
    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK_URL, json={"content": discord_message})

    return "✅ Clip request sent to Discord!"


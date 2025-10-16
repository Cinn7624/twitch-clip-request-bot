from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

@app.get("/")
async def root():
    return {"message": "Twitch Clip Request Bot is alive!"}

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

    # Format message for Discord
    discord_message = f"🎬 **{user}** requested a clip! Message: {message}"

    # Send to Discord webhook
    if DISCORD_WEBHOOK_URL:
        async with httpx.AsyncClient() as client:
            await client.post(DISCORD_WEBHOOK_URL, json={"content": discord_message})

    return {"status": "✅ Clip request sent to Discord!"}

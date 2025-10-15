from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

@app.api_route("/clip-command", methods=["GET", "POST"])
async def clip_command(request: Request):
    if request.method == "POST":
        data = await request.json()
        user = data.get("user")
    else:
        user = request.query_params.get("user")

    streamer = "StreamerName"  # 🔁 Replace with your streamer's name
    clip_url = f"https://www.twitch.tv/{streamer}/clip/create"

    discord_message = f"🎞️ **{user}** requested a clip!\n👉 Create it here: {clip_url}"

    async with httpx.AsyncClient() as client:
        await client.post(DISCORD_WEBHOOK_URL, json={"content": discord_message})

    return "✅ Clip request sent to Discord!"

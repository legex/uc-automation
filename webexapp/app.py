import json
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from webexapp.webexbotbase import WebexbotBase

load_dotenv()
API_TOKEN = os.getenv("WEBEXBOTTOKEN")
with open("welcome_message.txt", "r") as file:
    welcome_message = file.read()

webexbot = WebexbotBase()
app = FastAPI()
orgId = ""
@app.post("/roomwebhook")
async def room_webhook(request: Request):
    payload = await request.json()
    if payload.get("orgId") != orgId:
        return {"status": "ignored"}
    data = payload.get("data", {})
    room_id = data.get("id")
    if room_id:
        webexbot.send_message(room_id, welcome_message)
    return {"status": "success"}

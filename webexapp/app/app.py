from fastapi import FastAPI, Request
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("WEBEXBOTTOKEN")

url = "https://webexapis.com/v1/contents/Y2lzY29zcGFyazovL3VzL0NPTlRFTlQvODFjOTViZjAtYjQxNy0xMWYwLTgzMGMtMDlmMDA0YzQyMjE1LzA"

payload = {}
headers = {
  'Authorization': f'Bearer {API_TOKEN}'
}

response = requests.request("GET", url, headers=headers, data=payload)

with open("output_file.pdf", "wb") as f:
    f.write(response.content)

app = FastAPI()

@app.post("/roomwebhook")
def room_webhook(request: Request):
    data = request.json()
    print("Received room webhook:", json.dumps(data, indent=2))
    return {"status": "success"}

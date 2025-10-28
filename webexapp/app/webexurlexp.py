import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("WEBEXBOTTOKEN")
url = "https://webexapis.com/v1/webhooks"
ngrok_url = "https://872d3923b6a6.ngrok-free.app"

payload = json.dumps({
  "resource": "rooms",
  "event": "create",
  "targetUrl": f"{ngrok_url}/roomwebhook",
  "name": "MytestwebHook"
})
headers = {
  'Authorization': f'Bearer {API_TOKEN}',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

payload = json.dumps({
  "resource": "messages",
  "event": "all",
  "targetUrl": f"{ngrok_url}/messagewebhook",
  "name": "MytestwebHook"
})
headers = {
  'Authorization': f'Bearer {API_TOKEN}',
  'Content-Type': 'application/json'
}

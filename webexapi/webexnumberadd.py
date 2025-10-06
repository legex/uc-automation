import os
import json
import requests
import pandas as pd
from requests import HTTPError
from dotenv import load_dotenv
from metadata.settings import ACDLOCATIONS, WEBEX_URL, PATCH_LIC_URL
from utils.logger import setup_logger
from webexapi.webexBase import WebexBase

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = setup_logger('numberadd', 'log/numberadd.log')

# Read API token from environment
AUTH_TOKEN = os.getenv('AUTHTOKEN')
if not AUTH_TOKEN:
    raise RuntimeError("AUTHTOKEN environment variable must be set")

headclass = WebexBase()
headers = headclass.build_headers()

def get_location_id(employee_region: str) -> str | None:
    """
    Look up the Webex location ID that matches a given region substring.

    Args:
        employee_region (str): A substring to search in location names
                               (e.g., 'New York', 'London').

    Returns:
        str | None: Location ID if a match is found, otherwise None.

    Logs:
        - Warning if no match is found.
    """
    if ACDLOCATIONS[employee_region]:
        return ACDLOCATIONS[employee_region]
    return None

def addnumber(numbercsv, region):
    locationid = get_location_id(region)
    numdf = pd.read_csv(numbercsv, dtype={'ContactNumber': str})
    phonenumbers = []
    for _, row in numdf.iterrows():
        num = "+"+row['ContactNumber']
        phonenumbers.append(num)
    numberpayload = {
            "phoneNumbers": phonenumbers,
            "numberType": "DID",
            "state": "ACTIVE"
        }
    try:
        url = f"https://webexapis.com/v1/telephony/config/locations/{locationid}/numbers"
        resp = requests.post(url,
                              headers=headers,
                              data=json.dumps(numberpayload),
                              timeout=30)
        resp.raise_for_status()
        return resp.json()
    except HTTPError as e:
        logger.error("HTTP error updating user: %s", e)
    except Exception as e:
        logger.error("General error updating user: %s", e)
    return None

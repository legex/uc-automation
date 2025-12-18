"""
Docstring for webexapi.webexnumberadd
Module to add phone numbers to Webex locations based on region.
"""
import os
import json
import requests
from requests import HTTPError
from dotenv import load_dotenv
from metadata.settings import ACDLOCATIONS
from utils.logger import setup_logger
from utils.numberutility import batch_numbers_by_region
from webexapi.webexBase import WebexBase

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = setup_logger('numberadd', 'log/numberadd.log')
number_by_region = {}
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

def addnumber(numbercsv):
    """
    Docstring for addnumber
    
    :param numbercsv: CSV file containing phone numbers and their associated regions.
    :return: Dictionary mapping regions to API responses.
    """
    batched_numbers = batch_numbers_by_region(numbercsv)
    responses = {}
    for region, phonenumbers in batched_numbers.items():
        locationid = get_location_id(region)
        if not locationid:
            logger.warning("No location ID found for region: %s", region)
            continue
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
            logger.info("Status for %s: %s", region, resp.status_code)
            responses[region] = resp.json()
        except HTTPError as e:
            logger.error("HTTP error updating user: %s", e)
            responses[region] = None
        except Exception as e:
            logger.error("General error updating user: %s", e)
            responses[region] = None
    return responses

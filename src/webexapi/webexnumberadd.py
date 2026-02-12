"""
Docstring for webexapi.webexnumberadd
Module to add phone numbers to Webex locations based on region.
"""
import os
import json
import requests
from requests import HTTPError
from dotenv import load_dotenv
from appdatainternal.settings import ACDLOCATIONS
from utils.logger import setup_logger
from utils.numberutility import batch_numbers_by_region
from webexapi.webexBase import WebexBase
from webexapi.webexoperations import WebexOperations

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = setup_logger('numberadd', '/a/logs/numberadd.log')
number_by_region = {}

headclass = WebexBase()
webex_ops = WebexOperations(headclass.build_headers())
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

def addnumberbatch(numbercsv):
    """
    Docstring for addnumberbatch
    
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

def addnumbersingle(number: str, region: str):
    """
    Docstring for addnumbersingle
    
    :param number: Phone number to add.
    :param region: Region associated with the phone number.
    :return: API response for the added number.
    """
    locationid = get_location_id(region)
    if not locationid:
        logger.warning("No location ID found for region: %s", region)
        return None
    numberpayload = {
            "phoneNumbers": [f"+{number}"],
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
        print(resp.text)
        return {"result": resp.json(), "status_code": resp.status_code}
    except HTTPError as e:
        logger.error("HTTP error updating Number: %s", e)
        return {"result": None, "error": str(e)}
    except Exception as e:
        logger.error("General error updating Number: %s", e)
        return {"result": None, "error": str(e)}

def create_virtual_line(email, phone_number, region):
    """
    Create a virtual line in Webex for a user based on their email.
    
    A virtual line allows a phone number to be shared across multiple devices
    or users in the Webex Calling environment.
    
    Args:
        email (str): User's email address to create the virtual line for.
        phone_number (str): Phone number to assign to the virtual line.
        region (str): Region associated with the user's location.
    
    Returns:
        dict | None: JSON response containing virtual line details including 'id'
                     if successful, otherwise None.
    
    Logs:
        - Error if user ID is not found
        - Warning if location ID is not found for the region
        - Info on successful virtual line creation
        - Error on HTTP or general exceptions
    """
    url = "https://webexapis.com/v1/telephony/config/virtualLines"

    user_id = webex_ops.get_user_by_email(email)
    if not user_id:
        logger.error("User ID not found for email: %s", email)
        return None
    user_info = webex_ops.get_person(user_id)
    location_id = get_location_id(region)
    if not location_id:
        logger.warning("No location ID found for region: %s", region)
        return None

    payload = {
        "firstName": user_info.get("firstName", "Unknown"),
        "lastName": user_info.get("lastName", "Unknown"),
        "displayName": user_info.get("displayName", "Unknown"),
        "phoneNumber": phone_number,
        "locationId": location_id
    }
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        resp.raise_for_status()
        logger.info("Virtual line created successfully for email: %s", email)
        return resp.json()
    except HTTPError as e:
        logger.error("HTTP error creating virtual line for email %s: %s", email, e)
    except Exception as e:
        logger.error("General error creating virtual line for email %s: %s", email, e)
    return None

def assign_virtual_line_to_user(email, phone_number, region):
    """
    Create a virtual line and assign it to a Webex user with shared call appearance.
    
    This function performs a two-step process:
    1. Creates a new virtual line using create_virtual_line()
    2. Assigns the virtual line to the user's device on port 2 as a shared line
    
    Args:
        email (str): User's email address to assign the virtual line to.
        phone_number (str): Phone number to use for the virtual line.
        region (str): Region associated with the user's location.
    
    Returns:
        dict | None: JSON response from the assignment API if successful,
                     otherwise None.
    
    Configuration:
        - Line is assigned to port 2
        - primaryOwner: false
        - lineType: SHARED_CALL_APPEARANCE
        - allowCallDeclineEnabled: true
    
    Logs:
        - Error if user ID is not found
        - Error if virtual line creation fails
        - Info on successful assignment
        - Error on HTTP or general exceptions
    """
    user_id = webex_ops.get_user_by_email(email)
    if not user_id:
        logger.error("User ID not found for email: %s", email)
        return None
    line_create = create_virtual_line(email, phone_number, region)
    if not line_create:
        logger.error("Failed to create virtual line for email: %s", email)
        return None
    line_id = line_create.get("id")
    url = f"https://webexapis.com/v1/people/{user_id}/virtualLines"
    payload = {"members":
               [
                   {
                    "id": line_id,
                    "port": 2,
                    "primaryOwner": "false",
                    "lineType": "SHARED_CALL_APPEARANCE",
                    "allowCallDeclineEnabled": "true"
                    }
                ]
            }
    try:
        resp = requests.put(url, headers=headers, data=json.dumps(payload), timeout=30)
        resp.raise_for_status()
        logger.info("Virtual line assigned successfully to email: %s", email)
        return resp.json()
    except HTTPError as e:
        logger.error("HTTP error assigning virtual line to email %s: %s", email, e)
    except Exception as e:
        logger.error("General error assigning virtual line to email %s: %s", email, e)
    return None

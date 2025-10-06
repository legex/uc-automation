import os
import json
import requests
from requests import HTTPError
from dotenv import load_dotenv
from metadata.settings import license_store, LOCATIONS, WEBEX_URL, PATCH_LIC_URL
from utils.logger import setup_logger
from webexapi.webexBase import WebexBase

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = setup_logger('webexcalls', 'log/webexcalls.log')

# Read API token from environment
AUTH_TOKEN = os.getenv('AUTHTOKEN')
if not AUTH_TOKEN:
    raise RuntimeError("AUTHTOKEN environment variable must be set")

# License IDs sourced from settings metadata
WEBEX_LICENSE_ID = license_store["webexlic"]
UCM_LICENSE_ID = license_store["ucmlic"]

headclass = WebexBase()
headers = headclass.build_headers()
# def headers -> dict:
#     """
#     Build authorization and content headers for Webex API calls.

#     Returns:
#         dict: HTTP headers containing:
#             - Authorization: Bearer token fetched from AUTHTOKEN env var.
#             - Content-Type: application/json
#             - Accept: application/json

#     Raises:
#         RuntimeError: If AUTHTOKEN is not set in the environment.
#     """
#     return {
#         "Authorization": f"Bearer {AUTH_TOKEN}",
#         "Content-Type": "application/json",
#         "Accept": "application/json"
#     }


def query_user_id_by_email(email: str) -> str | None:
    """
    Retrieve a Webex user's unique person ID using their email address.

    Args:
        email (str): User's Webex-registered email address.

    Returns:
        str | None: Webex personId if found, otherwise None.

    Logs:
        - Error if no matching user is found or if API returns an error.

    Possible failures:
        - HTTPError: Networking/API issues.
        - ValueError: Unexpected API response format.
    """
    params = {'email': email}
    try:
        resp = requests.get(WEBEX_URL, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            logger.error("No user found for email: %s", email)
            return None
        return items[0]['id']
    except HTTPError as e:
        logger.error("HTTP error when querying user by email: %s", e)
    except Exception as e:
        logger.error("General error when querying user by email: %s", e)
    return None


def get_person(userid: str) -> dict | None:
    """
    Fetch a Webex user's detailed profile including calling data.

    Args:
        userid (str): Webex personId.

    Returns:
        dict | None: Full user profile JSON object if successful, else None.

    Logs:
        - Error details if API call fails.

    Notes:
        - Adds '?callingData=true' to the query to include calling info.
    """
    url = f"{WEBEX_URL}/{userid}?callingData=true"
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except HTTPError as e:
        logger.error("HTTP error in get_person: %s", e)
    except Exception as e:
        logger.error("General error in get_person: %s", e)
    return None


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
    for region in LOCATIONS['items']:
        if employee_region in region['name']:
            return region['id']
    logger.warning("Region not found: %s", employee_region)
    return None


def patch_license_dn(email: str, extension: str, employee_region: str):
    """
    Update a user's Webex license to Webex Calling (Professional) and remove
    UCM license if present, while also setting locationId and extension.

    This function:
      1. Looks up a Webex user by email.
      2. Fetches their current licenses.
      3. If missing, adds the Webex Calling license with provided location and extension.
      4. Removes UCM license if present.
      5. Sends a PATCH request to update licenses.

    Args:
        email (str): User's Webex-registered email address.
        extension (str): Extension number to assign to the user.
        employee_region (str): Region name substring to determine locationId.

    Returns:
        dict | None: JSON API response if successful, else None.

    Logs:
        - User lookup issues.
        - Missing license cases.
        - HTTP and general API errors.

    API Endpoint:
        PATCH https://webexapis.com/v1/licenses/users

    Notes:
        - Uses the legacy licenses/users API — verify in current Webex API docs for suitability.
        - Requires administrative privileges and the correct org context.
        - AUTHTOKEN must include scopes to manage user licenses.

    Raises:
        HTTPError: If the API request fails due to client/server errors.
    """
    userid = query_user_id_by_email(email)
    if not userid:
        logger.error("User ID not found for email: %s", email)
        return None

    payload = get_person(userid)
    if not payload:
        logger.error("User detail not found for user: %s", userid)
        return None

    location_id = get_location_id(employee_region)
    existing_licenses = set(payload.get("licenses", []))
    licenses_ops = []

    # Add Webex license if missing
    if WEBEX_LICENSE_ID not in existing_licenses:
        licenses_ops.append({
            "id": WEBEX_LICENSE_ID,
            "operation": "add",
            "properties": {
                "locationId": location_id,
                "extension": extension
            }
        })

        # Remove UCM license if present
        if UCM_LICENSE_ID in existing_licenses:
            licenses_ops.append({
                "id": UCM_LICENSE_ID,
                "operation": "remove"
            })

    if not licenses_ops:
        logger.info("No license changes required for %s", email)
        return None

    patch_payload = {
        "email": email,
        "personId": userid,
        "orgId": payload["orgId"],
        "licenses": licenses_ops
    }

    try:
        url = PATCH_LIC_URL
        resp = requests.patch(url,
                              headers=headers,
                              data=json.dumps(patch_payload),
                              timeout=30)
        resp.raise_for_status()
        return resp.json()
    except HTTPError as e:
        logger.error("HTTP error updating user: %s", e)
    except Exception as e:
        logger.error("General error updating user: %s", e)
    return None

def removelicense(email: str, extension: str, employee_region: str):

    userid = query_user_id_by_email(email)
    if not userid:
        logger.error("User ID not found for email: %s", email)
        return None

    payload = get_person(userid)
    if not payload:
        logger.error("User detail not found for user: %s", userid)
        return None

    location_id = get_location_id(employee_region)
    existing_licenses = set(payload.get("licenses", []))
    licenses_ops = []

    # Add Webex license if missing
    if WEBEX_LICENSE_ID in existing_licenses:
        licenses_ops.append({
            "id": WEBEX_LICENSE_ID,
            "operation": "remove"
        })

        # Remove UCM license if present
        if UCM_LICENSE_ID not in existing_licenses:
            licenses_ops.append({
                "id": UCM_LICENSE_ID,
                "operation": "add"
            })

    # if not licenses_ops:
    #     logger.info("No license changes required for %s", email)
    #     return None

    patch_payload = {
        "email": email,
        "personId": userid,
        "orgId": payload["orgId"],
        "licenses": licenses_ops
    }

    try:
        url = "https://webexapis.com/v1/licenses/users"
        resp = requests.patch(url,
                              headers=headers,
                              data=json.dumps(patch_payload),
                              timeout=30)
        resp.raise_for_status()
        return resp.json()
    except HTTPError as e:
        logger.error("HTTP error updating user: %s", e)
    except Exception as e:
        logger.error("General error updating user: %s", e)
    return None


def deactivate_user_account(email: str):
    userid = query_user_id_by_email(email)
    payload = get_person(userid)
    with open("payloadbefore.json",'w') as f:
        json.dump(payload, f, indent=4)
    payload['extension'] = '10'
    payload['locationId'] = "e501815c-f3d0-4dc9-9a7f-9dfa1fa12267"
    #payload['locationId'] = 'Y2lzY29zcGFyazovL3VzL0xPQ0FUSU9OL2U1MDE4MTVjLWYzZDAtNGRjOS05YTdmLTlkZmExZmExMjI2Nw'
    payload['loginEnabled'] = "false"
    license_payload = payload["licenses"]
    if WEBEX_LICENSE_ID not in license_payload:
        license_payload.append(WEBEX_LICENSE_ID)
    payload["licenses"] = license_payload
    #payload.pop("sipAddresses")
    with open("testresponse.json",'w') as f:
        json.dump(payload, f, indent=4)
    url = f"https://webexapis.com/v1/people/{userid}?callingData=true"
    try:
        resp = requests.put(url,
                              headers=headers,
                              data=json.dumps(payload),
                              timeout=30)
        return resp
    except HTTPError as e:
        logger.error("HTTP error updating user: %s", e)
    except Exception as e:
        logger.error("General error updating user: %s", e)
    return None

def remove_webex_license(email: str):

    userid = query_user_id_by_email(email)
    if not userid:
        logger.error("User ID not found for email: %s", email)
        return None

    payload = get_person(userid)
    if not payload:
        logger.error("User detail not found for user: %s", userid)
        return None
    existing_licenses = set(payload.get("licenses", []))
    licenses_ops = []

    # Add Webex license if missing
    if WEBEX_LICENSE_ID in existing_licenses:
        licenses_ops.append({
            "id": WEBEX_LICENSE_ID,
            "operation": "remove"
        })

        # Remove UCM license if present

    # if not licenses_ops:
    #     logger.info("No license changes required for %s", email)
    #     return None

    patch_payload = {
        "email": email,
        "personId": userid,
        "orgId": payload["orgId"],
        "licenses": licenses_ops
    }

    try:
        url = "https://webexapis.com/v1/licenses/users"
        resp = requests.patch(url,
                              headers=headers,
                              data=json.dumps(patch_payload),
                              timeout=30)
        resp.raise_for_status()
        return resp.json()
    except HTTPError as e:
        logger.error("HTTP error updating user: %s", e)
    except Exception as e:
        logger.error("General error updating user: %s", e)
    return None

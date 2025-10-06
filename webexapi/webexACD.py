import json
import requests
from requests import HTTPError
from metadata.settings import license_store, ACDLOCATIONS, WEBEX_URL, PATCH_LIC_URL
from utils.logger import setup_logger
from webexapi.webexBase import WebexBase


logger = setup_logger('webexacdmig', 'log/webexacdmig.log')

WEBEX_LICENSE_ID = license_store["webexlic"]
UCM_LICENSE_ID = license_store["ucmlic"]

headclass = WebexBase()
headers = headclass.build_headers()

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
    if ACDLOCATIONS[employee_region]:
        return ACDLOCATIONS[employee_region]
    return None

def patch_dn_acd(email: str, telephone: str, extension: str, employee_region: str):
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
    licenses_ops = [{
            "id": WEBEX_LICENSE_ID,
            "operation": "add",
            "properties": {
                "locationId": location_id,
                "phoneNumber": telephone,
                "extension": extension
            }
            }]


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

def removelicenseacd(email: str):

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
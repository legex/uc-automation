"""Webex General Migration Module.

This module handles Webex Calling license migration for general users.
It manages the addition of Webex Calling Professional licenses and removal
of UCM licenses, along with location and extension configuration.

Classes:
    WebexGenMigration: Manages general Webex user license and calling configuration.
"""
import os
import json
import requests
from requests import HTTPError
from dotenv import load_dotenv
from src.metadata.settings import license_store, LOCATIONS, WEBEX_URL, PATCH_LIC_URL
from src.utils.logger import setup_logger
from src.webexapi.webexBase import WebexBase
from src.webexapi.webexoperations import WebexOperation

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = setup_logger('webexgeneral', '/a/logs/webexgeneral.log')

# Read API token from environment
AUTH_TOKEN = os.getenv('AUTHTOKEN')
if not AUTH_TOKEN:
    raise RuntimeError("AUTHTOKEN environment variable must be set")

# License IDs sourced from settings metadata
WEBEX_LICENSE_ID = license_store["webexlic"]
UCM_LICENSE_ID = license_store["ucmlic"]

class WebexGenMigration:
    def __init__(self):
        headclass = WebexBase()
        self.baseoperations = WebexOperation()
        self.headers = headclass.build_headers()

    def patch_license_dn(self, email: str, extension: str, employee_region: str):
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
        userid = self.baseoperations.query_user_id_by_email(email)
        if not userid:
            logger.error("User ID not found for email: %s", email)
            return None

        payload = self.baseoperations.get_person(userid)
        if not payload:
            logger.error("User detail not found for user: %s", userid)
            return None
        if payload.get("loginEnabled") is False:
            logger.warning("User %s is disabled in Webex", email)
            return None
        location_id = self.baseoperations.get_location_id(employee_region)
        existing_licenses = set(payload.get("licenses", []))
        licenses_ops = [{
                "id": WEBEX_LICENSE_ID,
                "operation": "add",
                "properties": {
                    "locationId": location_id,
                    "extension": extension
                }
            }]

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
                                headers=self.headers,
                                data=json.dumps(patch_payload),
                                timeout=30)
            resp.raise_for_status()
            return resp.json()
        except HTTPError as e:
            logger.error("HTTP error updating user: %s", e)
        except Exception as e:
            logger.error("General error updating user: %s", e)
        return None

    def patch_dn(self, email: str, extension: str, employee_region: str):
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
        userid = self.baseoperations.query_user_id_by_email(email)
        if not userid:
            logger.error("User ID not found for email: %s", email)
            return None

        payload = self.baseoperations.get_person(userid)
        if not payload:
            logger.error("User detail not found for user: %s", userid)
            return None

        location_id = self.baseoperations.get_location_id(employee_region)
        existing_licenses = set(payload.get("licenses", []))
        licenses_ops = [{
                "id": WEBEX_LICENSE_ID,
                "operation": "add",
                "properties": {
                    "locationId": location_id,
                    "extension": extension
                }
            }]
        if UCM_LICENSE_ID in existing_licenses:
            licenses_ops.append({
                "id": UCM_LICENSE_ID,
                "operation": "remove"
            })
        patch_payload = {
            "email": email,
            "personId": userid,
            "orgId": payload["orgId"],
            "licenses": licenses_ops
        }
        print(patch_payload)
        try:
            url = PATCH_LIC_URL
            resp = requests.patch(url,
                                headers=self.headers,
                                data=json.dumps(patch_payload),
                                timeout=30)
            resp.raise_for_status()
            return resp.json()
        except HTTPError as e:
            logger.error("HTTP error updating user: %s", e)
        except Exception as e:
            logger.error("General error updating user: %s", e)
        return None



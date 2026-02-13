"""Webex Operations Module.

This module provides common operations for interacting with Webex APIs,
including user lookups, location queries, and license management.

Classes:
    WebexOperation: Handles core Webex API operations like user queries,
                    location lookups, and license updates.
"""
import os
import json
import requests
from requests import HTTPError
from appdatainternal.config import get_webex_license_config, get_webex_urls, get_locations_config
from appdatainternal.settings import  LOCATIONS, profileid_blr
from utils.logger import setup_logger
from webexapi.webexBase import WebexBase

# Initialize logger
logger = setup_logger('webexops', '/a/logs/webexops.log')

license_store = get_webex_license_config()
WEBEX_LICENSE_ID = license_store["webexlic"]
UCM_LICENSE_ID = license_store["ucmlic"]
webexurls = get_webex_urls()
WEBEX_URL = webexurls["WEBEX_URL"]
ACDLOCATIONS = get_locations_config()
class WebexOperation:

    def __init__(self):
        headclass = WebexBase()
        self.headers = headclass.build_headers()

    def query_user_id_by_email(self, email: str) -> str | None:
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
            resp = requests.get(WEBEX_URL, headers=self.headers, params=params, timeout=30)
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


    def get_person(self, userid: str) -> dict | None:
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
            resp = requests.get(url, headers=self.headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except HTTPError as e:
            logger.error("HTTP error in get_person: %s", e)
        except Exception as e:
            logger.error("General error in get_person: %s", e)
        return None


    def get_location_id_nonwebex(self, employee_region: str) -> str | None:
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

    def get_location_id(self, employee_region: str) -> str | None:
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
        if ACDLOCATIONS[employee_region]['id']:
            return ACDLOCATIONS[employee_region]['id']
        return None

    def get_location_id_acd(self, employee_region: str) -> str | None:
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
        if ACDLOCATIONS[employee_region]['id']:
            return ACDLOCATIONS[employee_region]
        return None
    def removelicense(self, email: str):

        userid = self.query_user_id_by_email(email)
        if not userid:
            logger.error("User ID not found for email: %s", email)
            return None

        payload = self.get_person(userid)
        if not payload:
            logger.error("User detail not found for user: %s", userid)
            return None

        existing_licenses = set(payload.get("licenses", []))
        licenses_ops = []

        # Remove Webex license if missing
        if WEBEX_LICENSE_ID in existing_licenses:
            licenses_ops.append({
                "id": WEBEX_LICENSE_ID,
                "operation": "remove"
            })

            # Add UCM license if present
        if UCM_LICENSE_ID not in existing_licenses:
            licenses_ops.append({
                "id": UCM_LICENSE_ID,
                "operation": "add"
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
    
    def update_calling_behavior(self, userid, profileid_blr):
        if not profileid_blr:
            logger.error("Profile ID for calling behavior is not provided.")
            return None
        url=f'https://webexapis.com/v1/people/{userid}/features/callingBehavior'
        payload = json.dumps({"profileId":profileid_blr})
        try:
            resp = requests.put(url,
                                headers=self.headers,
                                data=payload,
                                timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            logger.error("HTTP error updating calling behavior: %s", e)
        except Exception as e:
            logger.error("General error updating calling behavior: %s", e)
        return None 

    def remove_webex_license(self, email: str, region_India: bool = False):

        userid = self.query_user_id_by_email(email)
        if not userid:
            logger.error("User ID not found for email: %s", email)
            return None

        payload = self.get_person(userid)
        if not payload:
            logger.error("User detail not found for user: %s", userid)
            return None
        existing_licenses = set(payload.get("licenses", []))
        licenses_ops = []

        # Add Webex license if missing
        if UCM_LICENSE_ID not in existing_licenses:
            licenses_ops.append({
                "id": UCM_LICENSE_ID,
                "operation": "add"
            })

            # Remove Webex license if present
            if WEBEX_LICENSE_ID in existing_licenses:
                licenses_ops.append({
                    "id": WEBEX_LICENSE_ID,
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
                                headers=self.headers,
                                data=json.dumps(patch_payload),
                                timeout=30)
            resp.raise_for_status()
            return resp.json()
        except HTTPError as e:
            logger.error("HTTP error updating user: %s", e)
        except Exception as e:
            logger.error("General error updating user: %s", e)
        if region_India:
            try:
                self.update_calling_behavior(userid, profileid_blr)
            except Exception as e:
                logger.error("Error updating calling behavior for India region: %s", e)
        return None

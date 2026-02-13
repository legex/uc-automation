import json
from dotenv import load_dotenv
import os
import pandas as pd
from appdatainternal.environment import get_env_config


load_dotenv()

ENV = get_env_config()

def get_webex_license_config():
    if ENV == "PROD":
        license_store = {
            "ucmlic": "Y2lzY29zcGFyazovL3VzL0xJQ0VOU0UvYTM3NDkzMTUtYWUwOS00YTUyLTgwNmMtMmMzMjIyZmE3YzJjOlVDUFJFTV9jMzMyOWQzMi0xNmVkLTQxNDUtOTUyNS02M2FjYjRiMzFiMjA",
            "webexlic": "Y2lzY29zcGFyazovL3VzL0xJQ0VOU0UvYTM3NDkzMTUtYWUwOS00YTUyLTgwNmMtMmMzMjIyZmE3YzJjOkJDU1REXzFhNGRhOTZiLTNmYWUtNGVlYi1hZDYwLWFkNTA3MTE4NzFkMA"
        }
    else:
        license_store = {
            "ucmlic": "Y2lzY29zcGFyazovL3VzL0xJQ0VOU0UvYmMyZDgzNzItMzIzZS00ZGVmLTg1MWItZGMxM2M2ODQ0ZjExOlVDUFJFTV9jMzMyOWQzMi0xNmVkLTQxNDUtOTUyNS02M2FjYjRiMzFiMjA",
            "webexlic": "Y2lzY29zcGFyazovL3VzL0xJQ0VOU0UvYmMyZDgzNzItMzIzZS00ZGVmLTg1MWItZGMxM2M2ODQ0ZjExOkJDU1REXzBhNmM3NGI1LWZiYjktNDU3NS04MTdjLTFjZjc1ZTBlNjhlOQ"
        }
    return license_store


def get_locations_config():
    with open("appdatainternal/acd_locations.json", 'r') as f:
        ACDLOCATIONS = json.load(f)
    return ACDLOCATIONS

def cucm_servers():
    with open("appdatainternal/cucm.json", 'r') as f:
        CUCM_ADDRESSES = json.load(f)
    return CUCM_ADDRESSES

def get_ldap_creds():
    ldap_creds = {'SERVER': "wauth.corp.akamai.com:636",
                'LDAP_USERNAME': "akamai.com\\svc_tmt_account",
                'LDAP_PASSWORD': None
                }
    
    ldapsecretfile = "/a/secrets/app/ldap_user/ldap_user.opaque"
    if ENV == "PROD":
        with open(ldapsecretfile, 'r') as f:
            ldap_creds["LDAP_PASSWORD"] = f.read().strip()
    else:
        ldap_creds["LDAP_PASSWORD"] = os.environ.get("LDAPPASS", "default_ldap_password")
    return ldap_creds

def get_resultfile_location():
    if ENV == "PROD":
        resultfile_path = "tmp/resultfiles"
    else:
        resultfile_path = "/tmp/resultfiles/"
    def ensure_resultfile_path(resultfile_path):
        """Ensure the result file path exists."""
        if not os.path.exists(resultfile_path):
            os.makedirs(resultfile_path)
        return resultfile_path
    return ensure_resultfile_path(resultfile_path)

def get_cucm_credentials():
        """
        Returns the CUCM AXL credentials.

        Returns:
            tuple: A tuple containing (username, password).
        """
        ucm_creds = {"PROD": {"AXL_USERNAME": "admin1",
                            "AXL_PASSWORD": None},
                    "STAG": {"AXL_USERNAME": "admin1",
                            "AXL_PASSWORD": None},
                    "LOCAL": {"AXL_USERNAME": "administrator",
                            "AXL_PASSWORD": None}
                    }
        if ENV == "PROD" or ENV == "STAG":
            passfile = "/a/secrets/app/cucm_user/cucm_user.opaque"
            with open(passfile, 'r') as pf:
                ucm_creds["PROD"]["AXL_PASSWORD"] = pf.read().strip()
                print("Read CUCM password from file")
        else:
            ucm_creds["LOCAL"]["AXL_PASSWORD"] = os.environ.get("AXL_PASSWORD", "default_cucm_password")
        return ucm_creds[ENV]

def get_webex_token():
    """
    Retrieve the Webex API token.

    Returns:
        str: The Webex API token.
    """
    if ENV == "PROD":
        tokenfile = "/a/secrets/app/webex_token/webex_token.opaque"
        with open(tokenfile, 'r') as tf:
            token = tf.read().strip()
            print("Read Webex token from file")
    else:
        token = os.environ.get("AUTHTOKEN", None)
    return token

def get_webex_urls():
    urls = {
        "WEBEX_URL": "https://webexapis.com/v1/people",
        "PATCH_LIC_URL": "https://webexapis.com/v1/licenses/users"
    }
    return urls

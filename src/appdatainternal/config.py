import json
from dotenv import load_dotenv
import os
import pandas as pd
from appdatainternal.environment import get_env_config


load_dotenv()

ENV = get_env_config()
print(f"Application environment set to: {ENV}")
def get_webex_license_config():
    if ENV == "PROD" or ENV == "STAG" or ENV == "LOCAL":
        license_store = {
            "ucmlic":"licenseid",
            "ucmlic":"licenseid",
        }
    else:
        license_store = {
            "ucmlic":"licenseid",
            "ucmlic":"licenseid",
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
    ldap_creds = {'SERVER':"ldapserver",
                'LDAP_USERNAME':"ldapuser",
                'LDAP_PASSWORD': None
                }
    
    ldapsecretfile = "path_to_ldap_password_file"
    if ENV == "PROD" or ENV == "STAG":
        with open(ldapsecretfile, 'r') as f:
            ldap_creds["LDAP_PASSWORD"] = f.read().strip()
    else:
        ldap_creds["LDAP_PASSWORD"] = os.environ.get("LDAPPASS", "default_ldap_password")
    return ldap_creds

def get_resultfile_location():
    if ENV == "PROD" or ENV == "STAG":
        resultfile_path = "tmp/resultfiles"
    else:
        resultfile_path = "tmp/resultfiles/"
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
        ucm_creds = {"PROD": {"AXL_USERNAME": "username_prod",
                            "AXL_PASSWORD": None},
                    "STAG": {"AXL_USERNAME": "username_stag",
                            "AXL_PASSWORD": None},
                    "LOCAL": {"AXL_USERNAME": "username_local",
                            "AXL_PASSWORD": None}
                    }
        if ENV == "PROD" or ENV == "STAG":
            passfile = "path_to_cucm_password_file"
            with open(passfile, 'r') as pf:
                ucm_creds["PROD"]["AXL_PASSWORD"] = pf.read().strip()
                print("Read CUCM password from file")
        else:
            ucm_creds["LOCAL"]["AXL_PASSWORD"] = os.environ.get("AXL_PASSWORD", "default_cucm_password")
        return ucm_creds[ENV]

def get_cucm_rl_mapping():
    with open("appdatainternal/cucm_rl.json", 'r') as f:
        cucm_rl_mapping = json.load(f)
    return cucm_rl_mapping

def get_webex_token():
    """
    Retrieve the Webex API token.

    Returns:
        str: The Webex API token.
    """
    if ENV == "PROD" or ENV == "STAG":
        tokenfile = "path_to_webex_token_file"
        with open(tokenfile, 'r') as tf:
            token = tf.read().strip()
            print("Read Webex token from file")
    else:
        token = os.environ.get("INTEGRATIONTOKEN", None)
    return token

def get_webex_urls():
    urls = {
        "WEBEX_URL": "https://webexapis.com/v1/people",
        "PATCH_LIC_URL": "https://webexapis.com/v1/licenses/users"
    }
    return urls

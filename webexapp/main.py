import os
import sys
import pandas as pd
from ldapapi.updateldap import update_contacts_num, update_contacts_num_withDID
from cucmapi.axlop import AXLOperations
from cucmapi.axlroutepattern import AXLRoutePatternOperations
from metadata.settings import extension_prefix, exclude_list
from webexapi.webexgeneral import WebexGenMigration
from webexapi.webexACD import WebexMigACD
from webexapi.webexoperations import WebexOperation
from utils.logger import setup_logger

logger = setup_logger('webmainapp', 'log/webmainapp.log')

prefixes = extension_prefix
exclude_list = exclude_list
def batch_update_ldap(file, filename):
    """Update CUCM Extension"""
    df = pd.read_csv(file, dtype={'targetNum': str})
    status_on_ad = ""
    for _, row in df.iterrows():
        username = row['UserId']
        extension = row['targetNum']
        externalnumber = row.get('ExternalNumber', None)
        if username not in exclude_list:
            if externalnumber:
                try:
                    ad_result = update_contacts_num_withDID(username, extension, externalnumber)
                    status_on_ad = "Success" if ad_result else "Failed"
                except Exception as e:
                    logger.error("Error updating AD with DID for %s: %s", username, e)
                    status_on_ad = "Error"
            else:
                try:
                    ad_result = update_contacts_num(username, extension)
                    status_on_ad = "Success" if ad_result else "Failed"
                except Exception as e:
                    logger.error("Error updating AD for %s: %s", username, e)
                    status_on_ad = "Error"
        else:
            logger.info("User %s is in Exclude list", username)
            status_on_ad = "Skipped"
        ad_result = {
            "username": username,
            "extension": extension,
            "status_on_ad": status_on_ad
        }
        pd.DataFrame([ad_result]).to_csv(f"Aresultfiles/ldap_response_{filename}", mode='a', header=False, index=False)
    return "Script Run is Finished"
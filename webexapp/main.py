import os
import pandas as pd
from ldapapi.updateldap import (
    update_contacts_num,
    update_contacts_num_withDID,
    update_general_contacts_num_withDID
)
from cucmapi.axlop import AXLOperations
from cucmapi.axlroutepattern import AXLRoutePatternOperations
from metadata.settings import extension_prefix, exclude_list
from webexapi.webexgeneral import WebexGenMigration
from webexapi.webexACD import WebexMigACD
from webexapi.webexoperations import WebexOperation
from utils.logger import setup_logger

logger = setup_logger('webmainapp', 'log/webmainapp.log')

prefixes = extension_prefix
excluded_list = exclude_list
axloperations = AXLOperations()
axlrp = AXLRoutePatternOperations()
webex_mig_gen = WebexGenMigration()
webex_acd_mig = WebexMigACD()
currentdir = os.getcwd()
webop = WebexOperation()

def batch_update_ldap(file, filename):
    """Update CUCM Extension"""
    df = pd.read_csv(file, dtype={'targetNum': str})
    status_on_ad = ""
    for _, row in df.iterrows():
        username = row['UserId']
        extension = row['targetNum']
        externalnumber = row.get('ExternalNumber', None)
        if username not in excluded_list:
            if externalnumber:
                try:
                    ad_result = update_contacts_num_withDID(
                        username, extension, externalnumber)
                    status_on_ad = "Success" if ad_result else "Failed"
                except (ConnectionError, ValueError, AttributeError) as e:
                    logger.error(
                        "Error updating AD with DID for %s: %s", username, e)
                    status_on_ad = "Error"
            else:
                try:
                    ad_result = update_contacts_num(username, extension)
                    status_on_ad = "Success" if ad_result else "Failed"
                except (ConnectionError, ValueError, AttributeError) as e:
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
        pd.DataFrame(
            [ad_result]).to_csv(f"resultfiles/ldap_response_{filename}",
                                mode='a',
                                header=False,
                                index=False
                                )
    return "Script Run is Finished"

def batch_update_webex_gen(file, filename):
    """Update Webex Extension"""
    df = pd.read_csv(file, dtype={'extension': str, 'ContactNumber': str})
    for _, row in df.iterrows():
        username = row['UserId']
        phonenumber = row.get('ContactNumber', None)
        extension = row['extension']
        region = row['Country']
        ad_num = prefixes[region]+row['extension']
        email = row["Email"]
        status_on_ad = ""
        status_on_webex = ""
        print(extension)
        if username not in excluded_list:
            if phonenumber:
                try:
                    webex_results = webex_acd_mig.patch_dn_acd(
                        email,
                        phonenumber,
                        extension,
                        region
                    )
                    status_on_webex = "Success" if webex_results else "Failed"
                except (ConnectionError, ValueError, AttributeError) as e:
                    logger.error(
                        "Error updating Webex with DID for %s: %s", username, e)
                    status_on_webex = "Error"
                if status_on_webex == "Success":
                    try:
                        ad_result = update_general_contacts_num_withDID(
                            username,
                            phonenumber,
                            ad_num
                        )
                        status_on_ad = "Success" if ad_result else "Failed"
                    except (ConnectionError, ValueError, AttributeError) as e:
                        logger.error(
                            "Error updating AD for %s: %s", username, e)
                        status_on_ad = "Error"
            try:
                webex_results = webex_mig_gen.patch_license_dn(
                    email,
                    extension,
                    region
                )
                status_on_webex = "Success" if webex_results else "Failed"
            except (ConnectionError, ValueError, AttributeError) as e:
                logger.error("Error updating Webex for %s: %s", username, e)
                status_on_webex = "Error"
            if status_on_webex == "Success":
                try:
                    ad_result = update_contacts_num(
                        username,
                        ad_num
                    )
                    status_on_ad = "Success" if ad_result else "Failed"
                except (ConnectionError, ValueError, AttributeError) as e:
                    logger.error("Error updating AD for %s: %s", username, e)
                    status_on_ad = "Error"
            else:
                status_on_ad = "Skipped"
        else:
            logger.info("User %s is in Exclude list", username)
            status_on_ad = "Skipped"

        webex_mig_result = {
            "username": username,
            "email": email,
            "FullExtension": ad_num,
            "phoneNum": phonenumber,
            "extension": extension,
            "region": region,
            "status_on_cucm": status_on_webex,
            "status_on_ad": status_on_ad
        }
        pd.DataFrame(
            [webex_mig_result]).to_csv(f"resultfiles/webex_migresult_{filename}",
                                       mode='a',
                                       header=False,
                                       index=False
                                       )
    return "Script Run is Finished"

def batch_update_webex_acd(file, filename):
    """Update Webex Extension"""
    df = pd.read_excel(file, dtype={'extension': str, 'ContactNumber': str})
    for _, row in df.iterrows():
        username = row['UserId']
        phonenumber = row['ContactNumber']
        extension = row['extension']
        region = row['Country']
        ad_num = prefixes[region]+row['extension']
        email = row["Email"]
        print(extension)

        try:
            webex_results = webex_acd_mig.patch_dn_acd(
                email,
                phonenumber,
                extension,
                region
            )
            status_on_webex = "Success" if webex_results else "Failed"
        except (ConnectionError, ValueError, AttributeError) as e:
            logger.error("Error updating CUCM for %s: %s", username, e)
            status_on_webex = "Error"
        if status_on_webex == "Success":
            try:
                ad_result = update_contacts_num_withDID(
                    username,
                    phonenumber,
                    ad_num
                )
                status_on_ad = "Success" if ad_result else "Failed"
            except (ConnectionError, ValueError, AttributeError) as e:
                logger.error("Error updating AD for %s: %s", username, e)
                status_on_ad = "Error"
        else:
            status_on_ad = "Skipped"

        acd_result = {
            "username": username,
            "email": email,
            "phoneNum": phonenumber,
            "extension": extension,
            "region": region,
            "status_on_cucm": status_on_webex,
            "status_on_ad": status_on_ad
        }
        pd.DataFrame([acd_result]).to_csv(
            f"resultfiles/acd_migresult_{filename}",
            mode='a',
            header=False,
            index=False
            )
    return "Script Run is Finished"


def batch_routepattern_auto(file, filename):
    """Create Route Pattern in CUCM from CSV"""
    df = pd.read_csv(file, dtype={'ContactNumber': str})
    for _, row in df.iterrows():
        routepattern = f"{row['ContactNumber']}"
        username = row["UserId"]
        try:
            update_partition = axlrp.update_line(routepattern)
            update_rp = axlrp.create_routepattern(routepattern, username)
            status_on_cucm = "Success" if update_rp else "Failed"
            status_partition = "Success" if update_partition else "Failed"
        except (ConnectionError, ValueError, AttributeError) as e:
            logger.error(
                "Error updating CUCM for route pattern %s: %s", routepattern, e)
            status_on_cucm = "Error"
            status_partition = "Error"
        results = {
            "routepattern": routepattern,
            "status_on_cucm": status_on_cucm,
            "rp_update_status": status_partition,
        }
        pd.DataFrame([results]).to_csv(
            f"resultfiles/rpupdateresult_{filename}",
            mode='a',
            header=False,
            index=False
            )
    return "Script Run is Finished"

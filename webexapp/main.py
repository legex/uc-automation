import os
import pandas as pd
from ldapapi.updateldap import (
    update_contacts_num,
    update_contacts_num_withDID,
    update_general_contacts_num_withDID,
    update_acdcontacts_num
)
from cucmapi.axlop import AXLOperations
from cucmapi.axlroutepattern import AXLRoutePatternOperations
from metadata.settings import extension_prefix, exclude_list
from webexapi.webexgeneral import WebexGenMigration
from webexapi.webexACD import WebexMigACD
from webexapi.webexoperations import WebexOperation
from utils.logger import setup_logger

logger = setup_logger('webmainapp', 'log/webmainapp.log')
logger.setLevel('DEBUG')
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
    logger.info("Starting batch LDAP update for file: %s", filename)
    df = pd.read_csv(file, dtype={'targetNum': str})
    logger.info("Loaded %d rows from CSV file", len(df))
    status_on_ad = ""
    for idx, row in df.iterrows():
        logger.debug("Processing row %d", idx + 1)
        username = row['UserId']
        extension = row['targetNum']
        externalnumber = row.get('ExternalNumber', None)
        logger.info("Processing user: %s, extension: %s, external: %s", username, extension, externalnumber)
        if username not in excluded_list:
            if externalnumber:
                try:
                    logger.debug("Updating LDAP with DID for user: %s", username)
                    ad_result = update_general_contacts_num_withDID(
                        username, extension, externalnumber)
                    status_on_ad = "Success" if ad_result else "Failed"
                    logger.info("LDAP update with DID for %s: %s", username, status_on_ad)
                except (Exception) as e:
                    logger.error(
                        "Error updating AD with DID for %s: %s", username, e)
                    status_on_ad = "Error"
            else:
                try:
                    logger.debug("Updating LDAP without DID for user: %s", username)
                    ad_result = update_contacts_num(username, extension)
                    status_on_ad = "Success" if ad_result else "Failed"
                    logger.info("LDAP update for %s: %s", username, status_on_ad)
                except (Exception) as e:
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
    logger.info("Batch LDAP update completed for file: %s", filename)
    return "Script Run is Finished"

def batch_update_ldap_acd(file, filename):
    """Update CUCM Extension"""
    logger.info("Starting batch LDAP update for file: %s", filename)
    df = pd.read_csv(file, dtype={'targetNum': str})
    logger.info("Loaded %d rows from CSV file", len(df))
    status_on_ad = ""
    for idx, row in df.iterrows():
        logger.debug("Processing row %d", idx + 1)
        username = row['UserId']
        extension = row['targetNum']
        externalnumber = row.get('ExternalNumber', None)
        logger.info("Processing user: %s, extension: %s, external: %s", username, extension, externalnumber)
        if username not in excluded_list:
            if externalnumber:
                try:
                    logger.debug("Updating LDAP with DID for user: %s", username)
                    ad_result = update_contacts_num_withDID(
                        username, extension, externalnumber)
                    status_on_ad = "Success" if ad_result else "Failed"
                    logger.info("LDAP update with DID for %s: %s", username, status_on_ad)
                except (Exception) as e:
                    logger.error(
                        "Error updating AD with DID for %s: %s", username, e)
                    status_on_ad = "Error"
            else:
                try:
                    logger.debug("Updating LDAP without DID for user: %s", username)
                    ad_result = update_acdcontacts_num(username, extension)
                    status_on_ad = "Success" if ad_result else "Failed"
                    logger.info("LDAP update for %s: %s", username, status_on_ad)
                except (Exception) as e:
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
    logger.info("Batch LDAP update completed for file: %s", filename)
    return "Script Run is Finished"

def batch_update_webex_gen(file, filename):
    """Update Webex Extension"""
    logger.info("Starting batch Webex General update for file: %s", filename)
    df = pd.read_csv(file, dtype=str, na_filter=True, keep_default_na=True)
    logger.info("Loaded %d rows from CSV file", len(df))
    df['ContactNumber'] = df['ContactNumber'].where(
        pd.notna(df['ContactNumber']), None  # NaN → None
    )
    
    # Now safe to strip (no NaN left)
    df['ContactNumber'] = df['ContactNumber'].replace('', None)

    for idx, row in df.iterrows():
        logger.debug("Processing row %d", idx + 1)
        username = row['UserId']
        phonenumber = row["ContactNumber"]
        extension = row['extension']
        region = row['Country']
        ad_num = prefixes[region]+row['extension']
        email = row["Email"]
        status_on_webex = ""
        logger.info("Processing user: %s, email: %s, extension: %s, region: %s", username, email, extension, region)
        if username not in excluded_list:
            if phonenumber is not None and phonenumber.lower() != 'none':
                contact = "+" + phonenumber
                logger.debug("Processing with contact number: %s for user: %s", contact, username)
                try:
                    logger.debug("Updating Webex ACD for user: %s", username)
                    webex_results = webex_acd_mig.patch_dn_acd(
                        email,
                        contact,
                        extension,
                        region
                    )
                    print(webex_results)
                    status_on_webex = "Success" if webex_results else "Failed"
                    logger.info("Webex ACD update for %s: %s", username, status_on_webex)
                except Exception as e:
                    logger.error(
                        "Error updating Webex with DID for %s: %s", username, e)
                    status_on_webex = "Error"
            else:
                try:
                    logger.debug("Updating Webex license Extension for user: %s", username)
                    webex_results = webex_mig_gen.patch_license_dn(
                        email,
                        extension,
                        region
                    )
                    status_on_webex = "Success" if webex_results else "Failed"
                    logger.info("Webex license Extension update for %s: %s", username, status_on_webex)
                except (Exception) as e:
                    logger.error("Error updating Webex Extension for %s: %s", username, e)
                    status_on_webex = "Error"              
        else:
            logger.info("User %s is in Exclude list", username)

        webex_mig_result = {
            "username": username,
            "email": email,
            "FullExtension": ad_num,
            "phoneNum": phonenumber,
            "extension": extension,
            "region": region,
            "status_on_cucm": status_on_webex,
        }
        pd.DataFrame(
            [webex_mig_result]).to_csv(f"resultfiles/webex_migresult_{filename}",
                                       mode='a',
                                       header=False,
                                       index=False
                                       )
    logger.info("Batch Webex General update completed for file: %s", filename)
    return "Script Run is Finished"

def batch_update_webex_acd(file, filename):
    """Update Webex Extension"""
    logger.info("Starting batch Webex ACD update for file: %s", filename)
    df = pd.read_excel(file, dtype={'extension': str, 'ContactNumber': str})
    logger.info("Loaded %d rows from Excel file", len(df))
    for idx, row in df.iterrows():
        logger.debug("Processing row %d", idx + 1)
        username = row['UserId']
        phonenumber = "+" + row['ContactNumber']
        extension = row['extension']
        region = row['Country']
        ad_num = prefixes[region]+row['extension']
        email = row["Email"]
        logger.info("Processing user: %s, email: %s, extension: %s, phone: %s", username, email, extension, phonenumber)

        try:
            logger.debug("Updating Webex ACD for user: %s", username)
            webex_results = webex_acd_mig.patch_dn_acd(
                email,
                phonenumber,
                extension,
                region
            )
            status_on_webex = "Success" if webex_results else "Failed"
            logger.info("Webex ACD update for %s: %s", username, status_on_webex)
        except (Exception) as e:
            logger.error("Error updating CUCM for %s: %s", username, e)
            status_on_webex = "Error"
        if status_on_webex == "Success":
            try:
                logger.debug("Updating LDAP with DID for user: %s", username)
                ad_result = update_contacts_num_withDID(
                    username,
                    phonenumber,
                    ad_num
                )
                status_on_ad = "Success" if ad_result else "Failed"
                logger.info("LDAP update for %s: %s", username, status_on_ad)
            except (Exception) as e:
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
    logger.info("Batch Webex ACD update completed for file: %s", filename)
    return "Script Run is Finished"


def batch_routepattern_auto(file, filename):
    """Create Route Pattern in CUCM from CSV"""
    logger.info("Starting batch route pattern creation for file: %s", filename)
    df = pd.read_csv(file, dtype={'ContactNumber': str})
    logger.info("Loaded %d rows from CSV file", len(df))
    for idx, row in df.iterrows():
        logger.debug("Processing row %d", idx + 1)
        routepattern = f"{row['ContactNumber']}"
        username = row["UserId"]
        logger.info("Processing route pattern: %s for user: %s", routepattern, username)
        try:
            logger.debug("Updating line partition for route pattern: %s", routepattern)
            update_partition = axlrp.update_line(routepattern)
            logger.debug("Creating route pattern: %s", routepattern)
            update_rp = axlrp.create_routepattern(routepattern, username)
            status_on_cucm = "Success" if update_rp else "Failed"
            status_partition = "Success" if update_partition else "Failed"
            logger.info("Route pattern %s - CUCM: %s, Partition: %s", routepattern, status_on_cucm, status_partition)
        except (Exception) as e:
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
    logger.info("Batch route pattern creation completed for file: %s", filename)
    return "Script Run is Finished"

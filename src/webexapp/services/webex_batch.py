"""Webex Batch Update Service.

This module provides functions for batch updating Webex user configurations
from CSV/Excel files. It handles both general and ACD user migrations
with license management and extension assignment.

Functions:
    batch_update_webex_gen: Process general Webex updates from CSV.
    batch_update_webex_acd: Process ACD Webex updates from Excel.
"""
import pandas as pd
from webexapi.webexgeneral import WebexGenMigration
from webexapi.webexACD import WebexMigACD
from webexapi.webexoperations import WebexOperation
from appdatainternal.settings import exclude_list
from appdatainternal.config import get_resultfile_location, get_locations_config
from utils.logger import setup_logger

logger = setup_logger('webex_batch', '/a/logs/webex_batch.log')

location_config = get_locations_config()
excluded_list = exclude_list
resultpath = get_resultfile_location()
webex_mig_gen = WebexGenMigration()
webex_acd_mig = WebexMigACD()
webop = WebexOperation()

def batch_update_webex_gen(file, filename, exclude_users_override=None):
    """Update Webex Extension"""
    logger.info("Starting batch Webex General update for file: %s", filename)
    effective_excluded_list = exclude_users_override if exclude_users_override is not None else excluded_list
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
        ad_num = location_config[region]['prefix']+extension
        email = row["Email"]
        status_on_webex = ""
        logger.info("Processing user: %s, email: %s, extension: %s, region: %s", username, email, extension, region)
        if username not in effective_excluded_list:
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
                    status_on_webex = "Success" if webex_results["result"] else "Failed"
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
                    status_on_webex = "Success" if webex_results["result"] else "Failed"
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
            "status_on_webex": status_on_webex,
        }
        pd.DataFrame(
            [webex_mig_result]).to_csv(f"{resultpath}/webex_migresult_{filename}",
                                       mode='a',
                                       header=False,
                                       index=False
                                       )
    logger.info("Batch Webex General update completed for file: %s", filename)
    return "Script Run is Finished"

def batch_update_webex_acd(file, filename, exclude_users_override=None):
    """Update Webex Extension"""
    logger.info("Starting batch Webex ACD update for file: %s", filename)
    df = pd.read_csv(file, dtype={'extension': str, 'ContactNumber': str})
    df['ContactNumber'] = df['ContactNumber'].where(
        pd.notna(df['ContactNumber']), None  # NaN → None
    )
    logger.info("Loaded %d rows from Excel file", len(df))
    effective_excluded_list = exclude_users_override if exclude_users_override is not None else []
    for idx, row in df.iterrows():
        logger.debug("Processing row %d", idx + 1)
        username = row['UserId'].strip()
        phonenumber = row['ContactNumber']
        extension = row['extension'].strip()
        region = row['Country'].strip()
        ad_num = location_config[region]['prefix']+extension
        email = row["Email"].strip()
        logger.info("Processing user: %s, email: %s, extension: %s, phone: %s", username, email, extension, phonenumber)
        if username not in effective_excluded_list:
            if phonenumber is not None and phonenumber.lower() != 'none':
                phonenumber = "+" + phonenumber.strip()
                logger.debug("Processing with contact number: %s for user: %s", phonenumber, username)

                try:
                    logger.debug("Updating Webex ACD for user: %s", username)
                    webex_results = webex_acd_mig.patch_dn_acd(
                        email,
                        phonenumber,
                        extension,
                        region
                    )
                    status_on_webex = "Success" if webex_results["result"] else "Failed"
                    logger.info("Webex ACD update for %s: %s", username, status_on_webex)
                except (Exception) as e:
                    logger.error("Error updating CUCM for %s: %s", username, e)
                    status_on_webex = "Error"
            else:
                try:
                    logger.debug("Updating Webex license Extension for user: %s", username)
                    webex_results = webex_mig_gen.patch_license_dn(
                        email,
                        extension,
                        region
                    )
                    status_on_webex = "Success" if webex_results["result"] else "Failed"
                    logger.info("Webex license Extension update for %s: %s", username, status_on_webex)
                except (Exception) as e:
                    logger.error("Error updating Webex Extension for %s: %s", username, e)
                    status_on_webex = "Error"
        else:
            logger.info("User %s is in Exclude list", username)
            status_on_webex = "Skipped"
        acd_result = {
            "username": username,
            "email": email,
            "phoneNum": phonenumber if phonenumber else "",
            "FullExtension": ad_num,
            "extension": extension,
            "region": region,
            "status_on_webex": status_on_webex
        }
        pd.DataFrame([acd_result]).to_csv(
            f"{resultpath}/acd_migresult_{filename}",
            mode='a',
            header=False,
            index=False
            )
    logger.info("Batch Webex ACD update completed for file: %s", filename)
    return "Script Run is Finished"

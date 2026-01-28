"""Webex Batch Update Service.

This module provides functions for batch updating Webex user configurations
from CSV/Excel files. It handles both general and ACD user migrations
with license management and extension assignment.

Functions:
    batch_update_webex_gen: Process general Webex updates from CSV.
    batch_update_webex_acd: Process ACD Webex updates from Excel.
"""
import pandas as pd
from src.webexapi.webexgeneral import WebexGenMigration
from src.webexapi.webexACD import WebexMigACD
from src.webexapi.webexoperations import WebexOperation
from src.metadata.settings import extension_prefix, exclude_list
from src.utils.logger import setup_logger

logger = setup_logger('webex_batch', 'log/webex_batch.log')

prefixes = extension_prefix
excluded_list = exclude_list

webex_mig_gen = WebexGenMigration()
webex_acd_mig = WebexMigACD()
webop = WebexOperation()

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
        else:
            status_on_ad = "Skipped"

        acd_result = {
            "username": username,
            "email": email,
            "phoneNum": phonenumber,
            "extension": ad_num,
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
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
from utils.csv_helper import create_csv_holder
from webexapi.webexnumberadd import addnumbersingle
from webexapp.webexbotbase import WebexbotBase

logger = setup_logger('webex_batch', '/a/logs/webex_batch.log')

location_config = get_locations_config()
excluded_list = exclude_list
resultpath = get_resultfile_location()
webex_mig_gen = WebexGenMigration()
webex_acd_mig = WebexMigACD()
webop = WebexOperation()
webex_bot = WebexbotBase()

def batch_update_webex_gen(file, filename, current_user, exclude_users_override=None):
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
        results = []
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
        
        results.append({
            "username": username,
            "email": email,
            "FullExtension": ad_num,
            "phoneNum": phonenumber,
            "extension": extension,
            "region": region,
            "status_on_webex": status_on_webex,
        })
        csv_content = create_csv_holder(results, ["username", "email", "FullExtension", "phoneNum", "extension", "region", "status_on_webex"])
        webex_bot.send_message_with_attachment(
            f'{current_user}@akamai.com',
            filename,
            message=f"Batch Webex General update completed for file: {filename}",
            csv_text=csv_content,
        )
    logger.info("Batch Webex General update completed for file: %s", filename)
    return "Script Run is Finished"

def batch_update_webex_acd(file, filename, current_user, exclude_users_override=None):
    """Update Webex Extension"""
    logger.info("Starting batch Webex ACD update for file: %s", filename)
    df = pd.read_csv(file, dtype={'extension': str, 'ContactNumber': str})
    df['ContactNumber'] = df['ContactNumber'].where(
        pd.notna(df['ContactNumber']), None  # NaN → None
    )
    results=[]
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
        results.append({
            "username": username,
            "email": email,
            "phoneNum": phonenumber if phonenumber else "",
            "FullExtension": ad_num,
            "extension": extension,
            "region": region,
            "status_on_webex": status_on_webex
        })
        csv_content = create_csv_holder(results, ["username", "email", "phoneNum", "FullExtension", "extension", "region", "status_on_webex"])
        webex_bot.send_message_with_attachment(
            f'{current_user}@akamai.com',
            filename,
            message=f"Batch Webex General update completed for file: {filename}",
            csv_text=csv_content,
        )
    logger.info("Batch Webex ACD update completed for file: %s", filename)
    return "Script Run is Finished"


def batch_remove_license(file, filename, current_user, region_India):
    """Remove Webex License from CSV"""
    logger.info("Starting batch Webex license removal for file: %s", filename)
    df = pd.read_csv(file, dtype=str)
    logger.info("Loaded %d rows from CSV file", len(df))
    results=[]
    for idx, row in df.iterrows():
        logger.debug("Processing row %d", idx + 1)
        email = row["Email"].strip()
        logger.info("Processing license removal for email: %s", email)
        try:
            logger.debug("Removing Webex license for email: %s", email)
            webex_results = webop.remove_webex_license(email, region_India=region_India)
            status_on_webex = "Success" if webex_results["result"] else "Failed"
            logger.info("Webex license removal for %s: %s", email, status_on_webex)
        except (Exception) as e:
            logger.error("Error removing Webex license for %s: %s", email, e)
            status_on_webex = "Error"
        removal_result = {
            "email": email,
            "status_on_webex": status_on_webex
        }
        results.append(removal_result)
    csv_content = create_csv_holder(results, ["email", "status_on_webex"])
    webex_bot.send_message_with_attachment(
        f'{current_user}@akamai.com',
        filename,
        message=f"Batch Webex license removal completed for file: {filename}",
        csv_text=csv_content,
    )
    logger.info("Batch Webex license removal completed for file: %s", filename)
    return "Script Run is Finished"


def batch_add_number(file, filename, current_user):
    """Add Webex Number from CSV"""
    logger.info("Starting batch Webex number addition for file: %s", filename)
    df = pd.read_csv(file, dtype=str)
    logger.info("Loaded %d rows from CSV file", len(df))
    results=[]
    for idx, row in df.iterrows():
        logger.debug("Processing row %d", idx + 1)
        region = row["Country"].strip()
        phonenumber = row["ContactNumber"].strip()
        logger.info("Processing number addition for phone: %s, region: %s", phonenumber, region)
        try:
            logger.debug("Adding Webex number for phone: %s, region: %s", phonenumber, region)
            webex_results = addnumbersingle(phonenumber, region)
            status_on_webex = "Success" if webex_results["status_code"] in [204, 200] else "Failed"
            logger.info("Webex number addition for phone: %s: %s", phonenumber, status_on_webex)
        except (Exception) as e:
            logger.error("Error adding Webex number for phone: %s: %s", phonenumber, e)
            status_on_webex = "Error"
        addition_result = {
            "Country": region,
            "phoneNum": phonenumber,
            "status_on_webex": status_on_webex
        }
        results.append(addition_result)
    csv_content = create_csv_holder(results, ["Country", "phoneNum", "status_on_webex"])
    webex_bot.send_message_with_attachment(
        f'{current_user}@akamai.com',
        filename,
        message=f"Batch Webex number addition completed for file: {filename}",
        csv_text=csv_content,
    )
    logger.info("Batch Webex number addition completed for file: %s", filename)
    return "Script Run is Finished"

"""LDAP Batch Update Service.

This module provides functions for batch updating LDAP contact numbers
from CSV files. It supports both general and ACD user updates with
optional external DID numbers.

Functions:
    batch_update_ldap: Process general LDAP updates from CSV.
    batch_update_ldap_acd: Process ACD LDAP updates from CSV.
"""
import time
import pandas as pd
from ldapapi.updateldap import (
    update_contacts_num,
    update_contacts_num_withDID,
    update_general_contacts_num_withDID,
    update_acdcontacts_num
)
from appdatainternal.settings import exclude_list
from appdatainternal.config import get_resultfile_location
from utils.logger import setup_logger
from utils.csv_helper import create_csv_holder
from src.webexapp.webexbotbase import WebexbotBase

logger = setup_logger('ldapbatch', '/a/logs/ldapbatch.log')

excluded_list = exclude_list
resultpath = get_resultfile_location()
webex_bot = WebexbotBase()

def batch_update_ldap(file, filename, current_user):
    """Update CUCM Extension"""
    logger.info("Starting batch LDAP update for file: %s", filename)
    df = pd.read_csv(file, dtype=str, na_filter=True, keep_default_na=True)
    logger.info("Loaded %d rows from CSV file", len(df))
    df['ExternalNumber'] = df['ExternalNumber'].where(
        pd.notna(df['ExternalNumber']), None  # NaN → None
    )
    # Now safe to strip (no NaN left)
    df['ExternalNumber'] = df['ExternalNumber'].replace('', None)
    status_on_ad = ""
    results = []
    for idx, row in df.iterrows():
        logger.debug("Processing row %d", idx + 1)
        username = row['UserId']
        extension = row['extension']
        externalnumber = row.get('ExternalNumber', None)
        logger.info("Processing user: %s, extension: %s, external: %s", username, extension, externalnumber)
        if username not in excluded_list:
            if externalnumber is not None and externalnumber.lower() != 'none':
                externalnumber = externalnumber.strip()
                externalnumber = externalnumber.removesuffix(".0")
                try:
                    logger.debug("Updating LDAP with DID for user: %s", username)
                    ad_result = update_general_contacts_num_withDID(
                        username, extension, f"+{externalnumber}")
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
        results.append({
            "username": username,
            "extension": extension,
            "status_on_ad": status_on_ad
        })
    csv_content = create_csv_holder(results, ["username", "extension", "status_on_ad"])
    webex_bot.send_message_with_attachment(
        f'{current_user}@akamai.com',
        filename,
        message=f"Batch LDAP update completed for file: {filename}",
        csv_text=csv_content,
    )
    logger.info("Batch LDAP update completed for file: %s", filename)
    return "Script Run is Finished"

def batch_update_ldap_acd(file, filename, current_user):
    """Update CUCM Extension"""
    logger.info("Starting batch LDAP update for file: %s", filename)
    df = pd.read_csv(file, dtype=str, na_filter=True, keep_default_na=True)
    logger.info("Loaded %d rows from CSV file", len(df))
    df['ExternalNumber'] = df['ExternalNumber'].where(
        pd.notna(df['ExternalNumber']), None  # NaN → None
    )
    # Now safe to strip (no NaN left)
    df['ExternalNumber'] = df['ExternalNumber'].replace('', None)
    logger.info("Loaded %d rows from CSV file", len(df))
    status_on_ad = ""
    results = []
    for idx, row in df.iterrows():
        logger.debug("Processing row %d", idx + 1)
        username = row['UserId']
        extension = row['extension']  # Remove trailing .0 if present
        if extension:
            extension = extension.strip()
            extension = extension.removesuffix(".0")
        externalnumber = row.get('ExternalNumber', None)
        logger.info("Processing user: %s, extension: %s, external: %s", username, extension, externalnumber)
        if externalnumber:
            externalnumber = externalnumber.strip()
            externalnumber = externalnumber.removesuffix(".0")
            try:
                logger.debug("Updating LDAP with DID for user: %s", username)
                ad_result = update_contacts_num_withDID(
                    username, extension, f"+{externalnumber}")
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
        ad_result = {
            "username": username,
            "extension": extension,
            "status_on_ad": status_on_ad
        }
        results.append(ad_result)
        
    csv_content = create_csv_holder(results, ["username", "extension", "status_on_ad"])
    webex_bot.send_message_with_attachment(
        f'{current_user}@akamai.com',
        filename,
        message=f"Batch LDAP update completed for file: {filename}",
        csv_text=csv_content
    )
    logger.info("Batch LDAP update completed for file: %s", filename)
    return "Script Run is Finished"

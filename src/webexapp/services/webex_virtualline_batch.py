import pandas as pd
from webexapi.webexnumberadd import assign_virtual_line_to_user
from appdatainternal.config import get_resultfile_location, get_locations_config
from utils.logger import setup_logger

logger = setup_logger('webex_virtualline_batch', '/a/logs/webex_virtualline_batch.log')

resultfile_loc = get_resultfile_location()
location_config = get_locations_config()

def batch_assign_virtual_line(file, filename):
    """Assign virtual line to user"""
    logger.info("Starting batch virtual line assignment for file: %s", filename)
    df = pd.read_csv(file, dtype=str, na_filter=True, keep_default_na=True)
    logger.info("Loaded %d rows from CSV file", len(df))
    for idx, row in df.iterrows():
        logger.debug("Processing row %d", idx + 1)
        username = row['UserId']
        phoneNumber = row['ContactNumber']
        region = row['LineCountry']
        email = row["Email"]
        status_on_webex = ""
        logger.info("Processing user: %s, email: %s, phone number: %s, region: %s", username, email, phoneNumber, region)
        try:
            logger.debug("Assigning virtual line for user: %s with number: %s", username, phoneNumber)
            assign_results = assign_virtual_line_to_user(email, f"+{phoneNumber}", region)
            logger.debug("Assign results: %s", assign_results)
            status_on_webex = "Success" if assign_results["result"] else "Failed"
            logger.info("Virtual line assignment for %s: %s", username, status_on_webex)
        except Exception as e:
            logger.error(
                "Error assigning virtual line for %s: %s", username, e)
            status_on_webex = "Error"
        
        vl_assign_results = {
            "UserId": username,
            "Email": email,
            "ContactNumber": phoneNumber,
            "Region": region,
            "Status": status_on_webex
        }
        pd.DataFrame([vl_assign_results]).to_csv(
            f"{resultfile_loc}/virtual_line_result_{filename}",
            mode='a',
            header=False,
            index=False)

        logger.info("Batch Webex General update completed for file: %s", filename)
    return "Script Run is Finished"

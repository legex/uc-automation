import os
import pandas as pd
from ldapapi.updateldap import update_contacts_num
from cucmapi.axlop import AXLOperations
from webexapi.webexauto import patch_license_dn
from utils.logger import setup_logger

logger = setup_logger('mainapp', 'log/mainapp.log')


axloperations = AXLOperations()
filename = input("Enter File Name: ")
currentdir = os.getcwd()

def batch_update_cucm(csvlocation):
    """Update CUCM Extension"""
    filepath = os.path.join(currentdir, csvlocation)
    df = pd.read_csv(filepath)

    endresult = []
    for _, row in df.iterrows():
        username = row['username']
        extension = row['extension']

        try:
            cucm_result = axloperations.update_phone(username, extension)
            status_on_cucm = "Success" if cucm_result else "Failed"
        except Exception as e:
            logger.error("Error updating CUCM for %s: %s", username, e)
            status_on_cucm = "Error"
        if status_on_cucm == "Success":
            try:
                ad_result = update_contacts_num(username, extension)
                status_on_ad = "Success" if ad_result else "Failed"
            except Exception as e:
                logger.error("Error updating AD for %s: %s", username, e)
                status_on_ad = "Error"
        else:
            status_on_ad = "Skipped"

        endresult.append({
            "username": username,
            "extension": extension,
            "status_on_cucm": status_on_cucm,
            "status_on_ad": status_on_ad
        })

    pd.DataFrame(endresult).to_csv("CUCM_migration.csv", index=False)
    return "Script Run is Finished"

def batch_update_webex(csvlocation):
    """Update Webex Extension"""
    filepath = os.path.join(currentdir, csvlocation)
    df = pd.read_csv(filepath)

    endresult = []
    for _, row in df.iterrows():
        username = row['username']
        extension = row['extension']
        region = row['employee_region']

        try:
            webex_results = patch_license_dn(username, extension, region)
            status_on_webex = "Success" if webex_results else "Failed"
        except Exception as e:
            logger.error("Error updating CUCM for %s: %s", username, e)
            status_on_webex = "Error"
        if status_on_webex == "Success":
            try:
                ad_result = update_contacts_num(username, extension)
                status_on_ad = "Success" if ad_result else "Failed"
            except Exception as e:
                logger.error("Error updating AD for %s: %s", username, e)
                status_on_ad = "Error"
        else:
            status_on_ad = "Skipped"

        endresult.append({
            "username": username,
            "extension": extension,
            "region": region,
            "status_on_cucm": status_on_webex,
            "status_on_ad": status_on_ad
        })

    pd.DataFrame(endresult).to_csv("webex_migration.csv", index=False)
    return "Script Run is Finished"


if __name__ == "__main__":
    csv_file = input("Enter CSV file name: ")
    change_tpye = input("Choose from below:\nEnter 1 for CUCM Migration\n Enter 2 for Webex Migration")
    if int(change_tpye) == 1:
        batch_update_cucm(csv_file)
    if int(change_tpye) == 2:
        batch_update_webex(csv_file)
    else:
        print("Incorrect Selection")

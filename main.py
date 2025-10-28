import os
import sys
import pandas as pd
from ldapapi.updateldap import update_contacts_num
from cucmapi.axlop import AXLOperations
from cucmapi.axlroutepattern import AXLRoutePatternOperations
from metadata.settings import extension_prefix
from webexapi.webexgeneral import WebexGenMigration
from webexapi.webexACD import WebexMigACD
from utils.logger import setup_logger

logger = setup_logger('mainapp', 'log/mainapp.log')
prefixes = extension_prefix
axloperations = AXLOperations()
axlroutepattern = AXLRoutePatternOperations()
webex_mig_gen = WebexGenMigration()
webex_acd_mig = WebexMigACD()
currentdir = os.getcwd()

def batch_update_cucm(csvlocation):
    """Update CUCM Extension"""
    filepath = os.path.join(currentdir, csvlocation)
    df = pd.read_csv(filepath, dtype={'targetNum': str})
    posinput = ["Y","y", "Yes", "yes"]
    exclude_df = pd.read_csv("excludelist.csv")
    exclude_list = exclude_df['UserId'].tolist()
    status_on_ad = ""
    status_on_cucm = ""
    endresult = []
    counter = 0
    for _, row in df.iterrows():
        username = row['UserId']
        extension = row['targetNum']
        if username not in exclude_list:
            try:
                cucm_result = axloperations.update_phone(username, extension)
                status_on_cucm = "Success" if cucm_result else "Failed"
            except Exception as e:
                logger.error("Error updating CUCM for %s: %s", username, e)
                status_on_cucm = "Success"
            if status_on_cucm == "Success":
                try:
                    ad_result = update_contacts_num(username, extension)
                    status_on_ad = "Success" if ad_result else "Failed"
                except Exception as e:
                    logger.error("Error updating AD for %s: %s", username, e)
                    status_on_ad = "Error"
            else:
                status_on_ad = "Skipped"
            counter += 1
            print(f"Processed {counter} records")
            if counter == 3000:
                print("Do you wish to continue? Yes/Y or No/N")
                userinput = input()
                if userinput in posinput:
                    counter = 0
                else:
                    sys.exit("Exiting as per user request")
        else:
            logger.info("User %s is in Exclude list", username)

        endresult.append({
            "username": username,
            "extension": extension,
            "status_on_cucm": status_on_cucm,
            "status_on_ad": status_on_ad
        })

    pd.DataFrame(endresult).to_csv("CUCM_migrationfirst5.csv", index=False)
    return "Script Run is Finished"

def batch_update_webex_gen(csvlocation):
    """Update Webex Extension"""
    filepath = os.path.join(currentdir, csvlocation)
    df = pd.read_csv(filepath, dtype={'extension': str})

    endresult = []
    for _, row in df.iterrows():
        username = row['UserId']
        extension = row['extension']
        region = row['Country']
        ad_num = prefixes[region]+row['extension']
        email = row["Email"]
        print(extension)

        try:
            webex_results = webex_mig_gen.patch_license_dn(email, extension, region)
            #webex_results = removelicense(email, extension, region)
            status_on_webex = "Success" if webex_results else "Failed"
        except Exception as e:
            logger.error("Error updating CUCM for %s: %s", username, e)
            status_on_webex = "Error"
        if status_on_webex == "Success":
            try:
                ad_result = update_contacts_num(username, ad_num)
                status_on_ad = "Success" if ad_result else "Failed"
            except Exception as e:
                logger.error("Error updating AD for %s: %s", username, e)
                status_on_ad = "Error"
        else:
            status_on_ad = "Skipped"

        endresult.append({
            "username": username,
            "email": email,
            "TargetDID": ad_num,
            "extension": extension,
            "region": region,
            "status_on_cucm": status_on_webex,
            "status_on_ad": status_on_ad
        })

    pd.DataFrame(endresult).to_csv("linode_nodidwebex_migration.csv", index=False)
    return "Script Run is Finished"

def batch_update_webex_acd(csvlocation):
    """Update Webex Extension"""
    filepath = os.path.join(currentdir, csvlocation)
    df = pd.read_excel(filepath, dtype={'extension': str, 'ContactNumber': str})

    endresult = []
    for _, row in df.iterrows():
        username = row['UserId']
        phonenumber = row['ContactNumber']
        extension = row['extension']
        ad_num = prefixes[region]+row['extension']
        region = row['Country']
        email = row["Email"]
        print(extension)

        try:
            webex_results = webex_acd_mig.patch_dn_acd(email, phonenumber, extension, region)
            #removelicenseacd(email)
            status_on_webex = "Success" if webex_results else "Failed"
        except Exception as e:
            logger.error("Error updating CUCM for %s: %s", username, e)
            status_on_webex = "Error"
        if status_on_webex == "Success":
            try:
                ad_result = update_contacts_num(username, ad_num)
                status_on_ad = "Success" if ad_result else "Failed"
            except Exception as e:
                logger.error("Error updating AD for %s: %s", username, e)
                status_on_ad = "Error"
        else:
            status_on_ad = "Skipped"

        endresult.append({
            "username": username,
            "email": email,
            "phoneNum": phonenumber,
            "extension": extension,
            "region": region,
            "status_on_cucm": status_on_webex,
            "status_on_ad": status_on_ad
        })

    pd.DataFrame(endresult).to_csv("acd_linodewebex_migration_remaining.csv", index=False)
    return "Script Run is Finished"

def adupdate(csvlocation):
    filepath = os.path.join(currentdir, csvlocation)
    df = pd.read_excel(filepath, dtype={'extension': str, 'ContactNumber': str})

    endresult = []
    for _, row in df.iterrows():
        username = row['UserId']
        region = row['Country']
        extension = prefixes[region]+row['extension']
        try:
            ad_result = update_contacts_num(username, extension)
            status_on_ad = "Success" if ad_result else "Failed"
        except Exception as e:
            logger.error("Error updating AD for %s: %s", username, e)
            status_on_ad = "Error"
        endresult.append({
            "username": username,
            "extension": extension,
            "region": region,
            "status_on_ad": status_on_ad
        })
    pd.DataFrame(endresult).to_csv("linode_AD_update.csv", index=False)
    return "Script Run over"

def batch_update_ad_cucm_extension(csvlocation):
    """Update CUCM Extension"""
    filepath = os.path.join(currentdir, csvlocation)
    df = pd.read_csv(filepath, dtype={'targetNum': str})
    exclude_df = pd.read_csv("excludelist.csv")
    exclude_list = exclude_df['UserId'].tolist()
    status_on_ad = ""
    endresult = []
    for _, row in df.iterrows():
        username = row['UserId']
        extension = row['targetNum']
        if username not in exclude_list:
            try:
                ad_result = update_contacts_num(username, extension)
                status_on_ad = "Success" if ad_result else "Failed"
            except Exception as e:
                logger.error("Error updating AD for %s: %s", username, e)
                status_on_ad = "Error"
        else:
            logger.info("User %s is in Exclude list", username)
            status_on_ad = "Skipped"
    endresult.append({
            "username": username,
            "extension": extension,
            "status_on_ad": status_on_ad
        })

    pd.DataFrame(endresult).to_csv("AD_update_correction.csv", index=False)
    return "Script Run is Finished"

def batch_update_routepattern(csvlocation):
    """Update CUCM Route Pattern"""
    filepath = os.path.join(currentdir, csvlocation)
    df = pd.read_csv(filepath, dtype={'pattern': str})
    endresult = []
    for _, row in df.iterrows():
        routepattern = row['pattern']
        username = row["username"]
        try:
            update_partition = axlroutepattern.update_line(routepattern, "PT-Global-Internal")
            update_rp = axlroutepattern.create_routepattern(routepattern, username)
            status_on_cucm = "Success" if update_rp else "Failed"
            status_partition = "Success" if update_partition else "Failed"
        except Exception as e:
            logger.error("Error updating CUCM for route pattern %s: %s", routepattern, e)
            status_on_cucm = "Error"
        endresult.append({
            "routepattern": routepattern,
            "status_on_cucm": status_on_cucm,
            "rp_update_status": status_partition
        })

    pd.DataFrame(endresult).to_csv("Routepattern_update.csv", index=False)
    return "Script Run is Finished"

if __name__ == "__main__":
    csv_file = input("Enter CSV file name: ")
    STRTOPRINT = """Choose from below:
    Enter 1 for CUCM Migration
    Enter 2 for Webex Migration
    Enter 3 for Webex ACD Agent Migration
    Enter 4 for Webex ACD Agent Migration
    Enter 5 for AD Extension Update Correction
    """
    print(STRTOPRINT)
    change_type = input()
    if int(change_type) == 1:
        batch_update_cucm(csv_file)
    if int(change_type) == 2:
        batch_update_webex_gen(csv_file)
    if int(change_type) == 3:
        batch_update_webex_acd(csv_file)
    if int(change_type) == 4:
        adupdate(csv_file)
    if int(change_type) == 5:
        batch_update_ad_cucm_extension(csv_file)
    else:
        print("Incorrect Selection")

"""Route Pattern Batch Creation Service.

This module provides functions for batch creating route patterns in CUCM
from CSV files. It handles line partition updates and route pattern creation.

Functions:
    batch_routepattern_auto: Create route patterns from CSV file.
"""
import pandas as pd
from cucmapi.axlop import AXLOperations
from cucmapi.axlroutepattern import AXLRoutePatternOperations
from utils.logger import setup_logger
from appdatainternal.config import get_resultfile_location

resultpath = get_resultfile_location()
logger = setup_logger('rp_batch', '/a/logs/rp_batch.log')
axloperations = AXLOperations()
axlrp = AXLRoutePatternOperations()

def batch_routepattern_auto(file, filename, service):
    if not service:
        logger.debug("No service provided to batch_routepattern_auto")
    """Create Route Pattern in CUCM from CSV"""
    logger.info("Starting batch route pattern creation for file: %s", filename)
    df = pd.read_csv(file, dtype={'ContactNumber': str})
    logger.info("Loaded %d rows from CSV file", len(df))
    for idx, row in df.iterrows():
        logger.debug("Processing row %d", idx + 1)
        routepattern = f"\+{row['ContactNumber']}"
        username = row["UserId"]
        logger.info("Processing route pattern: %s for user: %s", routepattern, username)
        try:
            logger.debug("Updating line partition for route pattern: %s", routepattern)
            update_partition = axlrp.update_line(routepattern, service=service)
            logger.debug("Creating route pattern: %s", routepattern)
            update_rp = axlrp.create_routepattern(routepattern, username, service=service)
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
            f"{resultpath}/rpupdateresult_{filename}",
            mode='a',
            header=False,
            index=False
            )
    logger.info("Batch route pattern creation completed for file: %s", filename)
    return "Script Run is Finished"

def batch_updateroutepatterns_auto(file, filename, partition, service):
    """Update Route Pattern in CUCM from CSV"""
    if not service:
        logger.debug("No service provided to batch_updateroutepatterns_auto")
    logger.info("Starting batch route pattern update for file: %s", filename)
    df = pd.read_csv(file, dtype={'PatternToUpdate': str})
    logger.info("Loaded %d rows from CSV file", len(df))
    for idx, row in df.iterrows():
        logger.debug("Processing row %d", idx + 1)
        routepattern = f"\+{row['PatternToUpdate']}"
        logger.info("Processing route pattern: %s update partition to %s", routepattern, partition)
        try:
            logger.debug("Updating route pattern: %s", routepattern)
            update_rp = axlrp.update_routepattern(routepattern, partition, service=service)
            status_on_cucm = "Success" if update_rp else "Failed"
            logger.info("Route pattern %s update status on CUCM: %s", routepattern, status_on_cucm)
        except (Exception) as e:
            logger.error(
                "Error updating CUCM for route pattern %s: %s", routepattern, e)
            status_on_cucm = "Error"
        results = {
            "routepattern": routepattern,
            "status_on_cucm": status_on_cucm,
        }
        pd.DataFrame([results]).to_csv(
            f"{resultpath}/rpupdateresult_{filename}",
            mode='a',
            header=False,
            index=False
            )
    logger.info("Batch route pattern update completed for file: %s", filename)
    return "Script Run is Finished"


def batch_updatecallforwarding_auto(file, filename, service):
    """Update Call Forwarding for Route Pattern in CUCM from CSV"""
    if not service:
        logger.debug("No service provided to batch_updatecallforwarding_auto")
    logger.info("Starting batch call forwarding update for file: %s", filename)
    df = pd.read_csv(file, dtype={'PatternToUpdate': str, 'DestinationPattern': str})
    logger.info("Loaded %d rows from CSV file", len(df))
    for idx, row in df.iterrows():
        logger.debug("Processing row %d", idx + 1)
        routepattern = f"\+{row['PatternToUpdate']}"
        destination_pattern = f"+{row['DestinationPattern']}"
        logger.info("Processing route pattern: %s update call forwarding to destination: %s", routepattern, destination_pattern)
        try:
            logger.debug("Updating call forwarding for route pattern: %s", routepattern)
            update_rp = axlrp.update_callforwarding(routepattern, destination_pattern, service=service)
            status_on_cucm = "Success" if update_rp else "Failed"
            logger.info("Call forwarding update for route pattern %s on CUCM: %s", routepattern, status_on_cucm)
        except (Exception) as e:
            logger.error(
                "Error updating call forwarding on CUCM for route pattern %s: %s", routepattern, e)
            status_on_cucm = "Error"
        results = {
            "routepattern": routepattern,
            "destination_pattern": destination_pattern,
            "status_on_cucm": status_on_cucm,
        }
        pd.DataFrame([results]).to_csv(
            f"{resultpath}/callforwarding_result_{filename}",
            mode='a',
            header=False,
            index=False
            )
    logger.info("Batch call forwarding update completed for file: %s", filename)
    return "Script Run is Finished"

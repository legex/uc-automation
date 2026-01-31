"""Route Pattern Batch Creation Service.

This module provides functions for batch creating route patterns in CUCM
from CSV files. It handles line partition updates and route pattern creation.

Functions:
    batch_routepattern_auto: Create route patterns from CSV file.
"""
import pandas as pd
from src.cucmapi.axlop import AXLOperations
from src.cucmapi.axlroutepattern import AXLRoutePatternOperations
from src.utils.logger import setup_logger

logger = setup_logger('rp_batch', 'temp/a/logs/rp_batch.log')
axloperations = AXLOperations()
axlrp = AXLRoutePatternOperations()

def batch_routepattern_auto(file, filename):
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
            f"src/resultfiles/rpupdateresult_{filename}",
            mode='a',
            header=False,
            index=False
            )
    logger.info("Batch route pattern creation completed for file: %s", filename)
    return "Script Run is Finished"

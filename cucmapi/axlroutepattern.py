import sys
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from cucmapi.axlconn import ConnectionAXL
from utils.dict_helper import clean_axl_dict, sanitizedict
from utils.logger import setup_logger

logger = setup_logger('RoutepatternApp', 'log/Routepattern.log')

UNWANTEDELEMENTS = [
    'associatedDevices',
    'usage',
    'confidentialAccess',
    'enterpriseAltNum',
    'useEnterpriseAltNum',
    'e164AltNum',
    'useE164AltNum',
]

class AXLRoutePatternOperations:
    """
    A class to manage AXL operations related to directory number (DN) changes
    for a user's CSF (Client Services Framework) phone in Cisco Unified Communications Manager (CUCM).
    """

    def __init__(self):
        """
        Initialize the AXL client and set user context.

        Args:
            username (str): CUCM user ID.
            pattern (str): New directory number (DN) pattern to apply.
        """
        axlclient = ConnectionAXL()
        self.service = axlclient.service()

    def get_line(self,
                 pattern: str,
                 route_partition: str):
        """
        Fetch the line configuration for a given pattern and partition.

        Args:
            pattern (str): DN pattern.
            route_partition (str): Route partition name.

        Returns:
            dict or None: Line details if found, else None.
        """
        try:
            return self.service.getLine(pattern=pattern,
                                        routePartitionName=route_partition
                                        )['return']
        except Fault:
            logger.warning("Line %s not found in partition %s", pattern, route_partition)
            return None

    def update_line(self,
                    old_pattern: str,
                    route_partition: str):
        """
        Update an existing line to use the new pattern and update display name.

        Args:
            old_pattern (str): Current DN pattern.
            route_partition (str): Route partition name.

        Returns:
            dict or None: Update response if successful, otherwise None.
        """
        line_data = self.get_line(old_pattern, route_partition)
        if not line_data:
            logger.warning("No line data found for pattern: %s", old_pattern)
            sys.exit(1)

        line_serialized = serialize_object(line_data)
        line_dict = clean_axl_dict(line_serialized)['line']
        line_dict['routePartitionName'] = "pt-hidden-internal"
        print(line_dict)
        slinedict = sanitizedict(line_dict, UNWANTEDELEMENTS)
        return slinedict
        # try:
        #     logger.info("Updating line from %s to %s", old_pattern, new_pattern)
        #     return self.service.updateLine(**slinedict)['return']
        # except Fault as e:
        #     logger.error("Failed to update line: %s", e)
        #     return f"error: {e}"


    def get_routepattern(self, pattern):
        """
        Fetch the route pattern configuration for a given pattern.

        Args:
            pattern (str): Route pattern.

        Returns:
            dict or None: Route pattern details if found, else None.
        """
        try:
            return self.service.getRoutePattern(pattern=pattern,
                                                routePartitionName="pt-global-internal")['return']
        except Fault:
            logger.warning("Route pattern %s not found", pattern)
            return None

    def create_routepattern(self, pattern, username):
        """
        Create a new route pattern in CUCM.

        Args:
            pattern (str): The route pattern to create.
            username (str): The username associated with the creation.

        Returns:
            dict or None: Response from CUCM if successful, else None.
        """
        routerpattern = {
        'pattern': f'\\{pattern}',
        'description':f'WxC DID - {username}',
        'usage':'Route',
        'routePartitionName' : 'PT-Global-Internal',
        'patternPrecedence' : 'Default',
        'routeClass':'Default',
        'blockEnable': 'false',
        'useCallingPartyPhoneMask': 'Off',
        'networkLocation': 'OnNet',
        'patternUrgency': 'true',
        'prefixDigitsOut': None,
            'destination': {
                    'routeListName': "RL-WBX-CALLING"
                }


}
        try:
            return self.service.addRoutePattern(routerpattern)['return']
        except Fault as e:
            logger.error("Failed to create route pattern: %s", e)
            return None

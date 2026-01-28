"""CUCM AXL Route Pattern Operations Module.

This module provides operations for managing route patterns and directory numbers
in Cisco Unified Communications Manager (CUCM) via the AXL SOAP API.

Classes:
    AXLRoutePatternOperations: Manages CUCM route patterns, lines, and device configurations.
"""
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from src.cucmapi.axlconn import ConnectionAXL
from src.utils.dict_helper import clean_axl_dict, sanitizedict
from src.utils.logger import setup_logger

logger = setup_logger('RoutepatternApp', 'log/Routepattern.log')

UNWANTEDELEMENTS = [
    'associatedDevices',
    'usage',
    'directoryURIs',
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

    def get_device(self,
                username: str):
        """
        Get the CSF device (softphone) line configuration for the user.

        Returns:
            object or None: Lines object if found, otherwise None.
        """
        print(f'username as observed in get_device {username}')
        try:
            user_details = self.service.getPhone(name=username)['return'].phone
            return user_details
        except Fault as e:
            logger.error("Zeep error: Failed to get CSF device for %s: %s", username, e)
            return None
        
    def get_line(self,
                 pattern: str):
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
                                        routePartitionName="PT-Global-Internal"
                                        )['return']
        except Fault:
            logger.warning("Line %s not found", pattern)
            return None

    def update_line(self,
                    old_pattern: str):
        """
        Update an existing line to use the new pattern and update display name.

        Args:
            old_pattern (str): Current DN pattern.
            route_partition (str): Route partition name.

        Returns:
            dict or None: Update response if successful, otherwise None.
        """
        line_data = self.get_line(old_pattern)
        if not line_data:
            logger.warning("No line data found for pattern: %s", old_pattern)
        
        line_serialized = serialize_object(line_data)
        line_dict = clean_axl_dict(line_serialized)['line']
        line_dict['newRoutePartitionName'] = "PT-Hidden"
        slinedict = sanitizedict(line_dict, UNWANTEDELEMENTS)
        try:
            logger.info("Updating line %s ", old_pattern)
            return self.service.updateLine(**slinedict)['return']
        except Fault as e:
            logger.error("Failed to update line: %s", e)
            return f"error: {e}"

    def update_phone(self,username: str, pattern: str):
        """
        Update the phone configuration for the user.

        Args:
            username (str): CUCM user ID.
        """
        userdetails = self.get_device(f"csf{username}")
        if not userdetails:
            logger.warning("No user details found for username: %s", username)

        ser_obj = serialize_object(userdetails.lines.line)
        clean_obj = clean_axl_dict(ser_obj)
        updated_lines = []
        for line in clean_obj:
            if not (pattern in line['dirn']['pattern'] and line['dirn']['routePartitionName'] == 'PT-Hidden'):
                updated_lines.append(line)
        try:
            logger.info("Updating phone %s ", username)
            response = self.service.updatePhone(name=f"csf{username}",lines={'line': updated_lines})
            logger.info("Phone %s updated successfully", username)
            return response
        except Fault as e:
            logger.error("Failed to update phone: %s", e)
            return f"error: {e}"

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
        'pattern': f'{pattern}',
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
            logger.info("Creating route pattern %s ", pattern)
            response = self.service.addRoutePattern(routerpattern)['return']
            logger.info("Route pattern %s created successfully", pattern)
            return response
        except Fault as e:
            logger.error("Failed to create route pattern: %s", e)
            return None

    def update_routepattern(self, pattern, partition):
        """
        Update an existing route pattern in CUCM.

        Args:
            pattern (str): The route pattern to update.
            partition (str): The new partition name for the route pattern.
        Returns:
            dict or None: Response from CUCM if successful, else None.

        """
        routerpattern = {
        'pattern': f'{pattern}',
        'routePartitionName' : 'PT-Hidden',
        'newRoutePartitionName' : partition
        }
        try:
            logger.info("Updating route pattern %s ", pattern)
            response = self.service.updateRoutePattern(**routerpattern)['return']
            logger.info("Route pattern %s updated successfully", pattern)
            return response
        except Fault as e:
            logger.error("Failed to update route pattern: %s", e)
            return None

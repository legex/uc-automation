"""CUCM AXL Route Pattern Operations Module.

This module provides operations for managing route patterns and directory numbers
in Cisco Unified Communications Manager (CUCM) via the AXL SOAP API.

Classes:
    AXLRoutePatternOperations: Manages CUCM route patterns, lines, and device configurations.
"""
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from cucmapi.axlconn import ConnectionAXL
from utils.dict_helper import clean_axl_dict, sanitizedict
from utils.logger import setup_logger

logger = setup_logger('RoutepatternApp', '/a/logs/Routepattern.log')

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

    def get_device(self,
                username: str, service=None):
        """
        Get the CSF device (softphone) line configuration for the user.

        Returns:
            object or None: Lines object if found, otherwise None.
        """
        if not service:
            logger.debug("No service provided")
        print(f'username as observed in get_device {username}')
        try:
            user_details = service.getPhone(name=username)['return'].phone
            return user_details
        except Fault as e:
            logger.error("Zeep error: Failed to get CSF device for %s: %s", username, e)
            return None
        
    def get_line(self,
                 pattern: str, service=None):
        """
        Fetch the line configuration for a given pattern and partition.

        Args:
            pattern (str): DN pattern.
            route_partition (str): Route partition name.

        Returns:
            dict or None: Line details if found, else None.
        """
        if not service:
            logger.debug("No service provided")
        try:
            return service.getLine(pattern=pattern,
                                        routePartitionName="PT-Global-Internal"
                                        )['return']
        except Fault:
            logger.warning("Line %s not found", pattern)
            return None

    def update_line(self,
                    old_pattern: str, service=None):
        """
        Update an existing line to use the new pattern and update display name.

        Args:
            old_pattern (str): Current DN pattern.
            route_partition (str): Route partition name.

        Returns:
            dict or None: Update response if successful, otherwise None.
        """
        if not service:
            logger.debug("No service provided")
        line_data = self.get_line(old_pattern, service=service)
        if not line_data:
            logger.warning("No line data found for pattern: %s", old_pattern)
        
        line_serialized = serialize_object(line_data)
        line_dict = clean_axl_dict(line_serialized)['line']
        line_dict['newRoutePartitionName'] = "PT-Hidden"
        slinedict = sanitizedict(line_dict, UNWANTEDELEMENTS)
        try:
            logger.info("Updating line %s ", old_pattern)
            return service.updateLine(**slinedict)['return']
        except Fault as e:
            logger.error("Failed to update line: %s", e)
            return f"error: {e}"

    def update_phone(self,username: str, pattern: str, service=None):
        """
        Update the phone configuration for the user.

        Args:
            username (str): CUCM user ID.
        """
        if not service:
            logger.debug("No service provided")
        logger.info("Starting updatePhone for user: %s with new DN: %s", username, pattern)
        userdetails = self.get_device(f"csf{username}", service=service)
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
            response = service.updatePhone(name=f"csf{username}",lines={'line': updated_lines})
            logger.info("Phone %s updated successfully", username)
            return response
        except Fault as e:
            logger.error("Failed to update phone: %s", e)
            return f"error: {e}"

    def get_routepattern(self, pattern, service=None):
        """
        Fetch the route pattern configuration for a given pattern.

        Args:
            pattern (str): Route pattern.

        Returns:
            dict or None: Route pattern details if found, else None.
        """
        if not service:
            logger.debug("No service provided")
        try:
            return service.getRoutePattern(pattern=pattern,
                                                routePartitionName="pt-global-internal")['return']
        except Fault:
            logger.warning("Route pattern %s not found", pattern)
            return None

    def create_routepattern(self, pattern, username, service=None):
        """
        Create a new route pattern in CUCM.

        Args:
            pattern (str): The route pattern to create.
            username (str): The username associated with the creation.

        Returns:
            dict or None: Response from CUCM if successful, else None.
        """
        if not service:
            logger.debug("No service provided")
        routerpattern = {
        'pattern': f'{pattern}',
        'description':f'WxC - {username}',
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
            response = service.addRoutePattern(routerpattern)['return']
            logger.info("Route pattern %s created successfully", pattern)
            return response
        except Fault as e:
            logger.error("Failed to create route pattern: %s", e)
            return None

    def update_routepattern(self, pattern, partition, service=None):
        """
        Update an existing route pattern in CUCM.

        Args:
            pattern (str): The route pattern to update.
            partition (str): The new partition name for the route pattern.
        Returns:
            dict or None: Response from CUCM if successful, else None.

        """
        if not service:
            logger.debug("No service provided")
        print(f'Pattern observed in update_routepattern: {pattern} and partition observed: {partition}')
        routerpattern = {
        'pattern': f'{pattern}',
        'routePartitionName' : 'PT-Global-Internal',
        'newRoutePartitionName' : partition
        }
        try:
            logger.info("Updating route pattern %s ", pattern)
            response = service.updateRoutePattern(**routerpattern)['return']
            print(response)
            logger.info("Route pattern %s updated successfully", pattern)
            return response
        except Fault as e:
            logger.error("Failed to update route pattern: %s", e)
            print(f'Error in update_routepattern: {e}')
            return None

    def update_callforwarding(self, pattern, destination_pattern, service=None):

        """
        Update call forwarding settings for a given route pattern.

        Args:
            pattern (str): The route pattern to update.
            destination_pattern (str): The new destination pattern for call forwarding.
        Returns:
            dict or None: Response from CUCM if successful, else None.
        """
        if not service:
            logger.debug("No service provided")
        routerpattern = {
        'pattern': f'\+{pattern}',
        'routePartitionName' : "PT-Global-Internal",
        'callForwardAll': {
            'destination': f"+{destination_pattern}"
        }
        }
        try:
            logger.info("Updating call forwarding for route pattern %s ", pattern)
            response = service.updateLine(**routerpattern)['return']
            logger.info("Call forwarding for route pattern %s updated successfully", pattern)
            return response
        except Fault as e:
            logger.error("Failed to update call forwarding for route pattern: %s", e)
            return None

    def update_callforwarding_apac_japan(self, pattern, destination_pattern, service=None):

        """
        Update call forwarding settings for a given route pattern.

        Args:
            pattern (str): The route pattern to update.
            destination_pattern (str): The new destination pattern for call forwarding.
        Returns:
            dict or None: Response from CUCM if successful, else None.
        """
        if not service:
            logger.debug("No service provided")
        routerpattern = {
        'pattern': f'\+{pattern}',
        'routePartitionName' : "PT-Global-Internal",
        'callForwardAll': {
            'destination': f"+{destination_pattern}",
            'callingSearchSpaceName': 'CSS-GLOBAL-DEVICE'
        }
        }
        try:
            logger.info("Updating call forwarding for route pattern %s ", pattern)
            response = service.updateLine(**routerpattern)['return']
            logger.info("Call forwarding for route pattern %s updated successfully", pattern)
            return response
        except Fault as e:
            logger.error("Failed to update call forwarding for route pattern: %s", e)
            return None

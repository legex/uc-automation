import sys
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from axlconn import ConnectionAXL
from dict_helper import clean_axl_dict, sanitizedict
from logger import setup_logger

logger = setup_logger('DNchange', 'log/DNchange.log')

UNWANTEDELEMENTS = [
    'associatedDevices',
    'usage',
    'confidentialAccess',
    'enterpriseAltNum',
    'useEnterpriseAltNum',
    'e164AltNum',
    'useE164AltNum',
]

class AXLOperations:
    """
    A class to manage AXL operations related to directory number (DN) changes
    for a user's CSF (Client Services Framework) phone in Cisco Unified Communications Manager (CUCM).
    """

    def __init__(self, username, pattern):
        """
        Initialize the AXL client and set user context.

        Args:
            username (str): CUCM user ID.
            pattern (str): New directory number (DN) pattern to apply.
        """
        self.username = username
        self.pattern = pattern
        axlclient = ConnectionAXL()
        self.service = axlclient.service()

    def get_user_display_name(self):
        """
        Retrieve the user's full display name (first + middle + last).

        Returns:
            str or None: Full display name if user exists, else None.
        """
        try:
            user = self.service.getUser(userid=self.username)['return'].user
            return f"{user.firstName} {user.middleName + ' ' if user.middleName else ''}{user.lastName}"
        except Fault as e:
            logger.error("Zeep error: Could not fetch user %s: %s", self.username, e)
            return None

    def get_csf_device(self):
        """
        Get the CSF device (softphone) line configuration for the user.

        Returns:
            object or None: Lines object if found, otherwise None.
        """
        try:
            user_details = self.service.getPhone(name=f'csf{self.username}')['return'].phone
            return user_details.lines
        except Fault as e:
            logger.error("Zeep error: Failed to get CSF device for %s: %s", self.username, e)
            return None

    def get_line(self, pattern, route_partition):
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

    def update_line(self, old_pattern, route_partition):
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

        display_name = self.get_user_display_name()
        if display_name:
            line_dict['alertingName'] = display_name
            line_dict['asciiAlertingName'] = display_name

        line_dict['pattern'] = self.pattern
        slinedict = sanitizedict(line_dict, UNWANTEDELEMENTS)

        try:
            logger.info("Updating line from %s to %s", old_pattern, self.pattern)
            return self.service.updateLine(**slinedict)['return']
        except Fault as e:
            logger.error("Failed to update line: %s", e)
            return f"error: {e}"

    def add_line(self, routepartition):
        """
        Add a new line with the specified pattern and route partition.

        Args:
            routepartition (str): Route partition name.

        Returns:
            dict or None: Add line response if successful, else None.
        """
        basic_lineconfig = {
            'pattern': self.pattern,
            'routePartitionName': routepartition,
            'description': 'Test Line',
            'usage': 'Device',
        }
        try:
            return self.service.addLine(line=basic_lineconfig)
        except Fault as e:
            logger.error("Failed to add line '%s': %s", self.pattern, e)
            return None

    def update_phone(self):
        """
        Update the user's CSF phone to replace its current DN with a new one.
        Skips any line that starts with '555'.

        Returns:
            dict or None: CUCM updatePhone response if successful, else None.
        """
        logger.info("Starting updatePhone for user: %s with new DN: %s",
                    self.username,
                    self.pattern
                    )

        lines = self.get_csf_device()
        if not lines:
            logger.error("No CSF device found for user: %s", self.username)
            return None

        ser_lines = serialize_object(lines)
        clean_lines = clean_axl_dict(ser_lines)

        updated = False
        for line in clean_lines.get('line', []):
            old_pattern = line['dirn']['pattern']
            if old_pattern.startswith('555'):
                logger.info("Skipping line with pattern starting '555': %s", old_pattern)
                continue

            routepartition = line['dirn']['routePartitionName']

            if not self.get_line(self.pattern, routepartition):
                logger.info(
                    "Line with pattern '%s' not found in partition '%s'. Creating new line.",
                    self.pattern,
                    routepartition
                    )
                self.add_line(routepartition)
            else:
                logger.info("Line with pattern '%s' already exists in partition '%s'",
                            self.pattern,
                            routepartition
                            )

            self.update_line(old_pattern, routepartition)
            line['dirn']['pattern'] = self.pattern
            updated = True

        if not updated:
            logger.warning("No eligible lines updated for user: %s", self.username)
            return None

        try:
            logger.info("Updating CSF device for user: %s", self.username)
            return self.service.updatePhone(name=f'csf{self.username}', lines=clean_lines)
        except Fault as e:
            logger.error("Zeep error while updating phone for user %s: %s", self.username, e)
            return None

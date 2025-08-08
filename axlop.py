import sys
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from axlconn import ConnectionAXL
from dict_helper import (clean_axl_dict,
                         sanitizedict,
                         filter_and_reindex_lines
                         )
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

    def __init__(self):
        """
        Initialize the AXL client and set user context.

        Args:
            username (str): CUCM user ID.
            pattern (str): New directory number (DN) pattern to apply.
        """
        axlclient = ConnectionAXL()
        self.service = axlclient.service()

    def get_user_display_name(self,
                              username: str):
        """
        Retrieve the user's full display name (first + middle + last).

        Returns:
            str or None: Full display name if user exists, else None.
        """
        try:
            user = self.service.getUser(userid=username[3:])['return'].user
            return f"{user.firstName} {user.middleName + ' ' if user.middleName else ''}{user.lastName}"
        except Fault as e:
            logger.error("Zeep error: Could not fetch user %s: %s", username, e)
            return None

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
                    username: str,
                    new_pattern: str,
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
        print(f'username as observed in update_line {username}')
        line_data = self.get_line(old_pattern, route_partition)
        if not line_data:
            logger.warning("No line data found for pattern: %s", old_pattern)
            sys.exit(1)

        line_serialized = serialize_object(line_data)
        line_dict = clean_axl_dict(line_serialized)['line']

        display_name = self.get_user_display_name(username)
        if display_name:
            line_dict['alertingName'] = display_name
            line_dict['asciiAlertingName'] = display_name

        line_dict['pattern'] = new_pattern
        slinedict = sanitizedict(line_dict, UNWANTEDELEMENTS)

        try:
            logger.info("Updating line from %s to %s", old_pattern, new_pattern)
            return self.service.updateLine(**slinedict)['return']
        except Fault as e:
            logger.error("Failed to update line: %s", e)
            return f"error: {e}"

    def add_line(self,
                 new_pattern: str,
                 routepartition: str):
        """
        Add a new line with the specified pattern and route partition.

        Args:
            routepartition (str): Route partition name.

        Returns:
            dict or None: Add line response if successful, else None.
        """
        basic_lineconfig = {
            'pattern': new_pattern,
            'routePartitionName': routepartition,
            'description': 'Test Line',
            'usage': 'Device',
        }
        try:
            return self.service.addLine(line=basic_lineconfig)
        except Fault as e:
            logger.error("Failed to add line '%s': %s", new_pattern, e)
            return None

    def update_csf_phone_lines(self,
                               username: str,
                               new_pattern: str):
        """Method to update phone lines and return clean lines with updated details"""
        print(f'username as observed in update_csf_phone_lines {username}')
        lines = self.get_device(username)
        if not lines:
            logger.error("No CSF device found for user: %s", username)
            return None

        ser_lines = serialize_object(lines.lines)
        clean_lines = clean_axl_dict(ser_lines)

        updated = False
        updated_partitions = set()
        for line in clean_lines.get('line', []):
            old_pattern = line['dirn']['pattern']
            if old_pattern.startswith('555'):
                logger.info("Skipping line with pattern starting '555': %s", old_pattern)
                continue

            routepartition = line['dirn']['routePartitionName']

            if routepartition not in updated_partitions:
                if not self.get_line(new_pattern, routepartition):
                    logger.info(
                        "Line with pattern '%s' not found in partition '%s'. Creating new line.",
                        new_pattern,
                        routepartition
                    )
                    self.add_line(new_pattern, routepartition)
                else:
                    logger.info("Line with pattern '%s' already exists in partition '%s'",
                                new_pattern,
                                routepartition)
                updated_partitions.add(routepartition)

            if not updated and old_pattern != new_pattern:
                self.update_line(username, new_pattern, old_pattern, routepartition)
                line['dirn']['pattern'] = new_pattern
                updated = True
            else:
                logger.info(
                    "Skipping update for line %s; already updated or duplicate",
                    old_pattern
                )

        if not updated:
            logger.warning("No eligible lines updated for user: %s", username)
            return None

        return clean_lines


    def update_all_devices(self, username: str, clean_lines: str, new_pattern: str):
        """ Method to update all relevant devices"""
        print(f'username as observed in update_all_devices {username}')
        device_types = ['csf', 'TCT-', 'BOT-']

        all_results = {}
        for prefix in device_types:
            device_name = f"{prefix}{username}"
            phone = self.get_device(device_name)
            #print("here is phone: ", phone)
            #print(f'username as observed with {prefix} {device_name}')
            if phone:
                if prefix in ['TCT-', 'BOT-']:
                    lines_to_use = filter_and_reindex_lines(clean_lines, new_pattern)
                    if lines_to_use is None:
                        all_results[device_name] = "Skipped: no matching line"
                        continue
                else:
                    lines_to_use = clean_lines
                try:
                    logger.info("Updating %s device for user: %s", device_name, username)
                    result = self.service.updatePhone(name=device_name, lines=lines_to_use)
                    all_results[device_name] = result
                except Fault as e:
                    logger.error("Zeep error while updating phone for user %s: %s", username, e)
                    all_results[device_name] = f"error: {e}"
            else:
                logger.info("Device %s does not exist for user %s, skipping.",
                            device_name,
                            username
                            )
                all_results[device_name] = None
        return all_results


    def update_phone(self,
                     username: str,
                     new_pattern: str):
        """Function call for updating lines"""
        logger.info("Starting updatePhone for user: %s with new DN: %s",
                    username,
                    new_pattern)
        #print(f'username as observed in update_phone {username}')

        clean_lines = self.update_csf_phone_lines(f"csf{username}", new_pattern)
        print(clean_lines)
        if not clean_lines:
            return None
        return self.update_all_devices(username, clean_lines, new_pattern)

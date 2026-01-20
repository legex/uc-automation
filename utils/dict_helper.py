"""Dictionary Helper Utilities.

This module provides utility functions for cleaning and transforming
dictionary objects, particularly for processing AXL API responses from CUCM.

Functions:
    clean_axl_dict: Remove None values and unwrap AXL response structures.
    sanitizedict: Remove specified unwanted keys from a dictionary.
    filter_and_reindex_lines: Filter and reindex line configurations.
"""
import copy
from collections import OrderedDict
from utils.logger import setup_logger

logger = setup_logger('utilslog', 'log/utilslog.log')

def clean_axl_dict(obj):
    """
    Recursively clean AXL API response dictionaries.
    
    Removes None values, 'uuid' keys, and unwraps '_value_1' structures
    commonly found in AXL SOAP responses.
    
    Args:
        obj: Dictionary, OrderedDict, list, or primitive value to clean.
    
    Returns:
        Cleaned dictionary, list, or primitive value with None values removed
        and nested structures unwrapped.
    """
    if isinstance(obj, (OrderedDict, dict)):
        result = {}
        for k, v in obj.items():
            if v is None or k == 'uuid':
                continue  # Strip None values and 'uuid' keys
            elif isinstance(v, (dict, OrderedDict)):
                # Unwrap _value_1 if present
                if '_value_1' in v:
                    result[k] = v['_value_1']
                else:
                    result[k] = clean_axl_dict(v)
            elif isinstance(v, list):
                result[k] = [clean_axl_dict(item) for item in v]
            else:
                result[k] = v
        return result
    elif isinstance(obj, list):
        return [clean_axl_dict(item) for item in obj]
    else:
        return obj

def sanitizedict(linedict, unwantedkeys):
    """
    Remove unwanted keys from a dictionary.
    
    Args:
        linedict (dict): Dictionary to sanitize.
        unwantedkeys (list): List of keys to remove.
    
    Returns:
        dict: Sanitized dictionary with unwanted keys removed.
    """
    for key in unwantedkeys:
        if key in linedict:
            linedict.pop(key)
    return linedict

def filter_and_reindex_lines(clean_lines, new_pattern):
    """
    Filter and reindex line configurations based on pattern matching.
    
    Filters out lines starting with '555' and lines not matching the new_pattern,
    then reindexes remaining lines and updates call settings.
    
    Args:
        clean_lines (dict): Dictionary containing 'line' array with line configurations.
        new_pattern (str): Pattern to match for filtering lines.
    
    Returns:
        list: Filtered and reindexed list of line configurations.
    """
    filtered_lines = copy.deepcopy(clean_lines)
    remaining_lines = []
    next_index = 1
    for line in filtered_lines.get('line', []):
        pattern = line['dirn']['pattern']
        if pattern.startswith('555'):
            continue
        if pattern != new_pattern:
            continue
        line['index'] = next_index
        line['maxNumCalls'] = 2
        line['busyTrigger'] = 1
        remaining_lines.append(line)
        next_index += 1

    if not remaining_lines:
        logger.warning("No lines matching new pattern %s after filtering: skipping update", new_pattern)
        return None

    filtered_lines['line'] = remaining_lines
    return filtered_lines

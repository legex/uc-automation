import copy
from collections import OrderedDict
from utils.logger import setup_logger

logger = setup_logger('utilslog', 'log/utilslog.log')

def clean_axl_dict(obj):
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
    for key in unwantedkeys:
        linedict.pop(key)
    return linedict

def filter_and_reindex_lines(clean_lines, new_pattern):
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

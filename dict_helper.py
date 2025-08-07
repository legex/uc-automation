from collections import OrderedDict

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
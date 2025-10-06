import json

license_store = {
    "ucmlic": "Y2lzY29zcGFyazovL3VzL0xJQ0VOU0UvYTM3NDkzMTUtYWUwOS00YTUyLTgwNmMtMmMzMjIyZmE3YzJjOlVDUFJFTV9jMzMyOWQzMi0xNmVkLTQxNDUtOTUyNS02M2FjYjRiMzFiMjA",
    "webexlic": "Y2lzY29zcGFyazovL3VzL0xJQ0VOU0UvYTM3NDkzMTUtYWUwOS00YTUyLTgwNmMtMmMzMjIyZmE3YzJjOkJDU1REXzFhNGRhOTZiLTNmYWUtNGVlYi1hZDYwLWFkNTA3MTE4NzFkMA"
}
WEBEX_URL = "https://webexapis.com/v1/people"
PATCH_LIC_URL = "https://webexapis.com/v1/licenses/users"
with open("metadata/location.json", 'r') as f:
    LOCATIONS = json.load(f)

with open("metadata/acd_locations.json", 'r') as f:
    ACDLOCATIONS = json.load(f)
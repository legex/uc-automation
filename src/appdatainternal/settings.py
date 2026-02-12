import os
import json
import pandas as pd


with open("appdatainternal/cucm.json", 'r') as f:
    CUCM_ADDRESSES = json.load(f)

mode = "Prod"
if mode == "Prod":
    with open("appdatainternal/acd_locations.json", 'r') as f:
        ACDLOCATIONS = json.load(f)
else:
    with open("appdatainternal/dev_location.json", 'r') as f:
        ACDLOCATIONS = json.load(f)

if mode == "Prod":
    license_store = {
        "ucmlic": "Y2lzY29zcGFyazovL3VzL0xJQ0VOU0UvYTM3NDkzMTUtYWUwOS00YTUyLTgwNmMtMmMzMjIyZmE3YzJjOlVDUFJFTV9jMzMyOWQzMi0xNmVkLTQxNDUtOTUyNS02M2FjYjRiMzFiMjA",
        "webexlic": "Y2lzY29zcGFyazovL3VzL0xJQ0VOU0UvYTM3NDkzMTUtYWUwOS00YTUyLTgwNmMtMmMzMjIyZmE3YzJjOkJDU1REXzFhNGRhOTZiLTNmYWUtNGVlYi1hZDYwLWFkNTA3MTE4NzFkMA"
    }
else:
    license_store = {
        "ucmlic": "Y2lzY29zcGFyazovL3VzL0xJQ0VOU0UvYmMyZDgzNzItMzIzZS00ZGVmLTg1MWItZGMxM2M2ODQ0ZjExOlVDUFJFTV9jMzMyOWQzMi0xNmVkLTQxNDUtOTUyNS02M2FjYjRiMzFiMjA",
        "webexlic": "Y2lzY29zcGFyazovL3VzL0xJQ0VOU0UvYmMyZDgzNzItMzIzZS00ZGVmLTg1MWItZGMxM2M2ODQ0ZjExOkJDU1REXzBhNmM3NGI1LWZiYjktNDU3NS04MTdjLTFjZjc1ZTBlNjhlOQ"
    }
WEBEX_URL = "https://webexapis.com/v1/people"
PATCH_LIC_URL = "https://webexapis.com/v1/licenses/users"
with open("appdatainternal/location.json", 'r') as f:
    LOCATIONS = json.load(f)

exclude_df = pd.read_csv("appdatainternal/excludelist.csv")
exclude_list = exclude_df['UserId'].tolist()

extension_prefix = {
    "France": "784110",
    "United Kingdom": "784210",
    "Japan": "785310",
    "Poland": "784810",
    "Singapore": "785510",
    "United States": "785810",
    "India": "783910",
    "Canada": "785610",
    "Malaysia": "784610",
    "Germany": "785210",
    "Costa Rica": "785910",
    "Brazil": "784510",
    "South Korea": "785710",
    "Israel": "784410",
    "Czech Republic": "783210",
    "Italy": "783710",
    "Spain": "783510",
    "Sweden": "783310",
    "Australia": "784710",
    "Netherlands": "784310",
    "Denmark": "785410",
    "Ireland": "784910",
    "Switzerland": "783610"
}

resultfile_path = "/tmp/resultfiles/"
def ensure_resultfile_path(resultfile_path):
    """Ensure the result file path exists."""
    if not os.path.exists(resultfile_path):
        os.makedirs(resultfile_path)
    return resultfile_path
resultfile_location = ensure_resultfile_path(resultfile_path)



SERVER = "wauth.corp.akamai.com:636"
LDAP_USERNAME = "akamai.com\\svc_tmt_account"
ldapsecretfile = "/a/secrets/app/ldap_user/ldap_user.opaque"
with open(ldapsecretfile, 'r') as f:
    LDAP_PASSWORD = f.read().strip()

profileid_blr = "Y2lzY29zcGFyazovL3VzL0NBTExJTkdfUFJPRklMRS9iNTQyYWY1ZS0wMzkzLTQ0MjQtODI2OC1jYzdjYjI0ZGVkMDk"

allowed_users_list = ['abshukla', 'risaxen', 'raksingh', 'sshrutik', 'nvemula', 'emontero', 'ratiwar', 'rpangira', 'rasahu', 'akalpath']
rbac_roles = {
    "admin": ["abshukla", "risaxen", "raksingh",
              "sshrutik", "nvemula", "emontero",
              "ratiwar", "rpangira", "rasahu",
              "akalpath"],
    "viewer": ["dforeste"],
    "user": []
}
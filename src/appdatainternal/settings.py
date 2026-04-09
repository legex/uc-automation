import os
import json
from dotenv import load_dotenv
import pandas as pd

load_dotenv()


with open("appdatainternal/location.json", 'r') as f:
    LOCATIONS = json.load(f)

exclude_df = pd.read_csv("appdatainternal/excludelist.csv")
exclude_list = exclude_df['UserId'].tolist()

profileid_blr = "dummyidfromCH"

allowed_users_list = []
rbac_roles = {
    "admin": [],
    "viewer": [],
    "user": [],
    "jpuser": []
}

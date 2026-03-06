import os
import json
from dotenv import load_dotenv
import pandas as pd

load_dotenv()


with open("appdatainternal/location.json", 'r') as f:
    LOCATIONS = json.load(f)

exclude_df = pd.read_csv("appdatainternal/excludelist.csv")
exclude_list = exclude_df['UserId'].tolist()

profileid_blr = "Y2lzY29zcGFyazovL3VzL0NBTExJTkdfUFJPRklMRS9iNTQyYWY1ZS0wMzkzLTQ0MjQtODI2OC1jYzdjYjI0ZGVkMDk"

allowed_users_list = ['abshukla', 'risaxen', 'raksingh', 'sshrutik', 'nvemula', 'emontero', 'ratiwar', 'rpangira', 'rasahu', 'akalpath']
rbac_roles = {
    "admin": ["abshukla", "risaxen", "raksingh",
              "sshrutik", "nvemula", "emontero",
              "ratiwar", "rpangira", "rasahu",
              "akalpath"],
    "viewer": ["dforeste"],
    "user": [],
    "jpuser": ['ynarita', 'misato', 'yoritate', 'sjkin', 'sarakawa', 'thachimu', 
               'hhokari', 'yozaki', 'naraumi', 'aryonai', 'yiguchi', 'nokajima', 
               'ysatoi', 'esanpedr', 'tnoguchi', 'fhashita', 'hnagamat', 'esanpedr',
               'hsato', 'emuto', 'ykawabat']
}

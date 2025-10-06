import pandas as pd
import json

df = pd.read_csv("acd_region.csv")
def regions():
    region_dict = {}
    for _, row in df.iterrows():
        if isinstance(row["uid"], str):
            region_dict[row["region"]] = row["uid"]
    with open("metadata/acd_locations.json", "w") as f:
        json.dump(regions(), f, indent=4)
    return region_dict

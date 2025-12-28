import json

import pandas as pd
from shapely.geometry import Polygon

from utils import download_data, find_name_for_point

download_data()

df = pd.read_csv("data/hdb-property-info.csv")

with open("data/hdb_name_to_coords.json") as f:
    geoinfo = json.load(f)


name_to_geom = {name: Polygon(coords[0]) for name, coords in geoinfo.items()}

df["name"] = df.apply(
    lambda row: find_name_for_point(row["lon"], row["lat"], name_to_geom), axis=1
)

df.to_csv("data/hdb-property-info-with-name.csv", index=False)

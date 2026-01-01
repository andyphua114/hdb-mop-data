import argparse
import json

import pandas as pd
from shapely.geometry import Polygon

from utils import download_data, find_name_for_point


def main():
    parser = argparse.ArgumentParser(description="Download HDB MOP data")
    parser.add_argument("-a", "--year", type=int, help="HDB MOP year", default=2026)

    args = parser.parse_args()

    year = args.year

    download_data(year)

    df = pd.read_csv(f"data/hdb-property-info-mop-{year}.csv")

    with open("data/hdb_name_to_coords.json") as f:
        geoinfo = json.load(f)

    name_to_geom = {name: Polygon(coords[0]) for name, coords in geoinfo.items()}

    df["name"] = df.apply(
        lambda row: find_name_for_point(row["lon"], row["lat"], name_to_geom), axis=1
    )

    df.to_csv(f"data/hdb-property-info-with-name-{year}.csv", index=False)


if __name__ == "__main__":
    main()

import json
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from shapely.geometry import Point


def check_response(response):
    """Check the response based on status code.

    Args:
        response (requests.Response): The HTTP response returned by `requests.get()` or `requests.post()`.

    Returns:
        dict: Parsed JSON response from the API.

    Raises:
        requests.HTTPError: If the status code is not 200
    """

    if response.status_code == 200:
        return response.json()
    else:
        raise requests.HTTPError(
            f"Request failed with status code {response.status_code}: {response.text}"
        )


def get_token():
    """Retrieve your OneMap API token. The email and password must be defined in a .env file.

    Returns:
        string: OneMap API token
    """

    # Load environment variables from .env file
    load_dotenv(override=True)

    url = "https://www.onemap.gov.sg/api/auth/post/getToken"

    payload = {
        "email": os.environ["ONEMAP_EMAIL"],
        "password": os.environ["ONEMAP_EMAIL_PASSWORD"],
    }

    response = requests.request("POST", url, json=payload)
    token = check_response(response)["access_token"]

    return token


def get_latlon(location, token):
    """Retrieve your OneMap API token. The email and password must be defined in a .env file.

    Args:
        location (string): The search term to be used to query the OneMamp Search API.

    Returns:
        tuple: latitude and longitude of location
    """

    url = "https://www.onemap.gov.sg/api/common/elastic/search?searchVal={}&returnGeom=Y&getAddrDetails=Y&pageNum=1".format(
        location
    )
    headers = {"Authorization": "Bearer {}".format(token)}

    response = requests.get(url, headers=headers)
    search_result = check_response(response)

    if search_result["found"] == 0:
        return (None, None)
    else:
        # just take the first result as OneMap API results sorted based on estimated relevance
        return (
            search_result["results"][0]["LATITUDE"],
            search_result["results"][0]["LONGITUDE"],
        )


def find_name_for_point(lon: float, lat: float, name_to_geom: dict) -> str | None:
    """
    Returns NAME of polygon that contains the (lon, lat) point,
    or None if no polygon contains it.
    """
    pt = Point(lon, lat)
    for name, geom in name_to_geom.items():
        if geom.contains(pt):
            return name
    return None


def poll_download(dataset_id, year):
    response = requests.get(
        f"https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/poll-download",
        headers={"Content-Type": "application/json"},
        data=json.dumps(
            {
                "columnNames": [
                    "blk_no",
                    "street",
                    "max_floor_lvl",
                    "year_completed",
                    "bldg_contract_town",
                    "residential",
                    "2room_sold",
                    "3room_sold",
                    "4room_sold",
                    "5room_sold",
                ],
                # change the filter accordinly
                "filters": [
                    {"columnName": "year_completed", "type": "EQ", "value": year - 5},
                ],
            }
        ),
    )

    data = response.json()
    return data


def download_hdb_property_info(year=2026):
    # HDB Property Information
    dataset_id = "d_17f5382f26140b1fdae0ba2ef6239d2f"

    response = requests.get(
        f"https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/initiate-download",
        headers={"Content-Type": "application/json"},
        data=json.dumps(
            {
                "columnNames": [
                    "blk_no",
                    "street",
                    "max_floor_lvl",
                    "year_completed",
                    "bldg_contract_town",
                    "residential",
                    "2room_sold",
                    "3room_sold",
                    "4room_sold",
                    "5room_sold",
                ],
                "filters": [
                    {"columnName": "year_completed", "type": "EQ", "value": year - 5},
                ],
            }
        ),
    )

    data = response.json()
    print(data["data"]["message"])

    data = poll_download(dataset_id, year)

    # keep polling until data url is returned; wait for 2 secs between each poll
    while data["data"]["status"] != "DOWNLOAD_SUCCESS":
        print("Upstream still processing; continue polling...")
        time.sleep(2)
        data = poll_download(dataset_id, year)

    df = pd.read_csv(data["data"]["url"])

    # convert 2room, 3room, 4room, 5room_sold columns to type int
    # convert other columns as necessary
    df["2room_sold"] = df["2room_sold"].astype(int)
    df["3room_sold"] = df["3room_sold"].astype(int)
    df["4room_sold"] = df["4room_sold"].astype(int)
    df["5room_sold"] = df["5room_sold"].astype(int)

    # filter for residential = 'Y' and (2room_sold > or 3room_sold > 0 or 4room_sold > 0 or 5room_sold > 0)
    df = df[
        (df["residential"] == "Y")
        & (
            (df["2room_sold"] > 0)
            | (df["3room_sold"] > 0)
            | (df["4room_sold"] > 0)
            | (df["5room_sold"] > 0)
        )
    ]

    print(f"Total number of HDBs: {len(df)}")

    # retrieve the metadata of dataset and convert string of `bldg_contract_town` description text into a mapping DataFrame
    response = requests.get(
        f"https://api-production.data.gov.sg/v2/public/api/datasets/{dataset_id}/metadata",
        headers={"Accept": "*/*"},
    )

    metadata = check_response(response)
    metadata_mapping = metadata["data"]["columnMetadata"]["map"]
    town_value = "bldg_contract_town"
    town_key = next((k for k, v in metadata_mapping.items() if v == town_value), None)

    town_description = metadata["data"]["columnMetadata"]["metaMapping"][town_key][
        "description"
    ]

    town_pairs = []
    towns = town_description.split(" - ")
    for idx, t in enumerate(towns[:-1]):
        town_pairs.append((t.rsplit(" ", 1)[1], towns[idx + 1].rsplit(" ", 1)[0]))

    town_df = pd.DataFrame(town_pairs, columns=["bldg_contract_town", "area"])

    df = pd.merge(df, town_df, how="left", on="bldg_contract_town")

    # create address columns
    df["address"] = df["blk_no"] + " " + df["street"]

    token = get_token()

    df[["lat", "lon"]] = (
        df["address"].apply(lambda x: get_latlon(x, token=token)).apply(pd.Series)
    )

    df.to_csv(f"data/hdb-property-info-mop-{year}.csv", index=False)


def download_hdb_name_info():
    dataset_id = "d_930e662ac7e141fe3fd2a6efa5216902"
    url = (
        "https://api-open.data.gov.sg/v1/public/api/datasets/"
        + dataset_id
        + "/poll-download"
    )

    response = requests.get(url)
    json_data = response.json()
    if json_data["code"] != 0:
        print(json_data["errMsg"])
        exit(1)

    url = json_data["data"]["url"]
    response = requests.get(url).json()

    # Dict mapping NAME -> coordinates
    hdb_name_to_coords = {
        feature["properties"]["NAME"]: feature["geometry"]["coordinates"]
        for feature in response["features"]
    }

    with open("data/hdb_name_to_coords.json", "w", encoding="utf-8") as f:
        json.dump(hdb_name_to_coords, f, ensure_ascii=False, indent=4)


def download_data(year=2026):
    data_dir = Path("data")

    file1 = data_dir / f"hdb-property-info-mop-{year}.csv"
    file2 = data_dir / "hdb_name_to_coords.json"

    if file1.exists():
        print(f"{file1.name} exists, skipping download.")
    else:
        download_hdb_property_info(year)

    if file2.exists():
        print(f"{file2.name} exists, skipping download.")
    else:
        download_hdb_name_info()

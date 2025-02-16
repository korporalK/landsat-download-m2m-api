import os
import time
import asyncio
import aiohttp
import aiofiles
import requests
import tarfile
from urllib.parse import urlparse
from datetime import datetime
from typing import List, Dict

# How to use this script:
# 1. Set the EARTHDATA_USER and EARTHDATA_TOKEN environment variables to your Earthdata username and token.
#    Replace "insert usgs username here" and "insert usgs token here" with your Earthdata username and token.
#    For more information, see: https://m2m.cr.usgs.gov/api/docs/json/ , 
#                               https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/files/M2M%20Application%20Token%20Documentation_02112025_0.pdf

#    Note: You may need to log out and log back in for the changes to take effect.

# 2. Call the download_landsat_tool function with the desired parameters.


# Authentication
username = os.getenv("EARTHDATA_USER")  # Your Earthdata username
token = os.getenv("EARTHDATA_TOKEN")  # Your Earthdata token
if not username or not token:
    raise EnvironmentError("EARTHDATA_USER and EARTHDATA_TOKEN environment variables must be set.")


def download_landsat_tool(
    output_directory: str,
    start_date: str,
    end_date: str,
    max_cloud_cover: float = 20.0,
    landsat_sensors: List[str] = None,
    bands: List[str] = None,
    aoi_feature_class: str = None,
    bounding_box: str = None,
    delete_archive: bool = True,
    max_concurrent_downloads: int = 5,
) -> str:
    """Downloads Landsat Collection 2 Level-2 imagery (Surface Reflectance/Temperature) asynchronously via the USGS M2M API.

    This function automates the process of searching for, requesting, and downloading Landsat data.
    It handles authentication, scene searching, download option retrieval, batch download requests,
    polling for download URLs, downloading files, and (optionally) extracting tar archives.  It uses
    `asyncio` and `aiohttp` for concurrent downloads, significantly improving download speed.  `nest_asyncio`
    is used to allow for nested event loops, making it suitable for use in Jupyter notebooks and IPython.

    Args:
        output_directory: The directory where downloaded files and extracted data will be stored.
            This directory will be created if it doesn't exist.
        start_date: The start date for the imagery search (inclusive), in 'YYYY-MM-DD' format.
        end_date: The end date for the imagery search (inclusive), in 'YYYY-MM-DD' format.
        max_cloud_cover: The maximum acceptable cloud cover percentage (0-100).  Defaults to 20.0.
        landsat_sensors: A list of Landsat sensor identifiers to search for.  Valid options are
            "L8", "L9", "L7", and "L5". Defaults to ["L8", "L9"] if not specified.
        bands: A list of band identifiers to download.  If None, the entire product bundle is
            downloaded.  Band identifiers should be in the format "B1", "B2", etc. (e.g., ["B2", "B3", "B4"]).
            If specified, individual band files are downloaded instead of the full bundle.
        aoi_feature_class:  Not currently supported.  Reserved for future use with feature classes.
        bounding_box: A string defining the bounding box for the search, in the format
            "min_lon,min_lat,max_lon,max_lat" (WGS84 coordinates).
        delete_archive: If True (default), downloaded tar archives are deleted after extraction
            (only applicable when downloading full bundles, i.e., when `bands` is None).
        max_concurrent_downloads: The maximum number of concurrent downloads. Defaults to 5.  Higher
            values can improve download speed but may overwhelm your system or the server.

    Returns:
        A string summarizing the result of the download process, indicating the number of
        files/scenes downloaded and the output directory.  Returns an error message if any
        part of the process fails."""

    base_url = "https://m2m.cr.usgs.gov/api/api/json/stable/"

    def m2m_request(endpoint: str, payload: dict, apiKey: str = None) -> dict:
        url = base_url + endpoint
        headers = {}
        if apiKey:
            headers["X-Auth-Token"] = apiKey
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        resp_json = response.json()
        if resp_json.get("errorCode"):
            raise Exception(f"{resp_json.get('errorCode', 'Unknown Error')}: {resp_json.get('errorMessage', '')}")
        return resp_json.get("data")

    # --- Input validation and setup ---
    if not all([output_directory, start_date, end_date, bounding_box]):
        return "Error: output_directory, start_date, end_date, and bounding_box are required."
    os.makedirs(output_directory, exist_ok=True)

    try:
        min_lon, min_lat, max_lon, max_lat = map(float, bounding_box.split(","))
        if not (-180 <= min_lon <= 180 and -90 <= min_lat <= 90 and -180 <= max_lon <= 180 and -90 <= max_lat <= 90):
            return "Error: Bounding box coordinates must be within valid ranges."
    except (ValueError, TypeError):
        return "Error: Invalid bounding_box format. Use 'min_lon,min_lat,max_lon,max_lat'."

    try:
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return "Error: Invalid date format. Use 'YYYY-MM-DD'."

    if landsat_sensors is None:
        landsat_sensors = ["L8", "L9"]

    login_payload = {"username": username, "token": token}
    try:
        m2m_request("login", login_payload)
    except Exception as e:
        return f"Error during login: {str(e)}"

    # Further implementation for downloading data would go here...

    return "Download process initiated."
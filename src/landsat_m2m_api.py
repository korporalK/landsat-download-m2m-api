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
username = "insert usgs username here"  # Your Earthdata username
token = "insert usgs token here"  # Your Earthdata token
try:
    if username or token:
        print("EARTHDATA_USER and EARTHDATA_TOKEN environment variables are set.")
except KeyError as e:
    print("Error: EARTHDATA_USER and EARTHDATA_TOKEN environment variables must be set")



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
            raise ValueError()
    except (ValueError, TypeError):
        return "Error: Invalid bounding_box format. Use 'min_lon,min_lat,max_lon,max_lat'."

    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return "Error: Invalid date format. Use 'YYYY-MM-DD'."

    if landsat_sensors is None:
        landsat_sensors = ["L8", "L9"]


    login_payload = {"username": username, "token": token}
    try:
        apiKey = m2m_request("login-token", login_payload)
        print("Login successful.")
    except Exception as e:
        return f"Login failed: {str(e)}"

    # 3. Scene Search
    datasets_map = {
        "L8": "landsat_ot_c2_l2",
        "L9": "landsat_ot_c2_l2",
        "L7": "landsat_etm_c2_l2",
        "L5": "landsat_tm_c2_l2"
    }
    scene_list = []
    for sensor in landsat_sensors:
        sensor_key = sensor.upper()
        if sensor_key not in datasets_map:
            m2m_request("logout", {}, apiKey)
            return f"Error: Invalid sensor '{sensor}'."
        dataset = datasets_map[sensor_key]
        search_payload = {
            "datasetName": dataset,
            "sceneFilter": {
                "spatialFilter": {"filterType": "geojson", "geoJson": {
                    "type": "Polygon",
                    "coordinates": [[
                        [min_lon, min_lat], [max_lon, min_lat], [max_lon, max_lat], [min_lon, min_lat], [min_lon, min_lat]
                    ]]
                }},
                "acquisitionFilter": {"start": start_date, "end": end_date},
                "cloudCoverFilter": {"min": 0, "max": int(max_cloud_cover)}
            }
        }
        try:
            search_data = m2m_request("scene-search", search_payload, apiKey)
            results = search_data.get("results", [])
            print(f"Found {len(results)} scenes for sensor {sensor_key}.")
            scene_list.extend([(scene.get("entityId"), dataset, scene.get("displayId"))
                               for scene in results if scene.get("entityId") and scene.get("displayId")])
        except Exception as e:
            m2m_request("logout", {}, apiKey)
            return f"Search failed for sensor {sensor_key}: {str(e)}"

    if not scene_list:
        m2m_request("logout", {}, apiKey)
        return "No scenes found."

    entity_to_display = {entityId: displayId for entityId, _, displayId in scene_list}

    # 4. Download Options
    downloads = []
    dataset_groups: Dict[str, List[str]] = {}
    for entityId, ds, _ in scene_list:
        dataset_groups.setdefault(ds, []).append(entityId)


    if bands is None:
        # Full bundle workflow
        for ds, entityIds in dataset_groups.items():
            payload = {"datasetName": ds, "entityIds": entityIds}
            try:
                dload_data = m2m_request("download-options", payload, apiKey)
                if isinstance(dload_data, list):
                    options = dload_data
                elif isinstance(dload_data, dict):
                    options = dload_data.get("options", [])
                else:
                    options = []
                options_by_entity: Dict[str, dict] = {}
                for opt in options:
                    if opt.get("available"):
                        ent_id = opt.get("entityId")
                        if ent_id and ent_id not in options_by_entity:
                            options_by_entity[ent_id] = opt
                for ent in entityIds:
                    if ent in options_by_entity:
                        opt = options_by_entity[ent]
                        downloads.append({"entityId": ent, "productId": opt.get("id")})
                # Removed: No longer needed for verbose output: print(f"Retrieved bundle download options for dataset {ds}.")
            except Exception as e:
                print(f"Download-options request failed for dataset {ds}: {str(e)}")  # Keep: Important for error handling

    else:  # Specific bands
        for dataset_name, entity_ids in dataset_groups.items():
            payload = {"datasetName": dataset_name, "entityIds": entity_ids}
            try:
                options = m2m_request("download-options", payload, apiKey)
                if isinstance(options, dict):
                    options = options.get("options", [])
                options_by_entity = {opt["entityId"]: opt for opt in options if opt.get("available") and opt.get("entityId")}

                for entity_id in entity_ids:
                    if entity_id in options_by_entity:
                        option = options_by_entity[entity_id]
                        for secondary_option in option.get("secondaryDownloads", []):
                            if secondary_option.get("available"):
                                file_id = secondary_option.get("displayId", "")
                                if any(file_id.endswith(f"_{band_code.upper()}.TIF") for band_code in bands):
                                    downloads.append({"entityId": secondary_option["entityId"], "productId": secondary_option["id"]})
            except Exception as e:
                print(f"Download-options request failed for dataset {dataset_name}: {str(e)}")

    if not downloads:
        m2m_request("logout", {}, apiKey)
        return "No available downloads found."

    # 5. Download Request
    label = datetime.now().strftime("%Y%m%d_%H%M%S")
    req_payload = {"downloads": downloads, "label": label}
    try:
        req_results = m2m_request("download-request", req_payload, apiKey)
        print("Download request submitted.")
        available_downloads = req_results.get("availableDownloads", [])
        preparing_downloads = req_results.get("preparingDownloads", [])
    except Exception as e:
        m2m_request("logout", {}, apiKey)
        return f"Download request failed: {str(e)}"

    # 6. Poll for Download URLs (if needed) - CORRECTED LOGIC
    if preparing_downloads:  # Poll if *anything* is preparing
        retrieve_payload = {"label": label}
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                ret_data = m2m_request("download-retrieve", retrieve_payload, apiKey)
                if ret_data and ret_data.get("available"):
                    available_downloads.extend(ret_data["available"])  # Add new URLs
                    print(f"Attempt {attempt + 1}: Retrieved {len(ret_data['available'])} URLs.")
                    if len(available_downloads) >= len(downloads):
                        break  # Exit loop when we have all URLs
                else:
                    print("No download URLs retrieved yet.")
            except Exception as e:
                print(f"Download-retrieve attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_attempts - 1:
                print(f"Waiting 20 seconds... ({attempt + 1}/{max_attempts})")
                time.sleep(20)


    # 7. Download and Process (ASYNC)
    async def _download_and_process(downloads_to_process):
        async def _download_single_file(session, item, semaphore):
            async with semaphore:
                download_url = item.get("url")
                if not download_url:
                    return None

                try:
                    async with session.get(download_url, timeout=300) as response:
                        response.raise_for_status()

                        if bands is not None:
                            new_fname = item.get("fileName")
                            if not new_fname:
                                entity_id = item.get("entityId")
                                if entity_id:
                                    new_fname = entity_id + ".TIF"
                                else:
                                    print(f"Warning: entityId missing, skipping: {item}")
                                    return None
                        else:
                            entity = item.get("entityId")
                            display_id = entity_to_display.get(entity)
                            new_fname = (display_id + ".tar.gz") if display_id else os.path.basename(urlparse(download_url).path)

                        final_path = os.path.join(output_directory, new_fname)
                        async with aiofiles.open(final_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        print(f"Downloaded: {new_fname}")

                        if bands is None and new_fname.endswith(".tar.gz"):
                            try:
                                with tarfile.open(final_path, "r:*") as tar:
                                    extract_dir = os.path.join(output_directory, entity_to_display.get(item.get("entityId"), ""))
                                    os.makedirs(extract_dir, exist_ok=True)
                                    tar.extractall(path=extract_dir)
                                print(f"Extracted: {new_fname}")
                                if delete_archive:
                                    os.remove(final_path)
                                    print(f"Deleted archive: {final_path}")
                            except Exception as e:
                                print(f"Error extracting {final_path}: {str(e)}")
                        return final_path

                except Exception as e:
                    print(f"Download failed for {download_url}: {str(e)}")
                    return None

        semaphore = asyncio.Semaphore(max_concurrent_downloads)
        async with aiohttp.ClientSession() as session:
            tasks = [_download_single_file(session, item, semaphore) for item in downloads_to_process]
            return await asyncio.gather(*tasks)

    downloaded_files: List[str] = []
    try:
        # ALWAYS process available_downloads
        downloaded_files = asyncio.run(_download_and_process(available_downloads))
        downloaded_files = [path for path in downloaded_files if path is not None]  # Filter out failures

    except RuntimeError as e:
        print(f"RuntimeError: {e}")

    # 8. Logout
    try:
        m2m_request("logout", {}, apiKey)
        print("Logged out.")
    except Exception as e:
        print(f"Logout failed: {str(e)}")

    return f"Successfully downloaded {len(downloaded_files)} files to {output_directory}."


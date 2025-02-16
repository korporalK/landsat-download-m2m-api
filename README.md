# Landsat API Project

## Overview
This project provides a Python-based tool for efficiently downloading Landsat Collection 2 Level-2 imagery using the USGS M2M API. The script offers the following features:

- **Automated Data Access**: Streamlines the process of searching, requesting, and downloading Landsat imagery
- **Multiple Sensor Support**: Compatible with Landsat 5, 7, 8, and 9 satellites
- **Concurrent Downloads**: Uses async/await patterns for efficient parallel downloading
- **Flexible Data Selection**: 
  - Filter by date range and cloud cover percentage
  - Select specific spectral bands
  - Define area of interest using bounding box coordinates
- **Post-Processing Options**: 
  - Automatic extraction of downloaded archives
  - Band-specific downloads to reduce data volume
  - Cleanup options for managing storage

The tool is designed for researchers, GIS analysts, and remote sensing specialists who need programmatic access to Landsat imagery.

## Requirements
- Python 3.x
- Required Python packages listed in `requirements.txt`
- M2M API Acess Authorization Token

## Installation
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/landsat-api-project.git
   cd landsat-api-project
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set the environment variables for Earthdata username and token:
   ```
   export EARTHDATA_USER='your_username'
   export EARTHDATA_TOKEN='your_token'
   ```

## How to get M2M API Access Authorization Token`
To obtain the M2M API Access Authorization Token, follow these steps:

1. Register for an account on the [USGS Earthdata Login](https://urs.earthdata.nasa.gov/users/new).
2. After registering, log in to your account @ https://ers.cr.usgs.gov/
3. Navigate to the [USGS M2M API](https://m2m.cr.usgs.gov/api/docs/) page to read about the API Documentation.
4. Follow the instructions to generate an API token: https://www.usgs.gov/media/files/m2m-application-token-documentation
5. Copy the generated token and use it in your environment variables as shown in the Installation section.


## Usage
To use the script, call the `download_landsat_tool` function from `landsat_m2m_api.py` with the desired parameters:

```python
from src.landsat_m2m_api import download_landsat_tool

result = download_landsat_tool(
    output_directory="/path/to/output",
    start_date="2023-01-01",
    end_date="2023-01-31",
    max_cloud_cover=20.0,
    landsat_sensors=["L8", "L9"],
    bands=["B2", "B3", "B4"],
    bounding_box="-122.5,37.5,-122.0,38.0",
    delete_archive=True,
    max_concurrent_downloads=5
)
```

### Parameters

- `output_directory` (str): Directory where files will be saved
- `start_date` (str): Start date in 'YYYY-MM-DD' format
- `end_date` (str): End date in 'YYYY-MM-DD' format
- `max_cloud_cover` (float): Maximum cloud cover percentage (0-100)
- `landsat_sensors` (List[str]): Sensors to include (L8, L9, L7, L5)
- `bands` (List[str]): Specific bands to download (e.g., ["B2", "B3", "B4"])
- `bounding_box` (str): Area of interest in "min_lon,min_lat,max_lon,max_lat" format
- `delete_archive` (bool): Whether to delete tar archives after extraction
- `max_concurrent_downloads` (int): Maximum number of simultaneous downloads


## Running Tests
To run the tests, execute the following command:
```
pytest tests/test_landsat_m2m_api.py
```

## Contribution
Feel free to submit issues or pull requests. Please ensure that your code includes appropriate tests.

## License
This project is licensed under the MIT License. See the LICENSE file for details.


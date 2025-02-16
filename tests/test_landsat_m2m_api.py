import pytest
from src.landsat_m2m_api import download_landsat_tool


# Example usage:
output_directory = "test_output"
start_date = "2022-01-01"
end_date = "2022-01-31"
bounding_box = "-120.0,35.0,-119.0,36.0"
max_cloud_cover = 20.0
landsat_sensors = ["L8", "L9"]
bands = ["B2", "B3", "B4"]
aoi_feature_class = None
delete_archive = True
max_concurrent_downloads = 5

result = download_landsat_tool(output_directory="test_output", start_date="2022-01-01", end_date="2022-01-31", 
                               bounding_box="-120.0,35.0,-119.0,36.0", max_cloud_cover=20.0, 
                               landsat_sensors=["L8", "L9"], bands=["B2", "B3", "B4"], 
                               delete_archive=True, max_concurrent_downloads=5)
import pytest
from src.landsat_m2m_api import download_landsat_tool

def test_download_landsat_tool_valid_parameters():
    output_directory = "test_output"
    start_date = "2022-01-01"
    end_date = "2022-01-31"
    bounding_box = "-120.0,35.0,-119.0,36.0"
    
    result = download_landsat_tool(
        output_directory=output_directory,
        start_date=start_date,
        end_date=end_date,
        bounding_box=bounding_box
    )
    
    assert "downloaded" in result.lower()  # Check if the result indicates successful download

def test_download_landsat_tool_missing_parameters():
    result = download_landsat_tool(
        output_directory=None,
        start_date="2022-01-01",
        end_date="2022-01-31",
        bounding_box="-120.0,35.0,-119.0,36.0"
    )
    
    assert result == "Error: output_directory, start_date, end_date, and bounding_box are required."

def test_download_landsat_tool_invalid_bounding_box():
    output_directory = "test_output"
    start_date = "2022-01-01"
    end_date = "2022-01-31"
    bounding_box = "invalid_bounding_box"
    
    result = download_landsat_tool(
        output_directory=output_directory,
        start_date=start_date,
        end_date=end_date,
        bounding_box=bounding_box
    )
    
    assert result == "Error: Invalid bounding_box format. Use 'min_lon,min_lat,max_lon,max_lat'."
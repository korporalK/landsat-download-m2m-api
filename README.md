# Landsat API Project

## Overview
This project provides a Python script for downloading Landsat Collection 2 Level-2 imagery using the USGS M2M API. The script automates the process of searching for, requesting, and downloading Landsat data.

## Requirements
- Python 3.x
- Required Python packages listed in `requirements.txt`

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

## Usage
To use the script, call the `download_landsat_tool` function from `landsat_m2m_api.py` with the desired parameters. Ensure that the output directory and bounding box are specified.

## Running Tests
To run the tests, execute the following command:
```
pytest tests/test_landsat_m2m_api.py
```

## Contribution
Feel free to submit issues or pull requests. Please ensure that your code adheres to the project's coding standards and includes appropriate tests.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
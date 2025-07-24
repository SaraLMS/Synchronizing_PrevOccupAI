# ------------------------------------------------------------------------------------------------------------------- #
# imports
# ------------------------------------------------------------------------------------------------------------------- #
import os
from typing import Dict
import re

# internal imports
import load

# ------------------------------------------------------------------------------------------------------------------- #
# public functions
# ------------------------------------------------------------------------------------------------------------------- #


def get_device_filename_timestamp(folder_path: str) -> Dict[str, str]:
    """
    Extracts the start time for each device based on the timestamps in the filenames within a folder.

    This function scans the specified folder, identifies files corresponding to devices, and parses each filename
    to extract the device name and its associated timestamp. The extracted time (formatted as 'hh:mm:ss.000')
    is assumed to represent the start time of data collection for that device.

    :param folder_path: Path to the folder containing the raw data files.
    :return: A dictionary mapping each device name to its extracted start time.
             Example: {"watch": "11:00:01.000", "F0A55C68B2E1": "11:05:34.000"}
    """

    # innit dictionary to store the results
    start_times_dict: Dict[str, str] = {}

    for filename in os.listdir(folder_path):

        # extract device from filename
        device_name = load.extract_device_from_filename(filename)

        # extract timestamp from filename
        device_timestamp = _extract_timestamp_from_filename(filename)

        # update dictionary
        start_times_dict[device_name] = device_timestamp

    return start_times_dict


def extract_device_num_from_folder_path(folder_path: str):

    # find the group in the folder path (group1, group2, group3 ...)
    if match := re.search(r'LIBPhys #(\d+)', folder_path):

        return match.group()

    else:
        return None
# ------------------------------------------------------------------------------------------------------------------- #
# private functions
# ------------------------------------------------------------------------------------------------------------------- #

def _extract_timestamp_from_filename(filename: str) -> str:
    """
    Extracts the time portion from an OpenSignals filename and converts it to 'hh:mm:ss.000' format.

    Example:
        Input:  "opensignals_ANDROID_ROTATION_VECTOR_2022-05-02_11-00-01"
        Output: "11:00:01.000"

    :param filename: The filename string containing a timestamp
    :return: The timestamp in the 'hh:mm:ss.000' format
    """
    # Regex to extract the timestamp from filename - format is hh-mm-ss
    match = re.search(r'_(\d{2}-\d{2}-\d{2})$', filename)

    if not match:
        raise ValueError(f"No valid time found in filename: {filename}")

    # Change format to hh:mm:ss.000
    time_str = match.group(1).replace('-', ':') + ".000"

    return time_str


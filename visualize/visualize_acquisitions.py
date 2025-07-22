# ------------------------------------------------------------------------------------------------------------------- #
# imports
# ------------------------------------------------------------------------------------------------------------------- #
import os
import glob
import pandas as pd
from typing import Dict
import re

# internal imports
import load

# ------------------------------------------------------------------------------------------------------------------- #
# file specific constants
# ------------------------------------------------------------------------------------------------------------------- #
LOGGER_FILENAME_PREFIX = 'opensignals_ACQUISITION_LOG_'
LENGTH = 'length'
START_TIMES = 'start_times'

# ------------------------------------------------------------------------------------------------------------------- #
# public functions
# ------------------------------------------------------------------------------------------------------------------- #

def visualize_daily_acquisitions(daily_folder_path: str):
    final_dict: Dict[str, Dict[str, list]] = {}

    # iterate through the folders pertaining to the different acquisitions on the same day
    for acquisition_folder in os.listdir(daily_folder_path):

        # generate folder_path
        acquisition_folder_path = os.path.join(daily_folder_path, acquisition_folder)

        # load signals
        signals_dict = load.load_data_from_same_recording(acquisition_folder_path)

        # get lengths of the signals
        length_dict = _calculate_df_length(signals_dict)

        # logger file exists
        if _check_logger_file(acquisition_folder_path):

            # load timestamps of each device based on the logger file
            start_times_dict = load.load_logger_file_info(acquisition_folder_path)

        # no logger file
        else:

            # extract timestamps from the filename
            start_times_dict = _get_device_filename_timestamp(acquisition_folder_path)

        # combine and store results
        for device in length_dict:
            if device not in final_dict:
                final_dict[device] = {LENGTH: [], START_TIMES: []}

            final_dict[device][LENGTH].append(length_dict[device])

            # safely get start time (may not be available if something went wrong)
            start_time = start_times_dict.get(device, None)
            final_dict[device][START_TIMES].append(start_time)

    return final_dict


# ------------------------------------------------------------------------------------------------------------------- #
# private functions
# ------------------------------------------------------------------------------------------------------------------- #

def _calculate_df_length(df_dict: Dict[str, pd.DataFrame]) -> Dict[str, int]:
    """
    Calculates the number of rows in each DataFrame contained in a dictionary.
    It returns a new dictionary with the same keys, where each value is the number of rows (i.e., length)
    of the corresponding DataFrame.

    :param df_dict: A dictionary mapping keys to pandas DataFrames.
    :return: A dictionary mapping each key to the number of rows in its corresponding DataFrame.
    """
    lengths_dict: Dict[str, int] = {}

    for key, df in df_dict.items():

        lengths_dict[key] = df.shape[0]

    return lengths_dict


def _check_logger_file(folder_path: str) -> bool:
    """
    Checks if a logger file exists in the specified folder and that it is not empty.
    Assumes logger file name starts with 'opensignals_ACQUISITION_LOG_' and includes
    a timestamp.

    :param folder_path: The path to the folder containing the RAW acquisitions.
    :return: True if it exists and is not empty, otherwise False.
    """
    # Pattern to match the logger file, assuming it starts with LOGGER_FILENAME_PREFIX
    pattern = os.path.join(folder_path, f'{LOGGER_FILENAME_PREFIX}*')

    # Use glob to find files that match the pattern
    matching_files = glob.glob(pattern)

    # iterate through the files that match the logger file prefix - should only be one
    for file_path in matching_files:

        # gets the first one (and only) that is not empty
        if os.path.getsize(file_path) > 0:
            return True

    return False


def _get_device_filename_timestamp(folder_path: str) -> Dict[str, str]:
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
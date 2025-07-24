# ------------------------------------------------------------------------------------------------------------------- #
# imports
# ------------------------------------------------------------------------------------------------------------------- #
import os
import glob
import pandas as pd
from typing import Dict
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import re

# internal imports
import load
from .parser import get_device_filename_timestamp, extract_device_num_from_folder_path

# ------------------------------------------------------------------------------------------------------------------- #
# file specific constants
# ------------------------------------------------------------------------------------------------------------------- #
LOGGER_FILENAME_PREFIX = 'opensignals_ACQUISITION_LOG_'
LENGTH = 'length'
START_TIMES = 'start_times'

# ------------------------------------------------------------------------------------------------------------------- #
# public functions
# ------------------------------------------------------------------------------------------------------------------- #

def visualize_daily_acquisitions(daily_folder_path: str, fs=100):
    """
    Visualizes daily signal acquisitions per device as horizontal bars over a timeline.

    :param daily_folder_path: Path to the folder containing acquisition subfolders.
    :param fs: Sampling frequency used to convert sample count to duration (default 100 Hz).
    """
    acquisitions_dict = _get_daily_acquisitions_metadata(daily_folder_path)

    fig, ax = plt.subplots(figsize=(10, 4))

    color_palette = ['#3C787E', "#F07A15", '#f2b36f', '#4D92D0']

    # variable to hold the earliest timestamp among all device acquisitions
    min_start_time = None

    # variable to hold the last end time among all device acquisitions - to define the right boundary of the bar
    latest_end_time = None

    # First pass: determine global min start and max end time for axis limits
    for data in acquisitions_dict.values():

        # loop over the start times and durations of each device
        for length, start_str in zip(data[LENGTH], data[START_TIMES]):

            # convert to datetime to perform time arithmetic and comparisons
            start_dt = datetime.strptime(start_str, "%H:%M:%S.%f")

            # convert to seconds to know the full duration of the recording
            end_dt = start_dt + timedelta(seconds=length / fs)

            # if it is the first start time or it is earlier than the previously recorded minimum - update
            if min_start_time is None or start_dt < min_start_time:
                min_start_time = start_dt

            # if it is the first end time or this recording finishes later thane« latest_end_time - update
            if latest_end_time is None or end_dt > latest_end_time:
                latest_end_time = end_dt

    if min_start_time is None:
        raise ValueError("No valid start times found.")

    # Loop over each device and its corresponding data in the dictionary
    for i, (device, data) in enumerate(acquisitions_dict.items()):

        # get the list of lengths and start times
        lengths = data[LENGTH]
        start_times = data[START_TIMES]

        # change muscleban device name from mac address to 'mban_left' or 'mban_right'
        if match := re.search(r'[A-Z0-9]{12}', device):
            # load metadata
            meta_data_df = load.load_meta_data()

            # change device name to mban side
            device = load.get_muscleban_side(meta_data_df, match.group())

            # remove underscore
            device = device.replace("_", " ")

        vertical_spacing = 0.3
        bar_height = 0.2

        # if start time is missing, skip
        for length, start_str in zip(lengths, start_times):
            if not start_str:
                continue

            # convert to datetime object to calculate the duration
            start_dt = datetime.strptime(start_str, "%H:%M:%S.%f")
            duration = timedelta(seconds=length / fs)


            # draw the horizontal bars (broken_barh) for each device with the correct length
            ax.broken_barh(
                [(start_dt, duration)],
                (i * vertical_spacing - bar_height / 2, bar_height),
                facecolors=color_palette[i]
            )

        # manually place the device labels left of all bars
        # timedelta here is just to add space since min_start_time is also a datetime object
        ax.text(min_start_time - timedelta(seconds=500), i*vertical_spacing, device,
                va='center', ha='right', fontsize=12)

    # Format x-axis as hh:mm:ss
    ax.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))

    # Set x-limits based the first time stamp and the latest one
    ax.set_xlim(min_start_time, latest_end_time + timedelta(seconds=5))

    # Keep only the bottom axis line
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)

    ax.set_xlabel("Time (hh:mm:ss)")
    ax.set_yticks([])  # Hide y-ticks since labels are placed manually
    ax.set_title(extract_device_num_from_folder_path(daily_folder_path))
    plt.tight_layout()
    plt.show()


# ------------------------------------------------------------------------------------------------------------------- #
# private functions
# ------------------------------------------------------------------------------------------------------------------- #

def _get_daily_acquisitions_metadata(daily_folder_path: str) -> Dict[str, Dict[str, list]]:
    """
    Aggregates signal metadata (length and start time) for each device across multiple acquisitions recorded in a single day.
    This function is intended for data collected from a smartwatch, smartphone, or MuscleBans (Plux Wireless Biosignals),
    using the OpenSignals application.

    This function scans a daily folder containing multiple acquisition subfolders. For each acquisition:
        - Loads the raw signals and calculates the number of rows (length) per device.
        - Determines the start timestamp for each device (using the logger file if available, if not use the filenames).
        - Accumulates these values into a dictionary grouped by device.

    :param daily_folder_path: Path to the folder containing all acquisitions for a single the day
    :return: A dictionary where keys are device names, and values are dictionaries with two lists:
             - 'length': List of signal lengths.
             - 'start_times': List of corresponding start timestamps.
             Example:
             {
                 "phone": {"length": [10000], "start_times": ["11:20:20.000"]},
                 "watch": {"length": [500, 950], "start_times": ["10:20:50.000", "12:00:00.000"]}
             }
    """
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
            start_times_dict = get_device_filename_timestamp(acquisition_folder_path)

        # combine and store results
        for device in length_dict:
            if device not in final_dict:

                final_dict[device] = {LENGTH: [], START_TIMES: []}

            # add the length to the final dictionary
            final_dict[device][LENGTH].append(length_dict[device])

            # add the start time to the dictionary
            start_time = start_times_dict.get(device, None)
            final_dict[device][START_TIMES].append(start_time)

    return final_dict


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

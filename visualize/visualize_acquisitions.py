# ------------------------------------------------------------------------------------------------------------------- #
# imports
# ------------------------------------------------------------------------------------------------------------------- #
import os
import glob
import pandas as pd
from typing import Dict, Optional, List, Union
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import re

# internal imports
import load
from constants import PHONE
from .parser import get_device_filename_timestamp
from utils import extract_device_num_from_path, extract_group_from_path, extract_date_from_path, \
    get_most_common_acquisition_times, create_dir

# ------------------------------------------------------------------------------------------------------------------- #
# file specific constants
# ------------------------------------------------------------------------------------------------------------------- #
LOGGER_FILENAME_PREFIX = 'opensignals_ACQUISITION_LOG_'
LENGTH = 'length'
START_TIMES = 'start_times'
COLOR_PALLETE = ['#f2b36f', "#F07A15", '#4D92D0', '#3C787E']
DEVICE_ORDER = ['mBAN left', 'mBAN right', 'watch','phone']
# ------------------------------------------------------------------------------------------------------------------- #
# public functions
# ------------------------------------------------------------------------------------------------------------------- #

def visualize_group_acquisitions(group_folder_path, fs=100):

    # iterate through the subjects in the group
    for subject_folder in os.listdir(group_folder_path):

        # get path for the subject data
        subject_folder_path = os.path.join(group_folder_path, subject_folder)

        # iterate through the daily acquisitions
        for daily_folder in os.listdir(subject_folder_path):

            # plot visualizations for all acquisitions of the subject
            visualize_daily_acquisitions(subject_folder_path, daily_folder, fs=fs)



def visualize_daily_acquisitions(subject_folder_path: str, date: str, fs=100):
    """
    Visualizes daily signal acquisitions per device as horizontal bars over a timeline.

    :param subject_folder_path: Path to the subject's folder.
    :param date: Date string (YYYY-MM-DD) of the acquisitions to visualize.
    :param fs: Sampling frequency (default 100 Hz).
    """

    # Get the dictionary with the lengths and start times
    acquisitions_dict = _get_daily_acquisitions_metadata(subject_folder_path, date)

    # Get the missing data, if any
    missing_data_dict = _get_missing_data(subject_folder_path, acquisitions_dict)

    # Prepare full daily path
    daily_folder_path = os.path.join(subject_folder_path, date)

    fig, ax = plt.subplots(figsize=(10, 3))

    vertical_spacing = 0.2
    bar_height = 0.1

    # variable to hold the earliest timestamp among all device acquisitions
    min_start_time = None

    # variable to hold the last end time among all device acquisitions - to define the right boundary of the bar
    latest_end_time = None

    # Normalize acquisition device names (convert MAC to readable names)
    normalized_acquisitions_dict = {}
    meta_data_df = load.load_meta_data()

    for device_raw, data in acquisitions_dict.items():
        if match := re.search(r'[A-Z0-9]{12}', device_raw):
            device = load.get_muscleban_side(meta_data_df, match.group()).replace("_", " ")
        else:
            device = device_raw
        normalized_acquisitions_dict[device] = data

    # Also normalize missing data device names
    normalized_missing_data_dict = {}
    for device_raw, data in missing_data_dict.items():
        if match := re.search(r'[A-Z0-9]{12}', device_raw):
            device = load.get_muscleban_side(meta_data_df, match.group()).replace("_", " ")
        else:
            device = device_raw
        normalized_missing_data_dict[device] = data

    # Loop over both normalized dictionaries to find time range
    for data_dict in (normalized_acquisitions_dict, normalized_missing_data_dict):
        for data in data_dict.values():
            for length, start_str in zip(data[LENGTH], data[START_TIMES]):
                start_dt = datetime.strptime(start_str, "%H-%M-%S")
                end_dt = start_dt + timedelta(seconds=length / fs)

                if min_start_time is None or start_dt < min_start_time:
                    min_start_time = start_dt

                if latest_end_time is None or end_dt > latest_end_time:
                    latest_end_time = end_dt

    # Sort devices using DEVICE_ORDER
    sorted_devices = sorted(
        normalized_acquisitions_dict.keys(),
        key=lambda d: DEVICE_ORDER.index(d) if d in DEVICE_ORDER else len(DEVICE_ORDER)
    )

    device_to_index = {}

    # Plot actual acquisitions
    for i, device in enumerate(sorted_devices):
        data = normalized_acquisitions_dict[device]
        device_to_index[device] = i

        lengths = data[LENGTH]
        start_times = data[START_TIMES]

        for length, start_str in zip(lengths, start_times):
            start_dt = datetime.strptime(start_str, "%H-%M-%S")
            duration = timedelta(seconds=length / fs)
            y_center = i * vertical_spacing
            y_bottom = y_center - bar_height / 2
            y_top = y_center + bar_height / 2

            ax.broken_barh(
                [(start_dt, duration)],
                (y_bottom, bar_height),
                facecolors=COLOR_PALLETE[i % len(COLOR_PALLETE)]
            )

            ax.hlines(y=[y_bottom, y_top],
                      xmin=min_start_time,
                      xmax=latest_end_time + timedelta(seconds=5),
                      colors="#06171C", linestyles="dashed", linewidth=1.1)

        ax.text(min_start_time - timedelta(seconds=500), i * vertical_spacing, device,
                va='center', ha='right', fontsize=12, color='#06171C')

    # Plot missing data
    for device, data in normalized_missing_data_dict.items():
        if device not in device_to_index:
            continue

        i = device_to_index[device]
        y_center = i * vertical_spacing
        y_bottom = y_center - bar_height / 2

        for start_str, length in zip(data[START_TIMES], data[LENGTH]):
            if not start_str:
                continue

            start_dt = datetime.strptime(start_str, "%H-%M-%S")
            duration = timedelta(seconds=length / fs)

            ax.broken_barh(
                [(start_dt, duration)],
                (y_bottom, bar_height),
                facecolors='lightgray',
                edgecolor='black',
                linestyle='dashed',
                linewidth=0.8
            )

    # Formatting
    ax.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
    ax.set_xlim(min_start_time, latest_end_time + timedelta(seconds=5))

    for spine in ['top', 'right', 'left', 'bottom']:
        ax.spines[spine].set_visible(False)

    ax.set_xlabel("Time (hh:mm:ss)", color='#06171C')
    ax.set_yticks([])

    ax.set_title(
        f"Subject: Group {extract_group_from_path(daily_folder_path)} | "
        f"{extract_device_num_from_path(daily_folder_path)} | {extract_date_from_path(daily_folder_path)}",
        color='#06171C'
    )

    plt.tight_layout()

    # generate output filename
    out_filename = (f"group_{extract_group_from_path(daily_folder_path)}_{extract_device_num_from_path(daily_folder_path)}_"
                    f"{extract_date_from_path(daily_folder_path)}.png")

    # generate output path
    output_path = create_dir(os.getcwd(), f"group_{extract_group_from_path(daily_folder_path)}")

    # save plot
    plt.savefig(os.path.join(output_path, out_filename), dpi=300, bbox_inches='tight')



# ------------------------------------------------------------------------------------------------------------------- #
# private functions
# ------------------------------------------------------------------------------------------------------------------- #

def _get_daily_acquisitions_metadata(subject_folder_path: str, date: str) -> Dict[str, Dict[str, list]]:
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
    final_dict = {}

    daily_folder_path = os.path.join(subject_folder_path, date)

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


def _get_missing_timestamp(subject_folder_path, acquisition_times_list):

    # get the most common start times for the subject
    common_times_list = get_most_common_acquisition_times(subject_folder_path)

    # replace the seconds with '00'
    acquisition_times_list = [time[:-2] + '00' for time in acquisition_times_list]

    # compare sets do get th missing timestamps
    missing_times = set(common_times_list) - set(acquisition_times_list)

    return missing_times


def _get_missing_data(subject_folder_path, acquisitions_dict, fs=100):

    missing_data_dict = {}

    # check if there are missing acquisitions
    for device, data in acquisitions_dict.items():

        # if any device that is not phone didn't acquire 4 times, then it's missing
        if  device != PHONE and len(data[START_TIMES]) < 4:

            # get missing timestamps list
            missing_times_list = _get_missing_timestamp(subject_folder_path, data[START_TIMES])

            # initialize if device not in dict
            if device not in missing_data_dict:
                missing_data_dict[device] = {
                    START_TIMES: [],
                    LENGTH: []
                }

            # add missing times and lengths (should be 20 minutes acquisitions)
            for missing_time in missing_times_list:
                missing_data_dict[device][START_TIMES].append(missing_time)
                missing_data_dict[device][LENGTH].append(20 * 60 * fs)

    return missing_data_dict


# -*- coding: utf-8 -*-
"""
Functions to visualize daily and group-level sensor acquisitions.

Available Functions
-------------------
[Public]
visualize_group_acquisitions(...): Generate daily acquisition plots for each subject in a group.
visualize_daily_acquisitions(...): Plot acquisitions for a subject on a given day, including missing data, and save the visualization as a PNG file.
-------------------

[Private]
_get_daily_acquisitions_metadata(...): Aggregate acquisition lengths and start times for all devices on a given day.
_calculate_df_length(...): Compute the number of rows in each DataFrame of signals.
_check_logger_file(...): Verify if a logger file exists (and is non-empty) in a given folder.
_normalize_device_names(...): Translate raw device names into human-readable labels (Portuguese).
_get_day_string(...): Convert a date string into weekday and formatted date string in the specified locale.
_add_missing_device(...): Add a device missing for the entire day into the missing-data dictionary using a reference device.
_get_acquisition_time_range(...): Determine earliest and latest acquisition times across devices.
_plot_device_bars(...): Draw horizontal bars for each device’s acquisitions or missing data on a timeline.
_plot_reference_acquisition(...): Plot a reference duration line (e.g., 20 min) on top of acquisitions.
_plot_device_labels_and_guides(...): Plot device labels and dashed guidelines for visual clarity.
-------------------
"""

# ------------------------------------------------------------------------------------------------------------------- #
# imports
# ------------------------------------------------------------------------------------------------------------------- #
import os
import glob
import pandas as pd
from typing import Dict, Any, Optional, Tuple, Union, Callable
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.dates import DateFormatter
from matplotlib.patches import Patch
import re
import locale

# internal imports
import load
from constants import ACQUISITION_TIME_SECONDS, MBAN_RIGHT
from .parser import get_device_filename_timestamp
from utils import extract_device_num_from_path, extract_group_from_path, extract_date_from_path, create_dir
from .missing_data import get_missing_data
from .legend_handlers import RefLine, HandlerRefLine

# ------------------------------------------------------------------------------------------------------------------- #
# file specific constants
# ------------------------------------------------------------------------------------------------------------------- #
LOGGER_FILENAME_PREFIX = 'opensignals_ACQUISITION_LOG_'
LENGTH = 'length'
START_TIMES = 'start_times'
COLOR_PALLETE = ['#f2b36f', "#F07A15", '#4D92D0', '#3C787E']

SMARTPHONE = 'Smartphone'
SMARTWATCH = 'Smartwatch'
MBAN_ESQ = "mBAN esq"
MBAN_DIR = "mBAN dir"
DEVICE_ORDER = [MBAN_ESQ, MBAN_DIR, SMARTWATCH,SMARTPHONE]
REF_DEVICES = [SMARTWATCH, MBAN_DIR, MBAN_ESQ]
SMART = 'Smart'

VERTICAL_SPACING = 0.2
BAR_HEIGHT = 0.1
# ------------------------------------------------------------------------------------------------------------------- #
# public functions
# ------------------------------------------------------------------------------------------------------------------- #

def visualize_group_acquisitions(group_folder_path: str, fs=100) -> None:
    """
    Generates a plot with the daily acquisitions for each device and for each subject of the group.

    :param group_folder_path: Path to the folder containing all subjects' data from the group
    :param fs: the sampling frequency (default = 100 Hz)
    :return: None
    """
    # iterate through the subjects in the group
    for subject_folder in os.listdir(group_folder_path):

        # get path for the subject data
        subject_folder_path = os.path.join(group_folder_path, subject_folder)

        # iterate through the daily acquisitions
        for daily_folder in os.listdir(subject_folder_path):

            # plot visualizations for all acquisitions of the subject
            visualize_daily_acquisitions(subject_folder_path, daily_folder, fs=fs)



def visualize_daily_acquisitions(subject_folder_path: str, date: str, fs=100) -> None:
    """
    Visualizes daily signal acquisitions per subject as horizontal bars over a timeline, including missing acquisitions.
    The plot is saved as a PNG file.

    :param subject_folder_path: Path to the subject's folder.
    :param date: Date string (YYYY-MM-DD) of the acquisitions to visualize.
    :param fs: Sampling frequency (default 100 Hz).
    :return: None
    """

    # Get the dictionary with the lengths and start times
    acquisitions_dict = _get_daily_acquisitions_metadata(subject_folder_path, date)

    # Get the missing data, if any
    missing_data_dict = get_missing_data(subject_folder_path, acquisitions_dict)

    # only plot if there's any data
    if acquisitions_dict:

        # get full daily path
        daily_folder_path = os.path.join(subject_folder_path, date)

        # change muscleban device name to mBAN right or mBAN left from the dict with the acquisition data
        acquisitions_dict = _normalize_device_names(acquisitions_dict)

        # change muscleban device name to mBAN right or mBAN left from the dict with the acquisition data
        missing_data_dict = _normalize_device_names(missing_data_dict)

        # if acquisitions dict only has 3 items, then one device was missing for the entire day
        if len(acquisitions_dict) < 4:

            # add missing device to missing_data_dict
            missing_data_dict = _add_missing_device(acquisitions_dict, missing_data_dict, fs=fs)

        # get the minimum and maximum time ranges (datetime) to put the chunks in order and for the x-axis limits
        min_start_time, latest_end_time = _get_acquisition_time_range(acquisitions_dict, missing_data_dict, fs)

        # Sort acquisitions_dict according to DEVICE_ORDER
        acquisitions_dict = {
            d: acquisitions_dict[d]
            for d in sorted(acquisitions_dict.keys(),
                            key=lambda d: DEVICE_ORDER.index(d) if d in DEVICE_ORDER else len(DEVICE_ORDER))
        }

        # Build device_to_index from the union of acquisitions + missing devices
        all_devices = set(acquisitions_dict.keys()) | set(missing_data_dict.keys())
        sorted_devices = sorted(all_devices,
                                key=lambda d: DEVICE_ORDER.index(d) if d in DEVICE_ORDER else len(DEVICE_ORDER))
        device_to_index = {device: i for i, device in enumerate(sorted_devices)}

        fig, ax = plt.subplots(figsize=(10, 3))

        # Plot acquisitions horizontal bars
        _plot_device_bars(ax=ax, data_dict=acquisitions_dict, device_to_index=device_to_index, fs=fs, color_map=lambda i: COLOR_PALLETE[i % len(COLOR_PALLETE)], )

        # Plot missing data horizontal bars
        _plot_device_bars(ax=ax, data_dict=missing_data_dict, device_to_index=device_to_index, fs=fs, color_map=lambda _: 'lightgray',
                          edgecolor='#06171C', linestyle='dashed', linewidth=0.8)

        #Add reference acquisition line (20 minutes)
        _plot_reference_acquisition(ax, acquisitions_dict, missing_data_dict, device_to_index, seconds=20 * 60)

        # plot the dashed guidelines
        _plot_device_labels_and_guides(ax, device_to_index, min_start_time, latest_end_time)

        # Format the time
        ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))
        ax.set_xlim(min_start_time, latest_end_time + timedelta(seconds=5))

        # remove axis lines
        for spine in ['top', 'right', 'left', 'bottom']:
            ax.spines[spine].set_visible(False)

        # add labels to the x-axis and remove the ticks in the y-axis
        ax.set_xlabel("Tempo (hh:mm)", color='#06171C')
        ax.set_yticks([])

        # get the weekday based on the date - portuguese
        week_day, date = _get_day_string(extract_date_from_path(daily_folder_path))
        ax.set_title(f"{week_day} | {date}", color='#06171C')

        # Add legend for missing data
        missing_patch = Patch(facecolor='lightgray', edgecolor='black', linestyle='dashed', label='Sem dados')

        ax.legend(handles=[missing_patch, RefLine()], labels=["Sem dados", f"{ACQUISITION_TIME_SECONDS // 60} minutos"],
            handler_map={RefLine: HandlerRefLine()}, loc='upper left', bbox_to_anchor=(1.02, 1.02), frameon=False,
            handleheight=1, handlelength=2, borderaxespad=0.5)

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

    :param subject_folder_path: Path to the folder containing all data from one subject
    :param date: String pertaining to the date of the acquisition (name of the folder)
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


def _normalize_device_names(acquisitions_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize the keys in the dictionary, which pertains to the device names, for more user-friendly names in portuguese.

    (phone -> Smartphone, watch -> Smartwatch, mBAN left -> mBAN esq, mBAN right -> mBAN dir)
    :param acquisitions_dict: A dictionary where the keys are the device names
    :return: The same dictionary with the normalized device names (keys)
    """
    # change muscleban device name to mBAN right or mBAN left
    normalized_acquisitions_dict: Dict[str, Any] = {}

    # cycle over the devices in the dictionary keys
    for device_raw, data in acquisitions_dict.items():
        if match := re.search(r'[A-Z0-9]{12}', device_raw):

            # load metadata
            meta_data_df = load.load_meta_data()

            # get muscleban side and remove '_'
            device = load.get_muscleban_side(meta_data_df, match.group())

            # translate to portuguese
            if device == MBAN_RIGHT:
                device = MBAN_DIR

            else:
                device = MBAN_ESQ

        # if it's phone or watch keep the device name as it is
        else:
            device = SMART + device_raw

        # add device names to dict
        normalized_acquisitions_dict[device] = data

    return normalized_acquisitions_dict


def _get_day_string(date_string: str, locale_string: str = "Portuguese_Portugal.1252") -> Tuple[str, str]:
    """
    Gets the day as a string (i.e. Mon, Tue, Wednesday, etc.) from a date string in the language of the defined locale
    :param date_string: the date as string. The date should be in the format (year-month-day)
    :param locale_string: string indicating the local for returning the day string in a specific language
    :return: the day of the week as a string
    """
    # get a datetime object from the date string
    date_time = datetime.strptime(date_string, '%Y-%m-%d')

    # set the locale_string
    locale.setlocale(locale.LC_TIME, locale_string)

    return date_time.strftime('%A'), date_time.strftime('%x')


def _add_missing_device(data_dict: Dict[str, Dict[str, list]], missing_data_dict: Dict[str, Dict[str, list]], fs: int) \
        -> Dict[str, Dict[str, list]]:
    """
    Adds a device that did not acquire for the entire day to the missing_data_dict. This function:

    (1) goes over the devices in data_dict and finds one device that can be used as reference
    (watch, mBAN right, or mBAN left)

    (2) gets the timestamps of this reference device. If this device has missing acquisitions, gets the missing
    timestamps from the missing_data_dict.

    (3) all timestamps found will be used for the missing device, therefore these are added to the missing_data_dict,
    as well as, for each added timestamp, a length of 20 minutes (20*60*fs) is added.

    :param data_dict: A dictionary where keys are device names, and values are dictionaries with two lists:
             - 'length': List of signal lengths.
             - 'start_times': List of corresponding start timestamps.
             Example:
             {
                 "phone": {"length": [10000], "start_times": ["11:20:20.000"]},
                 "watch": {"length": [500, 950], "start_times": ["10:20:50.000", "12:00:00.000"]}
             }
    :param missing_data_dict: A dictionary where keys are device names, and values are dictionaries with two lists: length and start times
                                Same format as data_dict.
    :param fs:  the sampling frequency in Hz
    :return: the missing_data_dict with the missing device (and correspondent start times and length) added.
    """

    # variable for holding the device to be used as reference for getting the start times
    ref_device: Optional[str] = None

    # find the devices that are present
    present_devices = set(data_dict.keys()) | set(missing_data_dict.keys())

    # find the missing devices - except phone
    missing_devices = list((set(DEVICE_ORDER) - {SMARTPHONE}) - present_devices)

    # if watch and both muscleBANS are missing, raise error as it is no possible to get timestamps
    if len(missing_devices) == 3:
        raise ValueError("All 3 devices (watch + both mBANs) are missing. Cannot infer missing acquisitions.")

    # (1) get the reference device from the dictionary with the data
    for device in DEVICE_ORDER:

        if device != SMARTPHONE and device in data_dict:

            # get reference device
            ref_device = device
            break

    if ref_device is None:

        # This scenario does not occur, written for code completion
        return missing_data_dict

    # (2) Collect reference times. If the device that was used for reference has no missing start times, use the ones in data_dict.
    ref_times = data_dict[ref_device][START_TIMES].copy()

    # If the reference device has missing start times, merge the ones on both data_dict and missing_data_dict
    if ref_device in missing_data_dict:
        ref_times += missing_data_dict[ref_device][START_TIMES]

    # (3) Add missing devices data to missing_data_dict, including the length of the acquisitions
    for dev in missing_devices:

        missing_data_dict[dev] = {
            START_TIMES: sorted(ref_times),
            LENGTH: [ACQUISITION_TIME_SECONDS * fs] * len(ref_times)
        }

    return missing_data_dict


def _get_acquisition_time_range(acquisitions_dict: Dict[str, Dict[str, list]], missing_data_dict: Dict[str, Dict[str, list]],
                                fs: int) -> Tuple[datetime, datetime]:
    """
    Compute the earliest start time and latest end time from acquisitions and missing data.

    :param acquisitions_dict: Dictionary of acquisitions metadata.
    :param missing_data_dict: Dictionary of missing data metadata.
    :param fs: Sampling frequency (Hz).
    :return: (min_start_time, latest_end_time) as datetime objects.
    """

    # Initialize boundaries as None (they will be updated in the loop)
    min_start_time = None
    latest_end_time = None

    # Iterate over both acquisitions and missing data
    for data_dict in (acquisitions_dict, missing_data_dict):
        # Each device has lists of lengths and start times
        for data in data_dict.values():
            # Pair up each length with its corresponding start time
            for length, start_str in zip(data[LENGTH], data[START_TIMES]):

                # Convert start time string (HH-MM-SS) into datetime object
                start_dt = datetime.strptime(start_str, "%H-%M-%S")

                # Compute end time by adding duration (length / fs seconds)
                end_dt = start_dt + timedelta(seconds=length / fs)

                # Update minimum start time if this one is earlier
                if min_start_time is None or start_dt < min_start_time:
                    min_start_time = start_dt

                # Update maximum end time if this one is later
                if latest_end_time is None or end_dt > latest_end_time:
                    latest_end_time = end_dt

    # Return both boundaries
    return min_start_time, latest_end_time


def _plot_device_bars(ax: Axes, data_dict: Dict[str, Dict[str, list]], device_to_index: Dict[str, int], fs: int,
                      color_map: Union[Callable[[int], str], Dict[str, str]], edgecolor: Optional[str] = None,
                      linestyle: str = 'solid', linewidth: float = 1.0) -> None:
    """
    Plots horizontal bars for each device based on acquisition or missing data.

    :param ax: The matplotlib axis to draw on.
    :param data_dict: Dictionary containing acquisition or missing data.
    :param device_to_index: Mapping from device name to vertical position index.
    :param fs: Sampling frequency.
    :param color_map: Function or dict that returns a facecolor given the device index or name.
    :param edgecolor: Color of bar edge (optional).
    :param linestyle: Line style for the bar edge (default: solid).
    :param linewidth: Width of bar edge lines.
    """
    for device, data in data_dict.items():
        if device not in device_to_index:
            continue

        i = device_to_index[device]
        y_center = i * VERTICAL_SPACING
        y_bottom = y_center - BAR_HEIGHT / 2

        for length, start_str in zip(data[LENGTH], data[START_TIMES]):
            if not start_str:
                continue
            start_dt = datetime.strptime(start_str, "%H-%M-%S")
            duration = timedelta(seconds=length / fs)

            ax.broken_barh(
                [(start_dt, duration)],
                (y_bottom, BAR_HEIGHT),
                facecolors=color_map(i) if callable(color_map) else color_map.get(device, 'gray'),
                edgecolor=edgecolor,
                linestyle=linestyle,
                linewidth=linewidth
            )


def _plot_reference_acquisition(ax: Axes, acquisitions_dict: Dict[str, Dict[str, list]], missing_data_dict: Dict[str, Dict[str, list]],
                                device_to_index: Dict[str, int], seconds: int = 20*60) -> None:
    """
    Plots a reference acquisition line (e.g., 20 minutes) on the first available acquisition
    from one of the devices (watch, mBAN right, or mBAN left).

    :param ax: The matplotlib axis to draw on.
    :param acquisitions_dict: Dictionary of acquisitions with start times and lengths.
    :param missing_data_dict: Dictionary of missing acquisitions with start times and lengths.
    :param device_to_index: Mapping from device name to vertical index for plotting.
    :param seconds: Duration of the reference acquisition in seconds (default: 20 minutes).
    """
    # select the watch to be the bar where the line will be
    ref_device = SMARTWATCH

    # Try acquisitions first, fallback to missing data
    data_dict = acquisitions_dict.get(ref_device) or missing_data_dict.get(ref_device)

    # First chunk
    start_str = data_dict[START_TIMES][0]
    start_dt = datetime.strptime(start_str, "%H-%M-%S")
    end_dt = start_dt + timedelta(seconds=seconds)

    # Position above bar
    y_top = device_to_index[ref_device] * VERTICAL_SPACING + BAR_HEIGHT / 2
    offset = 0.1 * BAR_HEIGHT
    y_line = y_top + offset

    # Draw a double-headed arrow with vertical ticks
    ax.annotate(
        "",
        xy=(end_dt, y_line), xycoords="data",
        xytext=(start_dt, y_line), textcoords="data",
        arrowprops=dict(
            arrowstyle="|-|",
            shrinkA=0, shrinkB=0,
            color="#26373C",
            linewidth=2,
            mutation_scale=2
        )
    )


def _plot_device_labels_and_guides(ax: Axes, device_to_index: Dict[str, int], min_start_time: datetime,
                                   latest_end_time: datetime) -> None:
    """
    Plot dashed horizontal guidelines and device labels on the y-axis.

    :param ax: Matplotlib axis to plot on.
    :param device_to_index: Dictionary mapping device names to their y-index.
    :param min_start_time: Earliest acquisition time (datetime).
    :param latest_end_time: Latest acquisition time (datetime).
    """
    # Loop through devices and their vertical positions
    for device, i in device_to_index.items():
        # Compute vertical positions for the bar and label
        y_center = i * VERTICAL_SPACING
        y_bottom = y_center - BAR_HEIGHT / 2
        y_top = y_center + BAR_HEIGHT / 2

        # Draw dashed horizontal lines at the top and bottom of the bar
        ax.hlines(y=[y_bottom, y_top], xmin=min_start_time, xmax=latest_end_time + timedelta(seconds=5), colors="#06171C", linestyles="dashed", linewidth=1.1)

        # Add the device name as a label on the left side
        ax.text(min_start_time - timedelta(seconds=500), y_center, device, va="center", ha="right", fontsize=12, color="#06171C")
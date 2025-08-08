"""

"""

# ------------------------------------------------------------------------------------------------------------------- #
# imports
# ------------------------------------------------------------------------------------------------------------------- #
from typing import Dict, List
from datetime import datetime

# internal imports
from constants import PHONE
from utils import get_most_common_acquisition_times

# ------------------------------------------------------------------------------------------------------------------- #
# file specific constants
# ------------------------------------------------------------------------------------------------------------------- #
LENGTH = 'length'
START_TIMES = 'start_times'
ACQUISITION_TIME_SECONDS = 20*60 # 20 minute acquisitions
TIME_FORMAT = "%H-%M-%S"
# ------------------------------------------------------------------------------------------------------------------- #
# public functions
# ------------------------------------------------------------------------------------------------------------------- #

def get_missing_data(subject_folder_path: str, acquisitions_dict: Dict[str, Dict[str, list]], fs: int = 100,
                     tolerance_seconds: int = 600) -> Dict[str, Dict[str, list]]:
    """
    Identify and return missing data (start_time and length) for each device (except the phone).

    This function assumes that the smartwatch and two muscleBAN should all acquire data at the same time, four times
    per day. Due to potential connection issues, some acquisitions may be missing. This function determines which
    timestamps are missing for each device, based on what was recorded by the others.

    In the case that all devices failed to acquire in one of these four scheduled acquisitions, this function uses the
    average acquisition times (based on the common acquisition times during the five days of acquisition of the subject),
    to get the missing timestamp.

    Steps:
    (1) Obtain all unique timestamps of all devices, except the phone. As there is always some delay, timestamps that are
        less than five minute apart are considered to be the same one.

    (2) Compare the start_times in the acquisitions_dict with the unique timestamps to get a list with missing timestamps
        for each device.

    (3) If the length of the actual start times and the missing start times is less then four than there was one scheduled
        acquisition that either did not happen or all devices failed. In this case find the last remaining missing timestamps
        based on the average start times of the entire week.

    (4) For each missing timestamp, a default duration (20-minute acquisition) is appended to the list with lengths in
        the missing data dictionary.

    :param subject_folder_path: Path to the folder containing all data from the subject
    :param acquisitions_dict: A dictionary where keys are device names, and values are dictionaries with two lists:
             - 'length': List of signal lengths.
             - 'start_times': List of corresponding start timestamps.
             Example:
             {
                 "phone": {"start_times": ["11:20:20.000"], "length": [10000]},
                 "watch": {"start_times": ["10:20:50.000", "12:00:00.000"], "length": [500, 950]}
             }
    :param fs: the sampling frequency of the sensors in Hz. Default = 100.
    :param tolerance_seconds: Time in seconds used to consider two start times as referring to the same acquisition.
                            Default = 300. (e.g., 12:00:00 and 12:03:00 are considered to be the same start time).
    :return: A dictionary in the same format as `acquisitions_dict`, but containing only the missing acquisitions
             detected for each device.
    """

    # dictionary to store the missing data with the same format as the dictionary storing the actual acquisitions
    missing_data_dict: Dict[str, Dict[str, list]] = {}

    # check if there are missing acquisitions
    for device, data in acquisitions_dict.items():

        # skip if it's phone
        if device == PHONE:
            continue

        # if any device that is not phone didn't acquire 4 times, then it's missing
        if  len(data[START_TIMES]) < 4:

            # (1) get the unique timestamps - all timestamps of the devices that should acquire at the same time
            unique_timestamps_list = _find_unique_timestamps(acquisitions_dict, tolerance_seconds)

            # (2) compare the actual timestamps with the unique to get missing timestamps for the device
            missing_times_list = _get_missing_timestamps(unique_timestamps_list, data[START_TIMES])

            # (3) check if there are still missing timestamps - no device connected for the scheduled acquisition
            if len(data[START_TIMES]) + len(missing_times_list) < 4:

                # create list with the actual timestamps and the missing timestamps found in get_missing_time_from_device
                temp_list = data[START_TIMES] + missing_times_list

                # Get the most common expected acquisition based on the average of all days
                average_times_list = get_most_common_acquisition_times(subject_folder_path)

                # use the averages to get only the timestamps that are missing on both devices
                missing_times_list.extend(_get_missing_timestamps(average_times_list, temp_list))

                # handle the case where the acquisition time are so mismatched that data[START_TIMES] + missing_times_list > 4
                if len(data[START_TIMES]) + len(missing_times_list) > 4:
                    missing_times_list.pop(-1)

            # initialize if device not in dict
            if device not in missing_data_dict:
                missing_data_dict[device] = {
                    START_TIMES: [],
                    LENGTH: []
                }

            # (4) add missing times and lengths (should be 20 minutes acquisitions)
            for missing_time in missing_times_list:
                missing_data_dict[device][START_TIMES].append(missing_time)
                missing_data_dict[device][LENGTH].append(ACQUISITION_TIME_SECONDS * fs)

    return missing_data_dict


# ------------------------------------------------------------------------------------------------------------------- #
# private functions
# ------------------------------------------------------------------------------------------------------------------- #


def _has_close_time(time: datetime, time_list_dt: List[datetime], tolerance_seconds: int) -> bool:
    return any(abs((time - t).total_seconds()) <= tolerance_seconds for t in time_list_dt)


def _get_missing_timestamps(unique_timestamps_list: List[datetime], acquisitions_times_list: List[str],
                            tolerance_seconds=600) -> List[str]:

    # innit list to store the missing times
    missing_times = []

    # change the sensor start times to datetime
    device_timestamp_dt = [datetime.strptime(timestamp, TIME_FORMAT) for timestamp in acquisitions_times_list]

    # iterate through the unique timestamps
    for timestamp in unique_timestamps_list:

        # check if there is a timestamp that is NOT similar to the one in unique_timestamps_list
        if not _has_close_time(timestamp,device_timestamp_dt, tolerance_seconds):

            # add to the list with missing times in the correct format
            missing_times.append(timestamp.strftime(TIME_FORMAT))

    return missing_times


def _find_unique_timestamps(acquisitions_dict: Dict[str, Dict[str, list]], tolerance_seconds: int) -> List[datetime]:

    # list for holding all timestamps found for the 3 devices that acquire at the same time
    all_daily_timestamps: List[datetime] = []

    for device, data in acquisitions_dict.items():

        # skip if its phone
        if device == PHONE:
            continue

        # change to datetime objects to perform mathematics
        acquisition_times_dt = [datetime.strptime(time, TIME_FORMAT) for time in data[START_TIMES]]
        all_daily_timestamps.extend(acquisition_times_dt)

    # since these devices don't start exactly at the same time, remove the timestamps that are very similar based on tolerance_seconds
    # list for holding the unique timestamps
    filtered_timestamps: List[datetime] = []

    # iterate through the sorted list
    for timestamp in sorted(all_daily_timestamps):

        # if list is empty add the first timestamp
        if not filtered_timestamps:

            filtered_timestamps.append(timestamp)

        else:
            # check if this timestamp is similar to the previous value add only if it's not
            if not _has_close_time(timestamp, filtered_timestamps, tolerance_seconds):
                filtered_timestamps.append(timestamp)


    return filtered_timestamps
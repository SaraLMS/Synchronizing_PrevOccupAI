"""
Utility functions for working with subject folder structures and acquisition times.

Available Functions
-------------------
[Public]
create_dir(...): Create a new directory inside a specified path if it does not already exist.
extract_device_num_from_path(...): Extract the device/subject identifier (e.g., "#001") from a folder path.
extract_group_from_path(...): Extract the group number (e.g., "1", "2", "3") from a folder path.
extract_date_from_path(...): Extract the date string (YYYY-MM-DD) from a folder path.
get_most_common_acquisition_times(...): Find the four most common acquisition times for a subject by scanning folder names and filtering device data.
get_most_common_times(...): Compute the most common acquisition times from a list, with optional adjustment to merge times closer than 20 minutes.
-------------------

[Private]
_remove_dates(...): Remove date folder names from a folder list, keeping only acquisition time folders.
_adjust_most_common_times(...): Filter out acquisition times that are too close (< 20 minutes apart), keeping the most frequent ones.
-------------------
"""

# ------------------------------------------------------------------------------------------------------------------- #
# imports
# ------------------------------------------------------------------------------------------------------------------- #
from typing import Optional, List
import re
import os
from collections import Counter
from datetime import datetime

#internal imports
from constants import ANDROID, ANDROID_WEAR
# ------------------------------------------------------------------------------------------------------------------- #
# public functions
# ------------------------------------------------------------------------------------------------------------------- #

def create_dir(path, folder_name):
    """
    creates a new directory in the specified path
    :param path: the path in which the folder_name should be created
    :param folder_name: the name of the folder that should be created
    :return: the full path to the created folder
    """

    # join path and folder
    new_path = os.path.join(path, folder_name)

    # check if the folder does not exist yet
    if not os.path.exists(new_path):
        # create the folder
        os.makedirs(new_path)

    return new_path


def extract_device_num_from_path(folder_path: str) -> Optional[str]:
    # returns #001
    # folder name starts with 'group' (i.e.: group1, group2, group3...)
    if match := re.search(r'LIBPhys (#\d+)', folder_path):

        return match.group(1)

    else:
        return None


def extract_group_from_path(folder_path: str) -> Optional[str]:
    """

    :param folder_path:
    :return:
    """

    # find the group in the folder path (group1, group2, group3 ...)
    if match := re.search(r'group(\d+)', folder_path):

        return match.group(1)

    else:
        return None


def extract_date_from_path(folder_path: str) -> Optional[str]:
    """

    :param folder_path:
    :return:
    """

    # find the group in the folder path (group1, group2, group3 ...)
    if match := re.search(r'\b(\d{4}-\d{2}-\d{2})\b', folder_path):

        return match.group(1)

    else:
        return None


def get_most_common_acquisition_times(data_path: str) -> List[datetime]:
    """
    retrieves the four most common acquisition times found in all acquisition times for the subjects.
    The acquisition times are found by retrieving all folder names that contain a time that can be found within
    data_path.
    :param data_path: the path to the data of the current subject
    :return: list with the four most common acquisition times. In case there are less than four acquisition times found,
    then only those are returned.
    """
    # list for storing the acquisition times
    acquisition_times_list = []

    # check for group 1
    if 'group1' in data_path:

        for _, dirs, files in os.walk(data_path):
            acquisition_times_list.extend(dirs)
    else:

        # get all folder names within data path
        for root, _, files in os.walk(data_path):

            # check if any file contains '_ANDROID_WEAR_' and if no file contains '_ANDROID_' without '_WEAR_'
            # this is done to filter out the folders that contain the phone data
            contains_android_wear = any(ANDROID_WEAR in filename for filename in files)
            contains_android_only = any(ANDROID in filename and ANDROID_WEAR not in filename for filename in files)

            # filter for folders that contain EMG data (excluding folders that contain the phone data)
            if contains_android_wear and not contains_android_only:
                acquisition_times_list.append(os.path.basename(root))

    # remove all folder names that are not times (in the database structure there are date and time folders only)
    acquisition_times_list = _remove_dates(acquisition_times_list)

    # standardize the times (replacing seconds with 00)
    acquisition_times_list = [time[:-2] + '00' for time in acquisition_times_list]

    # find the most common times (usually 4 due to four acquisitions a day, but could also be less)
    acquisition_times_list = get_most_common_times(acquisition_times_list, adjust_close_times=True)

    return [datetime.strptime(time, "%H-%M-%S") for time in acquisition_times_list]


def get_most_common_times(acquisition_times_list, adjust_close_times=False):
    """
    gets the most common acquisition times. In case there are > 4 unique times the four most common times are return,
    otherwise just the unique acquisition times are returned.
    :param acquisition_times_list:
    :param adjust_close_times: boolean flag for adjusting times that are closer than 20 min to each other. When this
                               flag is set to True, the times in acquisition_times_list are adjusted in the following
                               way.
                               Example:
                               input:  ['10-30-00', '10-31-00', '10-35-00', '10-41-00', '11-00-00', '11-12-00']
                               output: ['10-30-00', '10-30-00', '10-30-00', '10-30-00', '11-00-00', '11-00-00']
    :return: list containing the four most common times within the passed acquisition_times_list
    """

    # check if the number of unique times is less than 4
    if len(set(acquisition_times_list)) <= 4:

        # get the unique times sorted
        most_common_times = sorted(list(set(acquisition_times_list)))

    else:

        # count the occurrences
        time_count = Counter(acquisition_times_list)

        if adjust_close_times:
            time_count = _adjust_most_common_times(time_count)

        # get the four most common times
        most_common = time_count.most_common(4)

        # Extract the times in ascending order if there's a tie
        most_common_times = sorted([time[0] for time in most_common])

    return most_common_times


# ------------------------------------------------------------------------------------------------------------------- #
# private functions
# ------------------------------------------------------------------------------------------------------------------- #
def _remove_dates(folder_list):
    """
    removes date folder names from the folder_list, thus only time folder names are kept.
    :param folder_list: a list containing all sub-folder names for a subject in the database
    :return: list with only acquisition time folder names
    """
    # Regular expression to match date patterns (HH-MM-SS)
    date_pattern = re.compile(r'\d{2}-\d{2}-\d{2}')

    # Filter out strings that don't match the date pattern
    result = [item for item in folder_list if re.match(date_pattern, item)]

    return result


def _adjust_most_common_times(counter):
    """
    Filter times that are too close to each other, keeping only those at least 20 minutes apart.
    :param counter: Counter object with times as keys and occurrences as values.
    :return: Counter object with filtered times.
    """

    # Convert time strings to datetime objects and sort by occurrences and then by time
    times = [(datetime.strptime(time, '%H-%M-%S'), time, count) for time, count in counter.items()]
    times.sort(key=lambda x: (-x[2], x[0]))  # Sort by occurrences (desc) and then by time (asc)

    # List to keep the filtered times
    filtered_times = []

    # Iterate and filter times
    for i in range(len(times)):

        current_time, current_time_str, current_count = times[i]

        # Check if the current time is too close to any already accepted time
        too_close = False
        for filtered_time, _, _ in filtered_times:
            if abs((current_time - filtered_time).total_seconds()) < 20 * 60:
                too_close = True
                break

        # If not too close, add to filtered times
        if not too_close:
            filtered_times.append(times[i])

    # Convert back to Counter
    result_counter = Counter({time_str: count for _, time_str, count in filtered_times})

    return result_counter

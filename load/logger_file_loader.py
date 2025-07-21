# ------------------------------------------------------------------------------------------------------------------- #
# imports functions
# ------------------------------------------------------------------------------------------------------------------- #
import os
import pandas as pd
import glob
from typing import Optional

# ------------------------------------------------------------------------------------------------------------------- #
# file specific constants
# ------------------------------------------------------------------------------------------------------------------- #
LOGGER_FILENAME_PREFIX = 'opensignals_ACQUISITION_LOG_'
TIMESTAMP = 'timestamp'
LOG = 'log'
LOGGER_FILE_COLUMNS = [TIMESTAMP, LOG]

# ------------------------------------------------------------------------------------------------------------------- #
# public functions
# ------------------------------------------------------------------------------------------------------------------- #

# TODO The check for the logger file should not be done here - this public function should get already the logger file path
def load_logger_file_info(folder_path: str):

    # check if logger file exists in the folder and if it is not empty
    logger_filepath = _check_logger_file(folder_path)

    # if it exists load logger file info into a pandas dataframe
    if  logger_filepath is not None:

        # load raw logger file into dataframe
        logger_df = pd.read_csv(logger_filepath, sep='\t', header=None, skiprows=3, names=LOGGER_FILE_COLUMNS)

        # filter to get only the start times of the devices
        logger_df = _filter_logger_file(logger_df)


    else:
        print(
            f"No valid logger file found in folder: '{folder_path}'. "
            f"\nExpected a file starting with '{LOGGER_FILENAME_PREFIX}' that is not empty."
        )


# ------------------------------------------------------------------------------------------------------------------- #
# private functions
# ------------------------------------------------------------------------------------------------------------------- #


def _check_logger_file(folder_path: str) -> Optional[str]:
    """
    Checks if a logger file exists in the specified folder and that it is not empty.
    Assumes logger file name starts with 'opensignals_ACQUISITION_LOG_' and includes
    a timestamp.

    :param folder_path: The path to the folder containing the RAW acquisitions.
    :return: The full path to the logger file if it exists and is not empty, otherwise None.
    """
    # Pattern to match the logger file, assuming it starts with LOGGER_FILENAME_PREFIX
    pattern = os.path.join(folder_path, f'{LOGGER_FILENAME_PREFIX}*')

    # Use glob to find files that match the pattern
    matching_files = glob.glob(pattern)

    # iterate through the files that match the logger file prefix - should only be one
    for file_path in matching_files:

        # gets the first one (and only) that is not empty
        if os.path.getsize(file_path) > 0:
            return file_path

    return None


def _filter_logger_file(logger_df):

    # keep only the rows that have : "SENSOR_DATA: received first data from"
    logger_df = logger_df[logger_df[LOG].str.contains("SENSOR_DATA: received first data from")]

    # remove that specified text, keeping only the device name on th elogs column
    logger_df.loc[:, LOG] = logger_df[LOG].str.replace("SENSOR_DATA: received first data from", "",
                                                                 regex=False)

    return logger_df
"""
Functions for loading the meta-data contained in 'subjects_info.csv'.

Available Functions
-------------------
[Public]
load_meta_data(): loads the meta-data contained in subjects_info.csv into a pandas.DataFrame.

------------------
[Private]

"""

# ------------------------------------------------------------------------------------------------------------------- #
# imports
# ------------------------------------------------------------------------------------------------------------------- #
import pandas as pd


# ------------------------------------------------------------------------------------------------------------------- #
# public functions
# ------------------------------------------------------------------------------------------------------------------- #
def load_meta_data():
    """
    loads the meta-data contained in subjects_info.csv into a pandas.DataFrame.
    :return: DataFrame containing the meta-data
    """

    return pd.read_csv('subjects_info.csv', sep=';', encoding='utf-8', index_col='subject_id')


def get_muscleban_side(meta_data_df, mac_address):
    """
    Extracts the side of the muscleban from the meta_data_df based on the mac address of the device
    :param meta_data_df: pd.DataFrame containing the subject meta-data contained in subjects_info.csv
    :param mac_address: str containing the mac address without the colons
    :return: str containing the muscleban side
    """
    # Search in mBAN_left column
    if mac_address in meta_data_df['mBAN_left'].values:
        return 'mBAN_left'

    # Search in mBAN_right column
    elif mac_address in meta_data_df['mBAN_right'].values:
        return 'mBAN_right'

    # If not found
    return None


# ------------------------------------------------------------------------------------------------------------------- #
# imports
# ------------------------------------------------------------------------------------------------------------------- #
import load
import os
from visualize.visualize_acquisitions import visualize_daily_acquisitions, visualize_group_acquisitions

# ------------------------------------------------------------------------------------------------------------------- #
# constants
# ------------------------------------------------------------------------------------------------------------------- #
VISUALIZE_DAY = True
VISUALIZE_GROUP = False

GROUP_FOLDER_PATH = "D:\\Backup PrevOccupAI data\\jan2023\\data\\group4\\sensors"
SUBJECT_NUM = "LIBPhys #011"
DATE = "2022-07-21"
# ------------------------------------------------------------------------------------------------------------------- #
# program starts here
# ------------------------------------------------------------------------------------------------------------------- #

if __name__ == '__main__':

    # visualize the acquisitions of a single day
    if VISUALIZE_DAY:

        visualize_daily_acquisitions(os.path.join(GROUP_FOLDER_PATH, SUBJECT_NUM), DATE)

    # visualize all daily acquisitions from all subject of the group
    if VISUALIZE_GROUP:

        visualize_group_acquisitions(GROUP_FOLDER_PATH)

    # data_dict = load.load_data_from_same_recording(os.path.join(subject_folder_path, date, '14-40-00'))
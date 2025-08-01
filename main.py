import load
from utils import get_most_common_acquisition_times
from visualize.missing_data import get_missing_data
from visualize.visualize_acquisitions import visualize_daily_acquisitions, visualize_group_acquisitions, \
    _get_daily_acquisitions_metadata

if __name__ == '__main__':

    # group_folder_path = "D:\\Backup PrevOccupAI data\\jan2023\\data\\group2\\sensors"
    # visualize_group_acquisitions(group_folder_path)
    subject_folder_path = "D:\\Backup PrevOccupAI data\\jan2023\\data\\group2\\sensors\\LIBPhys #005"
    date = '2022-06-20'
    visualize_daily_acquisitions(subject_folder_path, date)

    # acquisitions_dict = _get_daily_acquisitions_metadata(subject_folder_path, date)
    #
    # missing_data_dict = get_missing_data(subject_folder_path, acquisitions_dict, 100, 300)
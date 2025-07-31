import load
from utils import get_most_common_acquisition_times
from visualize.visualize_acquisitions import visualize_daily_acquisitions, visualize_group_acquisitions

if __name__ == '__main__':

    # group_folder_path = "D:\\Backup PrevOccupAI data\\jan2023\\data\\group2\\sensors"
    # visualize_group_acquisitions(group_folder_path)
    subject_folder_path = "D:\\Backup PrevOccupAI data\\jan2023\\data\\group2\\sensors\\LIBPhys #006"
    date = '2022-06-20'
    visualize_daily_acquisitions(subject_folder_path, date)

    # dict_signals = load.load_data_from_same_recording("D:\\Backup PrevOccupAI data\\jan2023\\data\\group2\\sensors\\LIBPhys #004\\2022-06-22\\15-40-00")

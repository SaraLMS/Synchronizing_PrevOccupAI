from load.raw_signal_loader import load_data_from_same_recording
from load.logger_file_loader import load_logger_file_info
from visualize.visualize_acquisitions import visualize_daily_acquisitions

if __name__ == '__main__':

    folder_path = "D:\\Backup PrevOccupAI data\\jan2023\\data\\group2\\sensors\\LIBPhys #002\\2022-06-21"
    # dict_data = load_data_from_same_recording(folder_path)
    # start_times_dict = load_logger_file_info(folder_path)
    dict = visualize_daily_acquisitions(folder_path)
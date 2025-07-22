from load.raw_signal_loader import load_data_from_same_recording
from load.logger_file_loader import load_logger_file_info


if __name__ == '__main__':

    folder_path = "C:\\Users\\srale\\Desktop\\12-30-00"
    # dict_data = load_data_from_same_recording(folder_path)
    start_times_dict = load_logger_file_info(folder_path)
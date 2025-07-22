# ------------------------------------------------------------------------------------------------------------------- #
# Android devices constants
# ------------------------------------------------------------------------------------------------------------------- #

ANDROID = "ANDROID"
ANDROID_WEAR = "ANDROID_WEAR"

PHONE = "phone"
WATCH = "watch"

ACC_PREFIX = "ACCELEROMETER"
GYR_PREFIX = "GYROSCOPE"
MAG_PREFIX = "MAGNET"
HEART_PREFIX = "HEART_RATE"
ROT_PREFIX = "ROTATION_VECTOR"
NOISE_PREFIX = "NOISERECORDER"

ACC = "ACC"
GYR = "GYR"
MAG = "MAG"
HEART = "HR"
ROT = "ROT"
NOISE = "NOISE"


IMU_SENSORS = [ACC, GYR, MAG]


# the order of the sensors in these two lists must be the same
AVAILABLE_ANDROID_PREFIXES = [ACC_PREFIX, GYR_PREFIX, MAG_PREFIX, HEART_PREFIX, ROT_PREFIX, NOISE_PREFIX]
AVAILABLE_ANDROID_SENSORS = [ACC, GYR, MAG, HEART, ROT, NOISE]


# definition of time column
TIME_COLUMN_NAME = 't'

# ------------------------------------------------------------------------------------------------------------------- #
# MuscleBan constants
# ------------------------------------------------------------------------------------------------------------------- #

FS_MBAN = 1000
EMG = 'emg'
XACC = 'xACC'
YACC = 'yACC'
ZACC = 'zACC'
NSEQ = 'nSeq'

VALID_MBAN_DATA = [NSEQ, EMG, XACC, YACC, ZACC]


# %% If we just want to analyse one run...
from autogaita import autogaita_utils
import os

# ...............  1) folderinfo & cfg-dicts: constants  ......................
# folderinfo
ROOT_DIR = "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/Testing/"
SCTABLE_FILENAME = "25mm.xlsx"  # has to be an excel file
DATA_STRING = "SIMINewOct"
BEAM_STRING = "BeamTraining"
PREMOUSE_STRING = "Mouse"
POSTMOUSE_STRING = "_25mm"
PRERUN_STRING = "run"
POSTRUN_STRING = "-6DLC_resnet50"
# base cfg
SAMPLING_RATE = 100
SUBTRACT_BEAM = True
DONT_SHOW_PLOTS = False
CONVERT_TO_MM = True
PIXEL_TO_MM_RATIO = 3.76  # used for converting x & y data to millimeters
# advanced cfg
X_SC_BROKEN_THRESHOLD = 200  # reject SC if x/y goes +-value @ neighbouring tps
Y_SC_BROKEN_THRESHOLD = 50
X_ACCELERATION = True
ANGULAR_ACCELERATION = True
SAVE_TO_XLS = True
BIN_NUM = 25
PLOT_SE = True
NORMALISE_HEIGHT_AT_SC_LEVEL = True
INVERT_Y_AXIS = True
FLIP_GAIT_DIRECTION = True
PLOT_JOINT_NUMBER = 3
HIND_JOINTS = ["Hind paw tao", "Ankle", "Knee", "Hip", "Iliac Crest"]
FORE_JOINTS = [
        "Front paw tao ",
        "Wrist ",
        "Elbow ",
        "Lower Shoulder ",
        "Upper Shoulder ",
    ]
BEAM_HIND_JOINTADD = ["Tail base ", "Tail center ", "Tail tip "]
BEAM_FORE_JOINTADD = ["Nose ", "Ear base "]
ANGLES = {"name": ["Ankle", "Elbow"], "lower_joint": ["Hind paw tao", "Wrist"], "upper_joint": ["Knee", "Lower Shoulder"]}


# ......................  info-dict: mouse/run-constants  ..............................
info = {}
info["mouse_num"] = 18
info["run_num"] = 2
info["name"] = ("ID " + str(info["mouse_num"])
                + " - Run " + str(info["run_num"]))
info["results_dir"] = os.path.join(ROOT_DIR + "Results/" + info["name"] + "/")

# %% code
def dlc_singlerun():
    folderinfo = prepare_folderinfo()
    cfg = prepare_cfg()
    # run
    autogaita_utils.try_to_run_gaita("DLC", info, folderinfo, cfg, False)


def prepare_folderinfo():
    """ Dump all infos about this given folder into a dict """
    folderinfo = {}
    folderinfo["root_dir"] = ROOT_DIR
    # to make sure root_dir works under windows
    # (windows is okay with all dir-separators being "/", so make sure it is!)
    folderinfo["root_dir"] = folderinfo["root_dir"].replace(os.sep, "/")
    if folderinfo["root_dir"][-1] != "/":
        folderinfo["root_dir"] = folderinfo["root_dir"] + "/"
    folderinfo["sctable_filename"] = SCTABLE_FILENAME
    folderinfo["data_string"] = DATA_STRING
    folderinfo["beam_string"] = BEAM_STRING
    folderinfo["premouse_string"] = PREMOUSE_STRING
    folderinfo["postmouse_string"] = POSTMOUSE_STRING
    folderinfo["prerun_string"] = PRERUN_STRING
    folderinfo["postrun_string"] = POSTRUN_STRING
    return folderinfo


def prepare_cfg():
    """ Dump all configuration information into a dict """
    cfg = {}
    cfg["sampling_rate"] = SAMPLING_RATE  # base cfg
    cfg["subtract_beam"] = SUBTRACT_BEAM
    cfg["dont_show_plots"] = DONT_SHOW_PLOTS
    cfg["convert_to_mm"] = CONVERT_TO_MM
    cfg["pixel_to_mm_ratio"] = PIXEL_TO_MM_RATIO
    cfg["x_sc_broken_threshold"] = X_SC_BROKEN_THRESHOLD  # optional cfg
    cfg["y_sc_broken_threshold"] = Y_SC_BROKEN_THRESHOLD
    cfg["x_acceleration"] = X_ACCELERATION
    cfg["angular_acceleration"] = ANGULAR_ACCELERATION
    cfg["save_to_xls"] = SAVE_TO_XLS
    cfg["bin_num"] = BIN_NUM
    cfg["plot_SE"] = PLOT_SE
    cfg["normalise_height_at_SC_level"] = NORMALISE_HEIGHT_AT_SC_LEVEL
    cfg["plot_joint_number"] = PLOT_JOINT_NUMBER
    cfg["invert_y_axis"] = INVERT_Y_AXIS
    cfg["flip_gait_direction"] = FLIP_GAIT_DIRECTION
    cfg["hind_joints"] = HIND_JOINTS
    cfg["fore_joints"] = FORE_JOINTS
    cfg["beam_hind_jointadd"] = BEAM_HIND_JOINTADD
    cfg["beam_fore_jointadd"] = BEAM_FORE_JOINTADD
    cfg["angles"] = ANGLES
    return cfg

# %% what happens if we just hit run
if __name__ == "__main__":
    dlc_singlerun()
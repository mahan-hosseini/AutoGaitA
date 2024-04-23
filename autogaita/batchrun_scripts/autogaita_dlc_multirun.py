# %% Imports, constants & notes

# imports
from autogaita import autogaita_utils
import os
import pdb

# constants
# folderinfo
ROOT_DIR = "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/Testing/"
SCTABLE_FILENAME = "25mm.xlsx"  # has to be an excel file
DATA_STRING = "SIMINewOct"
BEAM_STRING = "BeamTraining"
PREMOUSE_STRING = "Mouse"
POSTMOUSE_STRING = "_25mm"
PRERUN_STRING = "run"
POSTRUN_STRING = "-6DLC"
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
NORMALISE_HEIGHT_AT_SC_LEVEL = False
INVERT_Y_AXIS = True
FLIP_GAIT_DIRECTION = True
PLOT_JOINT_NUMBER = 3
# column cfg
HIND_JOINTS = ["Hind paw tao", "Ankle", "Knee", "Hip", "Iliac Crest"]
FORE_JOINTS = [
    "Front paw tao ",
    "Wrist ",
    "Elbow ",
    "Lower Shoulder ",
    "Upper Shoulder ",
]
BEAM_COL_LEFT = ["BeamLeft"]  # BEAM_COL_LEFT & _RIGHT must be lists of len=1
BEAM_COL_RIGHT = ["BeamRight"]
BEAM_HIND_JOINTADD = ["Tail base ", "Tail center ", "Tail tip "]
BEAM_FORE_JOINTADD = ["Nose ", "Ear base "]
ANGLES = {
    "name": ["Ankle", "Elbow"],
    "lower_joint": ["Hind paw tao", "Wrist"],
    "upper_joint": ["Knee", "Lower Shoulder"],
}


# .....................  User note - please configure  ........................
# 1) ROOT_DIR: where are the files
# 2) SCTABLE_FILENAME: excel filename with manual step cycle annotations
# 3) DATA_STRING: what is the string that defines files to contain data
# 4) BEAM_STRING: what is the string that defines files to contain beam-coords
# 5) PREMOUSE_STRING: what is the string written immediately prior to mouse num
# 6) POSTMOUSE_STRING: what is the string written immediately after mouse num
# 8) PRERUN_STRING: what is the string written immediately prior to the run num
# 9) POSTRUN_STRING: what is the string written immediately after the run num


# %% main program
def dlc_multirun():
    info = extract_info()
    folderinfo = prepare_folderinfo()
    cfg = prepare_cfg()
    for idx in range(len(info["name"])):
        run_singlerun(idx, info, folderinfo, cfg)


# %% local functions


def run_singlerun(idx, info, folderinfo, cfg):
    """Run the main code of individual run-analyses based on current cfg"""
    # extract and pass info of this mouse/run (also update resdir)
    this_info = {}
    keynames = info.keys()
    for keyname in keynames:
        this_info[keyname] = info[keyname][idx]
    this_info["results_dir"] = os.path.join(
        folderinfo["root_dir"] + "Results/" + this_info["name"] + "/"
    )
    # important to only pass this_info to main script here (1 run at a time!)
    autogaita_utils.try_to_run_gaita("DLC", this_info, folderinfo, cfg, True)


def prepare_folderinfo():
    """Dump all infos about this given folder into a dict"""
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
    """Dump all configuration information into a dict"""
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
    cfg["beam_col_left"] = BEAM_COL_LEFT
    cfg["beam_col_right"] = BEAM_COL_RIGHT
    cfg["beam_hind_jointadd"] = BEAM_HIND_JOINTADD
    cfg["beam_fore_jointadd"] = BEAM_FORE_JOINTADD
    cfg["angles"] = ANGLES
    return cfg


def extract_info():
    """Prepare a dict of lists that include unique name/mouse/run infos"""
    info = {"name": [], "mouse_num": [], "run_num": []}
    for filename in os.listdir(ROOT_DIR):
        if (
            (PREMOUSE_STRING in filename)  # make sure we don't get wrong files
            & (PRERUN_STRING in filename)
            & (filename.endswith(".csv"))
        ):
            # we can use COUNT vars as we do here, since we start @ 0 and do
            # not include the last index (so if counts=2, idx=[0:2]=include
            # 0&1 only!)
            this_mouse_num = find_number(filename, PREMOUSE_STRING, POSTMOUSE_STRING)
            this_run_num = find_number(filename, PRERUN_STRING, POSTRUN_STRING)
            this_name = "ID " + str(this_mouse_num) + " - Run " + str(this_run_num)
            if this_name not in info["name"]:  # no data/beam duplicates here
                info["name"].append(this_name)
                info["mouse_num"].append(this_mouse_num)
                info["run_num"].append(this_run_num)
    return info


def find_number(fullstring, prestring, poststring):
    """Find (mouse/run) number based on user-defined strings in filenames"""
    start_idx = fullstring.find(prestring) + len(prestring)
    end_idx = fullstring.find(poststring)
    return int(fullstring[start_idx:end_idx])


# %% what happens if we just hit run
if __name__ == "__main__":
    dlc_multirun()

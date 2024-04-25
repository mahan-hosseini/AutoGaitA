from autogaita import autogaita_utils
import pandas as pd
import pandas.testing as pdt
import os
import shutil
import pdb

# .............................  1) GLOBAL VARS  .......................................
# for testing - reset any previous test
TEST_PATH = "tests/test_data/dlc_data/"
TRUE_PATH = "example data/25mm/Results/ID 15 - Run 3/"
if os.path.exists(os.path.join(TEST_PATH, "Results")):
    shutil.rmtree(os.path.join(TEST_PATH, "Results"))
# batchrun_script global vars
# folderinfo
ROOT_DIR = TEST_PATH
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
DONT_SHOW_PLOTS = True
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
    "name": ["Ankle ", "Knee ", "Hip "],
    "lower_joint": ["Hind paw tao ", "Ankle ", "Knee "],
    "upper_joint": ["Knee ", "Hip ", "Iliac Crest "],
}
info = {}
info["mouse_num"] = 15
info["run_num"] = 3
info["name"] = "ID " + str(info["mouse_num"]) + " - Run " + str(info["run_num"])
info["results_dir"] = os.path.join(ROOT_DIR + "Results/" + info["name"] + "/")


# ...............................  2) RUN TEST  ........................................
def test_dlc_approval():
    """
    Approval Test of AutoGaitA DLC
    ------------------------------
    1. Run autogaita.dlc for ID 15 - Run 3 (with the cfg used there)
    2. Load the "Average Stepcycles".xlsx file from the repo and compare for equivalence to  average_data
    3. Do the same for "Standard Devs. Stepcycle.xlsx" and std_data
    4. Pass the test if the two df-pairs are equal
    """
    folderinfo = prepare_folderinfo()
    cfg = prepare_cfg()
    # run
    autogaita_utils.try_to_run_gaita("DLC", info, folderinfo, cfg, False)
    # load true dfs from xlsx files
    true_av_df = pd.read_excel(
        os.path.join(TRUE_PATH, "ID 15 - Run 3 - Average Stepcycle.xlsx")
    )
    true_std_df = pd.read_excel(
        os.path.join(TRUE_PATH, "ID 15 - Run 3 - Standard Devs. Stepcycle.xlsx")
    )
    test_av_df = pd.read_excel(
        os.path.join(
            TEST_PATH, "Results/ID 15 - Run 3/ID 15 - Run 3 - Average Stepcycle.xlsx"
        )
    )
    test_std_df = pd.read_excel(
        os.path.join(
            TEST_PATH,
            "Results/ID 15 - Run 3/ID 15 - Run 3 - Standard Devs. Stepcycle.xlsx",
        )
    )
    # finally assert equivalence of df-pairs
    pdt.assert_frame_equal(test_av_df, true_av_df)
    pdt.assert_frame_equal(test_std_df, true_std_df)


# ..............................  3) LOCAL FUNCTIONS  ..................................
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

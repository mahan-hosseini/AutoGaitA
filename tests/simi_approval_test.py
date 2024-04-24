from autogaita import autogaita_utils
import pandas as pd
import pandas.testing as pdt
import os
import shutil
import pdb

# .................................................  1) GLOBAL VARS  .........................................................
# for testing - reset any previous test
TEST_PATH = "tests/test_data/simi_data/test_data/"
TRUE_PATH = "tests/test_data/simi_data/true_data/"
if os.path.exists(os.path.join(TEST_PATH, "Results")):
    shutil.rmtree(os.path.join(TEST_PATH, "Results"))
# batchrun_script global vars
# folderinfo
ROOT_DIR = TEST_PATH
SCTABLE_FILENAME = "SC Latency Table"  # has to be an excel file
POSTNAME_FLAG = False
POSTNAME_STRING = ""
# base cfg
SAMPLING_RATE = 100
DONT_SHOW_PLOTS = True
# advanced cfg
Y_ACCELERATION = True
ANGULAR_ACCELERATION = True
BIN_NUM = 25
PLOT_SE = True
NORMALISE_HEIGHT_AT_SC_LEVEL = True
PLOT_JOINT_NUMBER = 7
# column cfg
JOINTS = ["Midfoot", "Ankle", "Knee", "Hip", "Pelvis "]
ANGLES = {
    "name": ["Ankle", "Knee", "Hip"],
    "lower_joint": ["Midfoot", "Ankle", "Knee"],
    "upper_joint": ["Knee", "Hip", "Pelvis "],
}
info = {}
info["name"] = "O_09"
info["results_dir"] = os.path.join(ROOT_DIR + "Results/" + info["name"] + "/")


# ....................................................  2) RUN TEST  .......................................................
def test_simi_approval():
    """
    Approval Test of AutoGaitA DLC
    1. Run autogaita.dlc for ID 15 - Run 3 (with the cfg used there)
    2. Load the "Average Stepcycles".xlsx file from the repo and compare for equivalence to  average_data
    3. Do the same for "Standard Devs. Stepcycle.xlsx" and std_data
    4. Pass the test if the two df-pairs are equal
    """
    folderinfo = prepare_folderinfo()
    cfg = prepare_cfg()
    # run
    autogaita_utils.try_to_run_gaita("Simi", info, folderinfo, cfg, False)
    # load true dfs from xlsx files
    true_av_df = pd.read_excel(os.path.join(TRUE_PATH, "O_09 - Average Stepcycle.xlsx"))
    true_std_df = pd.read_excel(
        os.path.join(TRUE_PATH, "O_09 - Standard Devs. Stepcycle.xlsx")
    )
    test_av_df = pd.read_excel(
        os.path.join(TEST_PATH, "Results/O_09/O_09 - Average Stepcycle.xlsx")
    )
    test_std_df = pd.read_excel(
        os.path.join(
            TEST_PATH,
            "Results/O_09/O_09 - Standard Devs. Stepcycle.xlsx",
        )
    )
    # finally assert equivalence of df-pairs
    pdt.assert_frame_equal(test_av_df, true_av_df)
    pdt.assert_frame_equal(test_std_df, true_std_df)


# ..................................................  3) LOCAL FUNCTIONS  ....................................................
def prepare_folderinfo():
    """Dump all infos about constants in this given folder into a dict"""
    folderinfo = {}
    folderinfo["root_dir"] = ROOT_DIR
    folderinfo["sctable_filename"] = SCTABLE_FILENAME
    folderinfo["postname_string"] = POSTNAME_STRING
    return folderinfo


def prepare_cfg():
    """Dump all configuration information into a dict"""
    cfg = {}
    cfg["sampling_rate"] = SAMPLING_RATE  # base cfg
    cfg["dont_show_plots"] = DONT_SHOW_PLOTS
    cfg["y_acceleration"] = Y_ACCELERATION
    cfg["angular_acceleration"] = ANGULAR_ACCELERATION
    cfg["bin_num"] = BIN_NUM
    cfg["plot_SE"] = PLOT_SE
    cfg["normalise_height_at_SC_level"] = NORMALISE_HEIGHT_AT_SC_LEVEL
    cfg["plot_joint_number"] = PLOT_JOINT_NUMBER
    cfg["joints"] = JOINTS
    cfg["angles"] = ANGLES
    return cfg

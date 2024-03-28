# %% If we just want to analyse one run...
from autogaita import autogaita_utils
import os
import traceback

# .............  1) folderinfo-dict: the folder-constants  ....................
# constants
ROOT_DIR = "/Users/mahan/sciebo/Research/AutoGaitA/Human/Testing2/"
SCTABLE_FILENAME = "SC Latency Table"  # has to be an xlsxfile
POSTNAME_FLAG = False
if POSTNAME_FLAG is False:
    POSTNAME_STRING = ""
else:
    POSTNAME_STRING = "_joint_centers"

# .................  2) cfg-dict: analysis-config  .......................
# base cfg
SAMPLING_RATE = 100
DONT_SHOW_PLOTS = False
# advanced cfg
Y_ACCELERATION = True
ANGULAR_ACCELERATION = True
BIN_NUM = 25
PLOT_SE = True
NORMALISE_HEIGHT_AT_SC_LEVEL = True
PLOT_JOINT_NUMBER = 7
JOINTS = ["Ankle", "Knee", "Hip", "Pelvis", "Shoulder", "Neck"]
ANGLES = {"name": ["Ankle", "Knee", "Elbow", "Skullbase"],
          "lower_joint": ["Midfoot", "Ankle", "Wrist", "Neck"],
          "upper_joint": ["Knee", "Hip", "Shoulder", "Skull"]}

# .................  3) info-dict: ID-constants  .......................
info = {}
info["name"] = "SK"  # analyse this dataset
info["results_dir"] = os.path.join(ROOT_DIR + "Results/" + info["name"] + "/")


# %% code
def simi_singlerun():
    folderinfo = prepare_folderinfo()
    cfg = prepare_cfg()
    # run
    autogaita_utils.try_to_run_gaita("Simi", info, folderinfo, cfg, False)


def prepare_folderinfo():
    """ Dump all infos about constants in this given folder into a dict """
    folderinfo = {}
    folderinfo["root_dir"] = ROOT_DIR
    folderinfo["sctable_filename"] = SCTABLE_FILENAME
    folderinfo["postname_string"] = POSTNAME_STRING
    return folderinfo


def prepare_cfg():
    """ Dump all configuration information into a dict """
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

# %% what happens if we just hit run
if __name__ == "__main__":
    simi_singlerun()
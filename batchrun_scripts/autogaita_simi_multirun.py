# %% Imports, constants & notes

# imports
from autogaita import autogaita_utils
import os
import pdb

# .............  1) folderinfo-dict: the folder-constants  ....................
# constants
ROOT_DIR = "/Users/mahan/sciebo/Research/AutoGaitA/Human/Testing2/"
if ROOT_DIR:
    if ROOT_DIR[-1] != "/":
        ROOT_DIR += "/"
SCTABLE_FILENAME = "SC Latency Table"  # has to be an xlsxfile
POSTNAME_FLAG = False
if POSTNAME_FLAG is False:
    POSTNAME_STRING = ""
else:
    POSTNAME_STRING = "_joint_centers"

# .................  2) cfg-dict: analysis-config  .......................
# base cfg
SAMPLING_RATE = 100
DONT_SHOW_PLOTS = True
# advanced cfg
Y_ACCELERATION = True
ANGULAR_ACCELERATION = True
BIN_NUM = 25
PLOT_SE = False
NORMALISE_HEIGHT_AT_SC_LEVEL = True
PLOT_JOINT_NUMBER = 7
JOINTS = ["Midfoot", "Ankle", "Knee", "Hip", "Pelvis", "Shoulder", "Neck"]
ANGLES = {"name": ["WHO", "Ankle", "Knee", "Elbow", "Skullbase"],
          "lower_joint": ["Midfoot", "IS", "Ankle", "Wrist", "Neck"],
          "upper_joint": ["Knee", "Hip", "Shoulder", "Skull"]}


# %% main program


def simi_multirun():
    info = extract_info()
    folderinfo = prepare_folderinfo()
    cfg = prepare_cfg()
    for idx, name in enumerate(info["name"]):
        run_singlerun(idx, info, folderinfo, cfg)


# %% local functions


def run_singlerun(idx, info, folderinfo, cfg):
    """ Run the main code of individual run-analyses based on current cfg """
    # extract and pass info of this mouse/run (also update resdir)
    this_info = {}
    keynames = info.keys()
    for keyname in keynames:
        this_info[keyname] = info[keyname][idx]
    # important to only pass this_info to main script here (1 run at a time!)
    autogaita_utils.try_to_run_gaita("Simi", this_info, folderinfo, cfg, True)


def extract_info():
    """ Prepare a dict of lists that include unique name infos"""
    info = {"name": [], "results_dir":[]}
    for filename in os.listdir(ROOT_DIR):
        if not POSTNAME_STRING:
            if (".xls" in filename) & (SCTABLE_FILENAME not in filename):
                info["name"].append(filename.split(".xls")[0])
                info["results_dir"].append(
                    os.path.join(ROOT_DIR + "Results/" + info["name"][-1] + "/")
                    )
        else:
            if POSTNAME_STRING in filename:
                info["name"].append(filename.split(POSTNAME_STRING)[0])
                info["results_dir"].append(
                    os.path.join(ROOT_DIR + "Results/" + info["name"][-1] + "/")
                    )
    return info


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
    simi_multirun()

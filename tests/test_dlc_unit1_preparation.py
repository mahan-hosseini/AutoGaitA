from autogaita.autogaita_dlc import some_prep
from hypothesis import given
import hypothesis.strategies as st
import os
import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest
import pdb


# %%................................  fixtures  ........................................
@pytest.fixture
def extract_data_using_some_prep(extract_info, extract_folderinfo, extract_cfg):
    data = some_prep(extract_info, extract_folderinfo, extract_cfg)
    return data


@pytest.fixture
def extract_info(tmp_path):
    info = {}
    info["mouse_num"] = 15
    info["run_num"] = 3
    info["name"] = "ID " + str(info["mouse_num"]) + " - Run " + str(info["run_num"])
    info["results_dir"] = os.path.join(tmp_path, info["name"])
    return info


@pytest.fixture
def extract_folderinfo():
    folderinfo = {}
    folderinfo["root_dir"] = "tests/test_data/dlc_data"
    folderinfo["sctable_filename"] = "25mm.xlsx"  # has to be an excel file
    folderinfo["data_string"] = "SIMINewOct"
    folderinfo["beam_string"] = "BeamTraining"
    folderinfo["premouse_string"] = "Mouse"
    folderinfo["postmouse_string"] = "_25mm"
    folderinfo["prerun_string"] = "run"
    folderinfo["postrun_string"] = "-6DLC"
    return folderinfo


@pytest.fixture
def extract_cfg():
    cfg = {}
    cfg["sampling_rate"] = 100
    cfg["subtract_beam"] = True
    cfg["dont_show_plots"] = True
    cfg["convert_to_mm"] = True
    cfg["pixel_to_mm_ratio"] = 3.76
    cfg["x_sc_broken_threshold"] = 200  # optional cfg
    cfg["y_sc_broken_threshold"] = 50
    cfg["x_acceleration"] = True
    cfg["angular_acceleration"] = True
    cfg["save_to_xls"] = True
    cfg["bin_num"] = 25
    cfg["plot_SE"] = True
    cfg["normalise_height_at_SC_level"] = False
    cfg["plot_joint_number"] = 3
    cfg["invert_y_axis"] = True
    cfg["flip_gait_direction"] = True
    cfg["hind_joints"] = ["Hind paw tao", "Ankle", "Knee", "Hip", "Iliac Crest"]
    cfg["fore_joints"] = [
        "Front paw tao ",
        "Wrist ",
        "Elbow ",
        "Lower Shoulder ",
        "Upper Shoulder ",
    ]
    cfg["beam_col_left"] = ["BeamLeft"]  # BEAM_COL_LEFT & _RIGHT must be lists of len=1
    cfg["beam_col_right"] = ["BeamRight"]
    cfg["beam_hind_jointadd"] = ["Tail base ", "Tail center ", "Tail tip "]
    cfg["beam_fore_jointadd"] = ["Nose ", "Ear base "]
    cfg["angles"] = {
        "name": ["Ankle ", "Knee ", "Hip "],
        "lower_joint": ["Hind paw tao ", "Ankle ", "Knee "],
        "upper_joint": ["Knee ", "Hip ", "Iliac Crest "],
    }
    return cfg


# %%..............................  preparation  ...................................

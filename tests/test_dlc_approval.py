from autogaita import autogaita_utils
import pandas as pd
import pandas.testing as pdt
import os
import shutil
import pdb
import pytest


# ............................  DLC APPROVAL TESTS STRUCTURE  ..........................
# 1. Run 4 pytest fixtures in preparation
# 2. Run autogaita.dlc for ID 15 - Run 3 (with the cfg used there)
# 3. Load the "Average Stepcycles".xlsx file from the repo and compare for
#    equivalence to average_data
# 4. Do the same for "Standard Devs. Stepcycle.xlsx" and std_data
# 5. Pass the test if the two df-pairs are equal


# ...............................  PREPARE - FOUR FIXTURES   ...........................


@pytest.fixture
def extract_true_dir():
    return "tests/test_data/dlc_data/true_data/"


@pytest.fixture
def extract_info(tmp_path):
    info = {}
    info["mouse_num"] = 12
    info["run_num"] = 3
    info["name"] = "ID " + str(info["mouse_num"]) + " - Run " + str(info["run_num"])
    info["results_dir"] = os.path.join(tmp_path, info["name"])
    return info


@pytest.fixture
def extract_folderinfo():
    folderinfo = {}
    folderinfo["root_dir"] = "tests/test_data/dlc_data/test_data/"
    folderinfo["sctable_filename"] = "correct_annotation_table.xlsx"
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
    cfg["normalise_height_at_SC_level"] = True
    cfg["plot_joint_number"] = 3
    cfg["invert_y_axis"] = True
    cfg["flip_gait_direction"] = True
    cfg["export_average_x"] = True
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


# ..............................  RUN - TWO APPROVAL TESTS  ............................
# A Note
# ------
# In group and simi approval tests we only have 1 test. Here we have 2 tests since Nick
# used this to teach the concept of fixtures and how multiple tests can use the same
# fixture to have the same testing environment. I decided against using multiple
# approval tests in the other two scripts since for those a given run of autogaita
# takes much longer and would unnecessarily increase computation times..
# For autogaita_dlc this is negligible since it runs that much faster in general


@pytest.mark.slow
def test_dlc_approval_average_df(
    extract_true_dir, extract_info, extract_folderinfo, extract_cfg
):
    autogaita_utils.try_to_run_gaita(
        "DLC", extract_info, extract_folderinfo, extract_cfg, False
    )
    true_av_df = pd.read_excel(
        os.path.join(extract_true_dir, "ID 12 - Run 3 - Average Stepcycle.xlsx")
    )
    test_av_df = pd.read_excel(
        os.path.join(
            extract_info["results_dir"],
            "ID 12 - Run 3 - Average Stepcycle.xlsx",
        )
    )
    pdt.assert_frame_equal(test_av_df, true_av_df)


@pytest.mark.slow
def test_dlc_approval_std_df(
    extract_true_dir, extract_info, extract_folderinfo, extract_cfg
):
    autogaita_utils.try_to_run_gaita(
        "DLC", extract_info, extract_folderinfo, extract_cfg, False
    )
    true_std_df = pd.read_excel(
        os.path.join(extract_true_dir, "ID 12 - Run 3 - Standard Devs. Stepcycle.xlsx")
    )
    test_std_df = pd.read_excel(
        os.path.join(
            extract_info["results_dir"],
            "ID 12 - Run 3 - Standard Devs. Stepcycle.xlsx",
        )
    )
    pdt.assert_frame_equal(test_std_df, true_std_df)

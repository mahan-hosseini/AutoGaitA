from autogaita.autogaita_dlc import some_prep
from autogaita.autogaita_dlc import (
    move_data_to_folders, check_and_expand_cfg, check_and_fix_cfg_strings, flip_mouse_body, check_gait_direction
    )
from hypothesis import given, strategies as st, settings, HealthCheck
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
    cfg["export_average_x"] = False
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


# %%..............................  preparation  .......................................
#                       AN IMPORTANT NOTE ON THESE UNIT TESTS!
# Calling check_and_expand cfg outside of some_prep with the 
# export_data_using_some_prep fixture leads to the cfg that is returned by 
# check_and_expand to be None since the data var DOES NOT INCLUDE the beam!
# => We thus set cfg["subtract_beam"] to False prior to calling it (see e.g.the
#    plot_joint test)

def test_wrong_data_and_beam_strings(extract_info, extract_folderinfo, extract_cfg):
    extract_folderinfo["beam_string"] = extract_folderinfo["data_string"]
    some_prep(extract_info, extract_folderinfo, extract_cfg)
    with open(os.path.join(extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert "Your data & baseline (beam) identifiers ([G] in our" in content
    

def test_wrong_postmouse_string(extract_info, extract_folderinfo, extract_cfg):
    extract_folderinfo["postmouse_string"] = "this_is_a_test"
    some_prep(extract_info, extract_folderinfo, extract_cfg)
    with open(os.path.join(extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert "Unable to identify ANY RELEVANT FILES for" in content


def test_global_min_normalisation(extract_info, extract_folderinfo, extract_cfg):
    extract_cfg["subtract_beam"] = False
    data = some_prep(extract_info, extract_folderinfo, extract_cfg)
    y_cols = [c for c in data.columns if c.endswith(" y")]
    assert data[y_cols].min().min() == 0


def test_datas_indexing_and_time_column(extract_info, extract_folderinfo, extract_cfg):
    for extract_cfg["sampling_rate"] in [50, 500, 5000]:
        data = some_prep(extract_info, extract_folderinfo, extract_cfg)
        assert data["Time"].max() == ((len(data)-1) / (1 * extract_cfg["sampling_rate"]))


def test_cols_we_added_to_data(extract_info, extract_folderinfo, extract_cfg):
    data = some_prep(extract_info, extract_folderinfo, extract_cfg)
    assert (data.columns[0] == "Time") & (data.columns[1] == "Flipped")


def test_move_csv_datafile_to_results_dir(extract_info, extract_folderinfo):
    move_data_to_folders(extract_info, extract_folderinfo)
    for file in os.listdir(extract_info["results_dir"]):
        if file.endswith(".csv"):
            assert ((extract_folderinfo["premouse_string"] in file) 
                    & (extract_folderinfo["postmouse_string"] in file)
                    & (extract_folderinfo["prerun_string"] in file)
                    & (extract_folderinfo["postrun_string"] in file))


def test_error_if_no_hindlimb_joints(extract_info, extract_folderinfo, extract_cfg):
    extract_cfg["hind_joints"] = ["not_in_data"]
    data = some_prep(extract_info, extract_folderinfo, extract_cfg)
    assert data is None


def test_plot_joint_error(extract_data_using_some_prep, extract_cfg, extract_info):
    extract_cfg["plot_joint_number"] = 2000
    extract_cfg["subtract_beam"] = False
    check_and_expand_cfg(extract_data_using_some_prep, extract_cfg, extract_info)
    with open(os.path.join(extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert "we can :)" in content
    extract_cfg = check_and_expand_cfg(
        extract_data_using_some_prep, extract_cfg, extract_info
        )
    assert extract_cfg["plot_joints"] == extract_cfg["hind_joints"]
    extract_cfg["plot_joint_number"] = 2
    extract_cfg = check_and_expand_cfg(
        extract_data_using_some_prep, extract_cfg, extract_info
        )
    assert extract_cfg["plot_joints"] == extract_cfg["hind_joints"][:2]


@given(test_list=st.lists(st.text(), min_size=1))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_removal_of_wrong_strings_from_cfg_key(test_list, extract_data_using_some_prep, extract_cfg, extract_info):
    cfg_key = "hind_joints"  # irrelevant since property testing
    extract_cfg[cfg_key] = test_list
    test_result = check_and_fix_cfg_strings(extract_data_using_some_prep, extract_cfg, cfg_key, extract_info)
    assert not test_result  # empty list is falsey


def test_flip_mouse_body(extract_info, extract_folderinfo, extract_cfg):
    extract_cfg["flip_gait_direction"] = False
    test_data = some_prep(extract_info, extract_folderinfo, extract_cfg)
    print("data:")
    print(test_data)
    # flipped_data = extract_data_using_some_prep
    test_flipped_data = test_data.copy()
    print("flipped_data pre flipping:")
    print(test_flipped_data)
    test_flipped_data = flip_mouse_body(test_data, extract_info)
    # flipped_data = data.copy()
    # test_data = data.copy()
    print("flipped_data post flipping:")
    print(test_flipped_data)
    for col in test_flipped_data.columns:
        if col.endswith("x"):
            flipped_test_series = test_flipped_data[col]
            print(f"Processing column: {col}")
            print("flipped_test_series:")
            print(flipped_test_series)
            # pytest.set_trace()
            test_series = max(
                test_data.loc[:, col]) - test_data.loc[:, col]
            print("test_series:")
            print(test_series)
            flipped_test_series = flipped_test_series.astype(float)
            print("flipped_test_series after conversion:")
            print(flipped_test_series)
            pdt.assert_series_equal(test_series, flipped_test_series)


def test_check_gait_direction(extract_data_using_some_prep, extract_cfg, extract_info):
    direction_joint = extract_cfg["direction_joint"]
    flip_gait_direction = True  # 1) test broken DLC data (empty)
    broken_data = pd.DataFrame(data=None, columns=extract_data_using_some_prep.columns)
    check_gait_direction(broken_data, direction_joint, flip_gait_direction, extract_info)
    with open(os.path.join(extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert "Unable to determine gait direction!" in content
    flip_this_data = pd.DataFrame(
        data=None, columns=extract_data_using_some_prep.columns
        )  # 2) test data that has to be flipped
    data_len = 20
    flip_this_data[direction_joint + "likelihood"] = [0.99] * data_len
    first_half = [10] * int((data_len / 2))
    second_half = [-10] * int((data_len / 2))
    x_coords = first_half + second_half
    flip_this_data[direction_joint + "x"] = x_coords
    flip_this_data = check_gait_direction(
        flip_this_data, direction_joint, flip_gait_direction, extract_info
        )
    assert flip_this_data["Flipped"][0] == True

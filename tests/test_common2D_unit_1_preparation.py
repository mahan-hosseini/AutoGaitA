from autogaita.common2D.common2D_1_preparation import (
    move_data_to_folders,
    check_and_expand_cfg,
    check_and_fix_cfg_strings,
    flip_mouse_body,
    some_prep,  # note that first input of some_prep is set to "DLC" when not mattering!
)
from autogaita.common2D.common2D_utils import extract_info
import os
import copy
import math
import numpy as np
import pandas.testing as pdt
from hypothesis import given, strategies as st, settings, HealthCheck
import pytest


# %%..............................  fixtures  ..........................................
# NOTE
# ----
# Calling them FIXTURE_extract_... since we have a function called extract_info!


@pytest.fixture
def extract_data_using_some_prep(
    fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
):
    data = some_prep(
        "DLC", fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
    )
    return data


@pytest.fixture
def fixture_extract_info(tmp_path):
    info = {}
    info["mouse_num"] = 15
    info["run_num"] = 3
    info["name"] = "ID " + str(info["mouse_num"]) + " - Run " + str(info["run_num"])
    info["results_dir"] = os.path.join(tmp_path, info["name"])
    return info


@pytest.fixture
def fixture_extract_folderinfo():
    folderinfo = {}
    folderinfo["root_dir"] = "tests/test_data/dlc_data"
    folderinfo["sctable_filename"] = (
        "correct_annotation_table.xlsx"  # has to be an excel file
    )
    folderinfo["data_string"] = "SIMINewOct"
    folderinfo["beam_string"] = "BeamTraining"
    folderinfo["premouse_string"] = "Mouse"
    folderinfo["postmouse_string"] = "25mm"
    folderinfo["prerun_string"] = "run"
    folderinfo["postrun_string"] = "6DLC"
    return folderinfo


@pytest.fixture
def fixture_extract_cfg():
    cfg = {}
    cfg["sampling_rate"] = 100
    cfg["subtract_beam"] = True
    cfg["dont_show_plots"] = True
    cfg["convert_to_mm"] = True
    cfg["pixel_to_mm_ratio"] = 3.76
    cfg["x_sc_broken_threshold"] = 200
    cfg["y_sc_broken_threshold"] = 50
    cfg["x_acceleration"] = True
    cfg["angular_acceleration"] = True
    cfg["save_to_xls"] = True
    cfg["bin_num"] = 25
    cfg["plot_SE"] = True
    cfg["standardise_y_at_SC_level"] = False
    cfg["standardise_y_to_a_joint"] = True
    cfg["y_standardisation_joint"] = ["Knee"]
    cfg["plot_joint_number"] = 3
    cfg["color_palette"] = "viridis"
    cfg["legend_outside"] = True
    cfg["invert_y_axis"] = True
    cfg["flip_gait_direction"] = True
    cfg["analyse_average_x"] = True
    cfg["standardise_x_coordinates"] = True
    cfg["x_standardisation_joint"] = ["Hind paw tao"]
    cfg["coordinate_standardisation_xls"] = ""
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


def test_move_data_to_folders_smoke_normal(
    fixture_extract_info, fixture_extract_folderinfo
):
    move_data_to_folders(
        "DLC", ".csv", fixture_extract_info, fixture_extract_folderinfo
    )
    assert len(os.listdir(fixture_extract_info["results_dir"])) == 3
    for file in os.listdir(fixture_extract_info["results_dir"]):
        if file.endswith(".csv"):
            assert (
                (fixture_extract_folderinfo["premouse_string"] in file)
                & (fixture_extract_folderinfo["postmouse_string"] in file)
                & (fixture_extract_folderinfo["prerun_string"] in file)
                & (fixture_extract_folderinfo["postrun_string"] in file)
            )


def test_move_data_to_folders_leading_zeros_handled(
    tmp_path, fixture_extract_folderinfo
):
    # ensure files with leading zeros are moved too
    # => this needs some preparation because I want to test extract_info, too, which is
    #    required to output lists in each of its keys because I use it in multiruns to
    #    iterate over each idxs which consistute separate runs
    fixture_extract_folderinfo["root_dir"] = (
        "tests/test_data/dlc_data/test_data/leading_zeros/"
    )
    # CARE! function: extract_info for info where we handle leading zeros
    info = extract_info("DLC", fixture_extract_folderinfo)
    for idx in range(len(info["name"])):
        this_info = {}
        # forloop below is borrowed from run_singlerun_in_multirun function
        for keyname in info.keys():
            if "leading_" in keyname:
                if info[keyname][idx] is not False:
                    this_info[keyname] = info[keyname][idx]
            else:  # pass as is for all other keys
                this_info[keyname] = info[keyname][idx]
    this_info["results_dir"] = tmp_path
    # move_data... creates it, make sure it's not there
    if os.path.exists(this_info["results_dir"]):
        for file in os.listdir(this_info["results_dir"]):
            os.remove(os.path.join(this_info["results_dir"], file))
        os.rmdir(this_info["results_dir"])
    # run with this_info
    move_data_to_folders("DLC", ".csv", this_info, fixture_extract_folderinfo)
    assert len(os.listdir(this_info["results_dir"])) == 2


# %%..........................  cfg & string stuff  ....................................
def test_plot_joint_error(
    extract_data_using_some_prep, fixture_extract_cfg, fixture_extract_info
):
    fixture_extract_cfg["plot_joint_number"] = 2000
    fixture_extract_cfg["subtract_beam"] = False
    check_and_expand_cfg(
        extract_data_using_some_prep, fixture_extract_cfg, fixture_extract_info
    )
    with open(os.path.join(fixture_extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert "we can :)" in content
    fixture_extract_cfg = check_and_expand_cfg(
        extract_data_using_some_prep, fixture_extract_cfg, fixture_extract_info
    )
    assert fixture_extract_cfg["plot_joints"] == fixture_extract_cfg["hind_joints"]
    fixture_extract_cfg["plot_joint_number"] = 2
    fixture_extract_cfg = check_and_expand_cfg(
        extract_data_using_some_prep, fixture_extract_cfg, fixture_extract_info
    )
    assert fixture_extract_cfg["plot_joints"] == fixture_extract_cfg["hind_joints"][:2]


def test_error_if_no_cfgkey_joints(
    fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
):
    full_cfg = copy.deepcopy(
        fixture_extract_cfg
    )  # no referencing here - we need copies!
    for cfg_key in [
        "hind_joints",
        "x_standardisation_joint",
        "y_standardisation_joint",
    ]:
        fixture_extract_cfg = copy.deepcopy(full_cfg)  # here too!
        fixture_extract_cfg[cfg_key] = ["not_in_data"]
        data = some_prep(
            "DLC", fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
        )
        with open(os.path.join(fixture_extract_info["results_dir"], "Issues.txt")) as f:
            content = f.read()
        if cfg_key == "hind_joints":
            assert "hind limb joint names" in content
        elif cfg_key == "x_standardisation_joint":
            assert "x-coordinate standardisation joint" in content
        elif cfg_key == "y_standardisation_joint":
            assert "y-coordinate standardisation joint" in content
        assert data is None
    # cannot loop case of x & y joints being broken
    fixture_extract_cfg = copy.deepcopy(full_cfg)
    fixture_extract_cfg["x_standardisation_joint"] = ["not_in_data"]
    fixture_extract_cfg["y_standardisation_joint"] = ["not_in_data"]
    data = some_prep(
        "DLC", fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
    )
    with open(os.path.join(fixture_extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
        assert "x & y-coordinate standardisation joint" in content
        assert data is None


@given(test_list=st.lists(st.text(), min_size=1))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_removal_of_wrong_strings_from_cfg_key(
    test_list, extract_data_using_some_prep, fixture_extract_cfg, fixture_extract_info
):
    # the following loop is to account for hypothesis randomly generating strings that
    # actually are data columns (happend for "Knee ")
    for i in range(len(test_list)):
        if test_list[i] + "x" in extract_data_using_some_prep.columns:
            test_list.pop(i)
    cfg_key = "hind_joints"  # irrelevant since property testing
    fixture_extract_cfg[cfg_key] = test_list
    test_result = check_and_fix_cfg_strings(
        extract_data_using_some_prep, fixture_extract_cfg, cfg_key, fixture_extract_info
    )
    assert not test_result  # empty list is falsey


def test_wrong_data_and_beam_strings(
    fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
):
    fixture_extract_folderinfo["beam_string"] = fixture_extract_folderinfo[
        "data_string"
    ]
    some_prep(
        "DLC", fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
    )
    with open(os.path.join(fixture_extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert "Your data & baseline (beam) identifiers ([G] in our" in content


def test_wrong_postmouse_string(
    fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
):
    fixture_extract_folderinfo["postmouse_string"] = "this_is_a_test"
    some_prep(
        "DLC", fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
    )
    with open(os.path.join(fixture_extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert "Unable to identify ANY RELEVANT FILES for" in content


# %%...........................  dataframe stuff  ......................................
def test_cols_we_added_to_data(
    fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
):
    data = some_prep(
        "DLC", fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
    )
    assert (data.columns[0] == "Time") & (data.columns[1] == "Flipped")


def test_datas_indexing_and_time_column(
    fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
):
    for fixture_extract_cfg["sampling_rate"] in [50, 500, 5000]:
        data = some_prep(
            "DLC", fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
        )
        # use isclose here because there are some floating point things going on (eg. 1.
        # 66 and 1.660 for sampling rate of 500)
        assert math.isclose(
            data["Time"].max(),
            (len(data) - 1) / (1 * fixture_extract_cfg["sampling_rate"]),
            rel_tol=1e-9,
        )


# %%...........................  data manipulation  ....................................
def test_global_min_standardisation(
    fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
):
    fixture_extract_cfg["subtract_beam"] = False
    fixture_extract_cfg["standardise_y_to_a_joint"] = False
    data = some_prep(
        "DLC", fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
    )
    y_cols = [c for c in data.columns if c.endswith(" y")]
    assert data[y_cols].min().min() == 0
    # approach here is find difference between global & standardisation joint minma and
    # see if all y cols' difference is equal to that
    # => this implies that joint-based y-standardisation worked
    global_and_standardisation_joints_y_min_diff = data[
        fixture_extract_cfg["y_standardisation_joint"][0] + " y"
    ].min()
    global_min_data = data.copy()
    fixture_extract_cfg["standardise_y_to_a_joint"] = True
    data = some_prep(
        "DLC", fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
    )
    assert np.allclose(  # use np.allclose here because we are comparing arrays
        global_min_data[y_cols],
        data[y_cols] + global_and_standardisation_joints_y_min_diff,
        atol=1e-9,
    )


def test_flip_mouse_body(
    fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
):
    fixture_extract_cfg["flip_gait_direction"] = False
    test_data = some_prep(
        "DLC", fixture_extract_info, fixture_extract_folderinfo, fixture_extract_cfg
    )
    function_flipped_data = test_data.copy()
    function_flipped_data = flip_mouse_body(test_data, fixture_extract_info)
    x_cols = [col for col in function_flipped_data.columns if col.endswith(" x")]
    global_x_max = max(test_data[x_cols].max())
    for col in x_cols:
        function_flipped_series = function_flipped_data[col]
        function_flipped_series = function_flipped_series.astype(float)
        manually_flipped_series = global_x_max - test_data[col]
        pdt.assert_series_equal(function_flipped_series, manually_flipped_series)

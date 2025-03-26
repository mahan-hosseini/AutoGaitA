from autogaita.common2D.common2D_1_preparation import (
    check_and_expand_cfg,
    check_and_fix_cfg_strings,
    flip_mouse_body,
)
from autogaita.dlc.dlc_1_preparation import some_prep
import os
from hypothesis import given, strategies as st, settings, HealthCheck
import pandas.testing as pdt
import pytest


# %%.....................  fixtures  (from dlc unit tests)  ............................
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
def extract_cfg():
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
def test_removal_of_wrong_strings_from_cfg_key(
    test_list, extract_data_using_some_prep, extract_cfg, extract_info
):
    cfg_key = "hind_joints"  # irrelevant since property testing
    extract_cfg[cfg_key] = test_list
    test_result = check_and_fix_cfg_strings(
        extract_data_using_some_prep, extract_cfg, cfg_key, extract_info
    )
    assert not test_result  # empty list is falsey


def test_flip_mouse_body(extract_info, extract_folderinfo, extract_cfg):
    extract_cfg["flip_gait_direction"] = False
    test_data = some_prep(extract_info, extract_folderinfo, extract_cfg)
    function_flipped_data = test_data.copy()
    function_flipped_data = flip_mouse_body(test_data, extract_info)
    x_cols = [col for col in function_flipped_data.columns if col.endswith(" x")]
    global_x_max = max(test_data[x_cols].max())
    for col in x_cols:
        function_flipped_series = function_flipped_data[col]
        function_flipped_series = function_flipped_series.astype(float)
        manually_flipped_series = global_x_max - test_data[col]
        pdt.assert_series_equal(function_flipped_series, manually_flipped_series)

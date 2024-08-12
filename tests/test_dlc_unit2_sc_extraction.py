from autogaita.autogaita_dlc import some_prep
from autogaita.autogaita_dlc import dlc, extract_stepcycles
from autogaita.autogaita_dlc import (
    check_cycle_out_of_bounds,
    check_cycle_duplicates,
    check_cycle_order,
    check_DLC_tracking,
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
    cfg["x_sc_broken_threshold"] = 200  # optional cfg
    cfg["y_sc_broken_threshold"] = 50
    cfg["x_acceleration"] = True
    cfg["angular_acceleration"] = True
    cfg["save_to_xls"] = True
    cfg["bin_num"] = 25
    cfg["plot_SE"] = True
    cfg["normalise_height_at_SC_level"] = False
    cfg["plot_joint_number"] = 3
    cfg["color_palette"] = "viridis"
    cfg["legend_outside"] = True
    cfg["invert_y_axis"] = True
    cfg["flip_gait_direction"] = True
    cfg["analyse_average_x"] = False
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


# %%..............................  test golden path  ..................................


def test_golden_path_extract_stepcycles(
    extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
):
    expected_cycles = [[284, 317], [318, 359], [413, 441]]
    assert (
        extract_stepcycles(
            extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
        )
        == expected_cycles
    )


# %%...................  test Annotation Table checks & handle_issues  .................


def test_file_not_found_error_in_extract_stepcycles(
    extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
):
    extract_folderinfo["root_dir"] = ""
    with pytest.raises(FileNotFoundError) as excinfo:
        extract_stepcycles(
            extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
        )
    assert "No Annotation Table found!" in str(excinfo.value)


def test_handle_issues_1_all_SCs_invalid_because_all_cycles_empty_in_dlc(
    extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
):
    # call dlc and not extract_stepcycles since handle_issues call we test is in dlc
    extract_folderinfo["root_dir"] = os.path.join(
        extract_folderinfo["root_dir"], "flawed_files"
    )
    extract_folderinfo["sctable_filename"] = "flawed_table_all_ID_15_SCs_invalid"
    dlc(extract_info, extract_folderinfo, extract_cfg)
    with open(os.path.join(extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert ("Skipped since all SCs invalid!" in content) & (
        "not in data/video" in content
    )


def test_handle_issues_2_no_scs_of_given_mouse_and_run_in_extract_stepcycles(
    extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
):
    extract_info["mouse_num"] = 12
    extract_info["run_num"] = 1
    extract_stepcycles(
        extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
    )
    with open(os.path.join(extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert "Skipped since no SCs in Annotation Table!" in content


def test_handle_issues_2_wrong_run_number_in_extract_stepcycles(
    extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
):
    extract_info["run_num"] = 123456789101112
    extract_stepcycles(
        extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
    )
    with open(os.path.join(extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert "Skipped since no SCs in Annotation Table!" in content


def test_handle_issues_3_wrong_mouse_number_in_extract_stepcycles(
    extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
):
    extract_info["mouse_num"] = 123456789101112
    extract_stepcycles(
        extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
    )
    with open(os.path.join(extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert "ID not in Annotation Table!" in content


def test_handle_issues_4_bad_annotation_table_columns_in_extract_stepcycles(
    extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
):
    extract_folderinfo["root_dir"] = os.path.join(
        extract_folderinfo["root_dir"], "flawed_files"
    )
    extract_folderinfo["sctable_filename"] = "flawed_table_bad_column_names_table"
    extract_stepcycles(
        extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
    )
    with open(os.path.join(extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert "Annotation Table's Column Names are wrong!" in content


def test_handle_issues_5_double_ID_in_annotation_table_in_extract_stepcycles(
    extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
):
    extract_folderinfo["root_dir"] = os.path.join(
        extract_folderinfo["root_dir"], "flawed_files"
    )
    extract_folderinfo["sctable_filename"] = "flawed_table_double_ID_15_table"
    extract_stepcycles(
        extract_data_using_some_prep, extract_info, extract_folderinfo, extract_cfg
    )
    with open(os.path.join(extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert "ID found more than once in Annotation Table!" in content


# .....................  test clean all_cycles local functions  ........................


@given(
    all_cycles=st.lists(
        st.lists(
            st.one_of(st.integers(), st.floats(), st.text()), min_size=2, max_size=2
        )
    )
)
def test_clean_cycles_1a_cycle_out_of_bounds_in_extract_stepcycles(all_cycles):
    all_cycles = check_cycle_out_of_bounds(all_cycles)
    flat_cycles = flatten_all_cycles(all_cycles)
    if all_cycles:  # can be None
        assert all(isinstance(idx, (int, np.integer)) for idx in flat_cycles)


# Note for following cases that within extract_stepcycles a check for cycle-idxs being in data.index assigns all_cycles[s] to [None, None] - so we have to use that here
cases = (
    (
        [[1, 100], [None, None], [200, 300]],
        [[1, 100], [200, 300]],
    ),
    ([[None, None], [None, None], [None, None]], None),
)  # fmt: skip
@pytest.mark.parametrize("all_cycles, expected_cycles", cases)
def test_clean_cycles_1b_cycle_out_of_bounds_in_extract_stepcycles(
    all_cycles, expected_cycles
):
    assert expected_cycles == check_cycle_out_of_bounds(all_cycles)


cases = (
    (
        [[11, 12], [12, 14], [14, 110], [110, 210]],
        [[11, 12], [13, 14], [15, 110], [111, 210]],
    ),
    ([[1, 2], [2, 3], [3, 4], [4, 5]], [[1, 2], [3, 3], [4, 4], [5, 5]]),
)  # fmt: skip
@pytest.mark.parametrize("all_cycles, expected_cycles", cases)
def test_clean_cycles_2_cycle_duplicates_in_extract_stepcycles(
    all_cycles, expected_cycles
):
    assert expected_cycles == check_cycle_duplicates(all_cycles)


@given(all_cycles=st.lists(st.lists(st.integers(), min_size=2, max_size=2)))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_clean_cycles_3_cycle_order(all_cycles, extract_info):
    """Note here that we manually create results_dir's tmp_path if required bc. it's usually created in dlc somewhere and that hypothesis complains without the if not condition bc. the path keeps being created for new cases I think!"""
    if not os.path.exists(extract_info["results_dir"]):
        os.makedirs(extract_info["results_dir"])
    all_cycles = check_cycle_order(all_cycles, extract_info)
    flat_cycles = flatten_all_cycles(all_cycles)
    if all_cycles:  # can be None
        assert flat_cycles == sorted(flat_cycles)


def test_clean_cycles_4_DLC_tracking(
    extract_data_using_some_prep, extract_info, extract_cfg
):
    """Note that we know that very early on (2-150) the mouse was not in the frame yet so DLC is broken and these SCs will be excluded. The other 3 of case 2 are the correcty SCs of this ID/run of which None should be excluded!"""
    all_cycles_of_the_two_cases = (
        [[2, 50], [52, 100], [102, 150]],
        [[2, 50], [52, 100], [102, 150], [284, 317], [318, 359], [413, 441]],
    )
    expected_cycles = ([None], [[284, 317], [318, 359], [413, 441]])
    for c, this_cases_all_cycles in enumerate(all_cycles_of_the_two_cases):
        expected_cycles[c] == check_DLC_tracking(
            extract_data_using_some_prep,
            extract_info,
            this_cases_all_cycles,
            extract_cfg,
        )


# ...............................  helper functions  ...................................
def flatten_all_cycles(all_cycles):
    if all_cycles:
        return [idx for cycle in all_cycles for idx in cycle]

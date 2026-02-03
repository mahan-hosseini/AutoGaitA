from autogaita.resources.utils import (
    standardise_primary_joint_coordinates,
    compute_angle,
    define_bins,
    write_angle_warning,
)
from autogaita.common2D.common2D_1_preparation import some_prep as some_prep_2D
from autogaita.universal3D.universal3D_1_preparation import some_prep as some_prep_3D
from autogaita.common2D.common2D_2_sc_extraction import extract_stepcycles
from autogaita.common2D.common2D_3_analysis import analyse_and_export_stepcycles
import os
import math
import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest


# %%...........................  2D GaitA fixtures  ....................................
@pytest.fixture
def extract_2D_info(tmp_path):
    info = {}
    info["mouse_num"] = 15
    info["run_num"] = 3
    info["name"] = "ID " + str(info["mouse_num"]) + " - Run " + str(info["run_num"])
    info["results_dir"] = os.path.join(tmp_path, info["name"])
    return info


@pytest.fixture
def extract_2D_folderinfo():
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
def extract_2D_cfg():
    cfg = {}
    cfg["sampling_rate"] = 100
    cfg["subtract_beam"] = False
    cfg["dont_show_plots"] = True
    cfg["convert_to_mm"] = False  # false!
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
    cfg["flip_gait_direction"] = False
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


# %%...........................  3D GaitA fixtures  ....................................
@pytest.fixture
def extract_3D_info(tmp_path):
    info = {}
    info["name"] = "TestSubject"
    info["results_dir"] = os.path.join(tmp_path, info["name"])
    return info


@pytest.fixture
def extract_3D_folderinfo():
    folderinfo = {}
    folderinfo["root_dir"] = "tests/test_data/universal3D_data/test_data/"
    folderinfo["sctable_filename"] = "SC Latency Table"
    folderinfo["postname_string"] = ""
    return folderinfo


@pytest.fixture
def extract_3D_cfg():
    cfg = {}
    cfg["sampling_rate"] = 100
    cfg["dont_show_plots"] = True
    cfg["y_acceleration"] = True
    cfg["angular_acceleration"] = True
    cfg["bin_num"] = 25
    cfg["plot_SE"] = True
    cfg["standardise_z_at_SC_level"] = True
    cfg["standardise_z_to_a_joint"] = False
    cfg["z_standardisation_joint"] = ["Midfoot, left"]
    cfg["plot_joint_number"] = 7
    cfg["legend_outside"] = True
    cfg["flip_gait_direction"] = False
    cfg["color_palette"] = "viridis"
    cfg["analyse_average_y"] = False
    cfg["standardise_y_coordinates"] = True
    cfg["y_standardisation_joint"] = ["Midfoot, left"]
    cfg["coordinate_standardisation_xls"] = ""
    cfg["joints"] = ["Midfoot", "Ankle", "Knee", "Hip", "Pelvis "]
    cfg["angles"] = {
        "name": ["Ankle", "Knee", "Hip"],
        "lower_joint": ["Midfoot", "Ankle", "Knee"],
        "upper_joint": ["Knee", "Hip", "Pelvis "],
    }
    return cfg


# %% .................................  tests  .........................................


def test_compute_angle():
    # Test case 1: Basic case
    joint1 = [0, 0]
    joint2 = [1, 0]
    joint3 = [0, 1]
    expected_angle = 90
    result, _ = compute_angle(joint1, joint2, joint3)
    assert math.isclose(result, expected_angle)
    # Test case 2: two joints are equal - this won't happen in autogaita because of the
    # test in extract_stepcycles but I want to make sure that the function returns
    # broken=True correctly
    joint1 = [5, 5]
    joint2 = [2, 2]
    joint3 = [2, 2]
    expected_angle = None
    result, broken = compute_angle(joint1, joint2, joint3)
    assert result == 0
    assert broken is True


def test_write_angle_warning(extract_2D_cfg, extract_2D_info):
    # prep: remove existing Issues.txt
    results_dir = extract_2D_info["results_dir"]
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    issues_path = os.path.join(results_dir, "Issues.txt")
    if os.path.exists(issues_path):
        os.remove(issues_path)
    # prep: more vars
    step = pd.DataFrame()
    step["Time"] = [0.1, 0.2, 0.3]
    step["dummy_coord"] = [1, 2, 3]  # need this too otherwise stuff breaks
    angles = extract_2D_cfg["angles"]
    a = 0
    broken_angle_idxs = [0, 2]
    # run
    write_angle_warning(step, a, angles, broken_angle_idxs, extract_2D_info)
    # assert
    with open(issues_path, "r") as f:
        issues = f.read()
    assert (
        "Angle: Ankle" in issues  # bc. of extract_2D_cfg
        and "Lower Joint: Hind paw tao" in issues
        and "Upper Joint: Knee" in issues
        and "Cycle-time: 0.1-0.3s" in issues
    )
    # run again - test legname works as expected
    os.remove(issues_path)  # first remove previous textfile
    write_angle_warning(
        step, a, angles, broken_angle_idxs, extract_2D_info, legname="left"
    )
    with open(issues_path, "r") as f:
        issues = f.read()
    assert "Leg: left" in issues


def test_correct_coordinate_standardisation(
    extract_2D_info,
    extract_2D_folderinfo,
    extract_2D_cfg,
    extract_3D_info,
    extract_3D_folderinfo,
    extract_3D_cfg,
):
    for tracking_software in ["DLC", "Universal 3D"]:
        # prep vars
        if tracking_software == "DLC":
            info = extract_2D_info
            folderinfo = extract_2D_folderinfo
            cfg = extract_2D_cfg
        else:
            info = extract_3D_info
            folderinfo = extract_3D_folderinfo
            cfg = extract_3D_cfg
        # run respective some_prep functions to get dfs
        if tracking_software == "DLC":
            # unstandardised data
            cfg["coordinate_standardisation_xls"] = ""
            unstandardised_data = some_prep_2D(tracking_software, info, folderinfo, cfg)
            # standardised data
            cfg["coordinate_standardisation_xls"] = (
                "tests/test_data/utils/Correct DLC CoordStand Table.xlsx"
            )
            standardised_data = some_prep_2D(tracking_software, info, folderinfo, cfg)
        elif tracking_software == "Universal 3D":
            # unstandardised data
            cfg["coordinate_standardisation_xls"] = ""
            unstandardised_data = some_prep_3D(info, folderinfo, cfg)[0]  # tuple!
            # standardised data
            cfg["coordinate_standardisation_xls"] = (
                "tests/test_data/utils/Correct Universal 3D CoordStand Table.xlsx"
            )
            standardised_data, global_Y_max = some_prep_3D(info, folderinfo, cfg)
        # revert standardisation
        reverted_data = standardised_data.copy()
        standardisation_df = pd.read_excel(
            cfg["coordinate_standardisation_xls"]
        ).astype(str)
        if tracking_software == "DLC":
            condition = (standardisation_df["ID"] == str(info["mouse_num"])) & (
                standardisation_df["Run"] == str(info["run_num"])
            )
        elif tracking_software == "Universal 3D":
            condition = standardisation_df["ID"] == info["name"]
        standardisation_value = float(
            standardisation_df.loc[condition, "Standardisation Value"]
        )
        if tracking_software == "DLC":
            cols_to_revert = [
                col
                for col in reverted_data.columns
                if (not col.endswith("likelihood"))
                and any([joint in col for joint in cfg["hind_joints"]])
            ]
        elif tracking_software == "Universal 3D":
            cols_to_revert = [
                col
                for col in reverted_data.columns
                if any([joint in col for joint in cfg["joints"]])
            ]
        reverted_data[cols_to_revert] *= standardisation_value

        # compare dataframes
        pd.testing.assert_frame_equal(
            reverted_data, unstandardised_data, check_exact=False, check_dtype=False
        )


def test_angles_are_unaffected_by_coordinate_standardisation(
    extract_2D_info, extract_2D_folderinfo, extract_2D_cfg
):
    # prep: run dlc_main's first 3 steps to get dfs with angles
    # 1) for unstandardised data
    data = some_prep_2D("DLC", extract_2D_info, extract_2D_folderinfo, extract_2D_cfg)
    all_cycles = extract_stepcycles(
        "DLC", data, extract_2D_info, extract_2D_folderinfo, extract_2D_cfg
    )
    unstandardised_results = analyse_and_export_stepcycles(
        data, all_cycles, extract_2D_info, extract_2D_cfg
    )
    # 2) for standardised data
    extract_2D_cfg["coordinate_standardisation_xls"] = (
        "autogaita/resources/Coordinate Standardisation Table Template.xlsx"
    )
    data = some_prep_2D("DLC", extract_2D_info, extract_2D_folderinfo, extract_2D_cfg)
    all_cycles = extract_stepcycles(
        "DLC", data, extract_2D_info, extract_2D_folderinfo, extract_2D_cfg
    )
    standardised_results = analyse_and_export_stepcycles(
        data, all_cycles, extract_2D_info, extract_2D_cfg
    )
    # compare angles
    cols_to_compare = [
        col
        for col in unstandardised_results["average_data"].columns
        if col.endswith("Angle")
    ]
    pdt.assert_frame_equal(
        unstandardised_results["average_data"][cols_to_compare],
        standardised_results["average_data"][cols_to_compare],
    )


# Parameterized test for error cases
@pytest.mark.parametrize(
    "xls_path, expected_error",
    [
        (
            "autogaita/resources/This CoordStand Table is Missing.xlsx",
            "No coordinate standardisation xls file found at:",
        ),
        (
            "tests/test_data/utils/This CoordStand Table has wrong columns.xlsx",
            "does not have the correct column names",
        ),
        (
            "tests/test_data/utils/This CoordStand Table has wrong Run.xlsx",
            "Unable to find",
        ),
        (
            "tests/test_data/utils/This CoordStand Table has multiple Names.xlsx",
            "Found multiple entries for",
        ),
        (
            "tests/test_data/utils/This CoordStand Table doesn't have a float as standval.xlsx",
            "Unable to convert standardisation value for",
        ),
        (
            "tests/test_data/utils/This CoordStand Table has a value smaller than 1.xlsx",
            "smaller than 1!",
        ),
    ],
)
def test_standardisation_xls_error_cases(
    extract_2D_info, extract_2D_folderinfo, extract_2D_cfg, xls_path, expected_error
):
    # prep: remove existing Issues.txt
    results_dir = extract_2D_info["results_dir"]
    issues_path = os.path.join(results_dir, "Issues.txt")
    if os.path.exists(issues_path):
        os.remove(issues_path)

    # set the xls path in the config & run some_prep which will run the standardisation
    extract_2D_cfg["coordinate_standardisation_xls"] = xls_path
    with pytest.raises(Exception):
        data = some_prep_2D(
            "DLC", extract_2D_info, extract_2D_folderinfo, extract_2D_cfg
        )

    # assert the error message - inform about what error failed if it did
    with open(issues_path, "r") as f:
        issues = f.read()
    assert (
        expected_error in issues
    ), f"Expected error '{expected_error}' not found in Issues.txt"


def test_angle_joints_not_in_joints(
    extract_2D_info, extract_2D_folderinfo, extract_2D_cfg
):
    # prep cfg stuff
    cfg = extract_2D_cfg.copy()
    cfg["coordinate_standardisation_xls"] = (
        "tests/test_data/utils/Correct DLC CoordStand Table.xlsx"
    )
    cfg["hind_joints"] = ["Ankle", "Knee", "Hip"]
    cfg["angles"] = {  # hind paw is to be removed (not in cfg["joints"]!)
        "name": ["Hind paw tao", "Knee", "Knee", "Knee"],
        "lower_joint": ["Ankle", "Hind paw tao", "Ankle", "Ankle"],
        "upper_joint": ["Hip", "Hip", "Hind paw tao", "Hip"],
    }
    # prep: remove existing Issues.txt
    results_dir = extract_2D_info["results_dir"]
    issues_path = os.path.join(results_dir, "Issues.txt")
    if os.path.exists(issues_path):
        os.remove(issues_path)
    # run (not just some prep, because we want the cfg, too)
    data = some_prep_2D("DLC", extract_2D_info, extract_2D_folderinfo, cfg)
    data, cfg = standardise_primary_joint_coordinates(data, "DLC", extract_2D_info, cfg)
    # assert error
    with open(issues_path, "r") as f:
        issues = f.read()
    assert "We will update your cfg (!)" in issues
    # assert updated cfg
    assert cfg["angles"] == {
        "name": ["Knee "],
        "lower_joint": ["Ankle "],
        "upper_joint": ["Hip "],
    }


def test_define_bins_longer_trial():
    # triallength > bin_num: should return a list of lists covering all indices
    triallength = 100
    bin_num = 25
    bins = define_bins(triallength, bin_num)
    assert isinstance(bins, list)
    assert len(bins) == bin_num
    # each element should be a list of indices
    assert all(isinstance(b, list) for b in bins)
    flattened = [i for sub in bins for i in sub]
    assert set(flattened) == set(range(triallength))
    assert min(flattened) == 0
    assert max(flattened) == triallength - 1
    # check indices are correct for moving averages
    triallength = 8
    bin_num = 3
    bins = define_bins(triallength, bin_num)
    assert bins == [[0, 1, 2], [3, 4, 5], [6, 7]]


def test_define_bins_shorter_trial():
    # triallength < bin_num: should return an array (or list) of length bin_num
    # with values in the range [0, triallength-1] and max == triallength-1
    triallength = 10
    bin_num = 25
    bins = define_bins(triallength, bin_num)
    # allow either numpy array or list-like
    bins_list = list(bins)
    assert len(bins_list) == bin_num
    assert all(0 <= v <= (triallength - 1) for v in bins_list)
    assert max(bins_list) == triallength - 1
    assert min(bins_list) == 0
    # check that values are spaced evenly across the trial
    triallength = 5
    bin_num = 12
    bins = define_bins(triallength, bin_num)
    assert bins == [0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 4, 4]


def test_define_bins_equal_length():
    # triallength == bin_num: should return a list of ints equal to range(triallength)
    triallength = 25
    bin_num = 25
    bins = define_bins(triallength, bin_num)
    assert isinstance(bins, list)
    assert len(bins) == bin_num
    # elements should be ints 0..triallength-1
    assert all(isinstance(b, (int, np.integer)) for b in bins)
    assert bins == list(range(triallength))

from autogaita.resources.utils import standardise_primary_joint_coordinates
from autogaita.common2D.common2D_1_preparation import some_prep
import os
import pandas as pd
import pytest


# %%..............................  fixtures  ..........................................
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
    cfg["subtract_beam"] = False  # false!
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


# ..................................  tests  .........................................
def test_correct_coordinate_standardisation(
    extract_info, extract_folderinfo, extract_cfg
):
    # unstandardised data
    extract_cfg["coordinate_standardisation_xls"] = ""
    unstandardised_data = some_prep(
        "DLC", extract_info, extract_folderinfo, extract_cfg
    )

    # standardised data
    extract_cfg["coordinate_standardisation_xls"] = (
        "autogaita/resources/Coordinate Standardisation Table Template.xlsx"
    )
    standardised_data = some_prep("DLC", extract_info, extract_folderinfo, extract_cfg)

    # revert standardisation
    reverted_data = standardised_data.copy()
    standardisation_df = pd.read_excel(
        extract_cfg["coordinate_standardisation_xls"]
    ).astype(str)
    condition = (standardisation_df["ID"] == str(extract_info["mouse_num"])) & (
        standardisation_df["Run"] == str(extract_info["run_num"])
    )
    standardisation_value = float(
        standardisation_df.loc[condition, "Standardisation Value"]
    )
    cols_to_revert = [
        col
        for col in reverted_data.columns
        if (not col.endswith("likelihood"))
        and any([joint in col for joint in extract_cfg["hind_joints"]])
    ]
    reverted_data[cols_to_revert] *= standardisation_value

    # compare dataframes
    pd.testing.assert_frame_equal(
        reverted_data, unstandardised_data, check_exact=False, check_dtype=False
    )


def test_standardisation_xls_error_cases(extract_info, extract_folderinfo, extract_cfg):
    # prep: get data using some_prep
    name = extract_info["name"]
    data = some_prep("DLC", extract_info, extract_folderinfo, extract_cfg)

    # Error 1 - no standardisation xls file
    if os.path.exists(os.path.join(extract_info["results_dir"], "Issues.txt")):
        os.remove(os.path.join(extract_info["results_dir"], "Issues.txt"))
    extract_cfg["coordinate_standardisation_xls"] = (
        "autogaita/resources/This CoordStand Table is Missing.xlsx"
    )
    data = standardise_primary_joint_coordinates(data, "DLC", extract_info, extract_cfg)
    with open(os.path.join(extract_info["results_dir"], "Issues.txt"), "r") as f:
        issues = f.read()
    assert "No coordinate standardisation xls file found at:" in issues

    # Error 2 - xls file has wrong column names
    if os.path.exists(os.path.join(extract_info["results_dir"], "Issues.txt")):
        os.remove(os.path.join(extract_info["results_dir"], "Issues.txt"))
    extract_cfg["coordinate_standardisation_xls"] = (
        "tests/test_data/utils/This CoordStand Table has wrong columns.xlsx"
    )
    data = standardise_primary_joint_coordinates(data, "DLC", extract_info, extract_cfg)
    with open(os.path.join(extract_info["results_dir"], "Issues.txt"), "r") as f:
        issues = f.read()
    assert "does not have the correct column names" in issues

    # Error 3 - xls file does not have ID/Run
    if os.path.exists(os.path.join(extract_info["results_dir"], "Issues.txt")):
        os.remove(os.path.join(extract_info["results_dir"], "Issues.txt"))
    extract_cfg["coordinate_standardisation_xls"] = (
        "tests/test_data/utils/This CoordStand Table has wrong Run.xlsx"
    )
    data = standardise_primary_joint_coordinates(data, "DLC", extract_info, extract_cfg)
    with open(os.path.join(extract_info["results_dir"], "Issues.txt"), "r") as f:
        issues = f.read()
    assert f"Unable to find {name}" in issues

    # Error 4 - xls file has ID/Run multiple times
    if os.path.exists(os.path.join(extract_info["results_dir"], "Issues.txt")):
        os.remove(os.path.join(extract_info["results_dir"], "Issues.txt"))
    extract_cfg["coordinate_standardisation_xls"] = (
        "tests/test_data/utils/This CoordStand Table has multiple Names.xlsx"
    )
    data = standardise_primary_joint_coordinates(data, "DLC", extract_info, extract_cfg)
    with open(os.path.join(extract_info["results_dir"], "Issues.txt"), "r") as f:
        issues = f.read()
    assert f"Found multiple entries for {name}" in issues

    # Error 5 - xls file does not have a number in standardisation value
    if os.path.exists(os.path.join(extract_info["results_dir"], "Issues.txt")):
        os.remove(os.path.join(extract_info["results_dir"], "Issues.txt"))
    extract_cfg["coordinate_standardisation_xls"] = (
        "tests/test_data/utils/This CoordStand Table doesn't have a float as standval.xlsx"
    )
    data = standardise_primary_joint_coordinates(data, "DLC", extract_info, extract_cfg)
    with open(os.path.join(extract_info["results_dir"], "Issues.txt"), "r") as f:
        issues = f.read()
    assert "Unable to convert standardisation value for " in issues

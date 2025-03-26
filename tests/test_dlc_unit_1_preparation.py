from autogaita.common2D.common2D_1_preparation import (
    some_prep,
    move_data_to_folders,
    check_gait_direction,
)
import os
import pandas as pd
import pytest


# %%................................  fixtures  ........................................
@pytest.fixture
def extract_data_using_some_prep(extract_info, extract_folderinfo, extract_cfg):
    data = some_prep("DLC", extract_info, extract_folderinfo, extract_cfg)
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


def test_move_csv_datafile_to_results_dir(extract_info, extract_folderinfo):
    move_data_to_folders("DLC", ".csv", extract_info, extract_folderinfo)
    for file in os.listdir(extract_info["results_dir"]):
        if file.endswith(".csv"):
            assert (
                (extract_folderinfo["premouse_string"] in file)
                & (extract_folderinfo["postmouse_string"] in file)
                & (extract_folderinfo["prerun_string"] in file)
                & (extract_folderinfo["postrun_string"] in file)
            )


def test_check_gait_direction(extract_data_using_some_prep, extract_cfg, extract_info):
    direction_joint = extract_cfg["direction_joint"]
    flip_gait_direction = True  # 1) test broken DLC data (empty)
    broken_data = pd.DataFrame(data=None, columns=extract_data_using_some_prep.columns)
    check_gait_direction(
        "DLC", broken_data, direction_joint, flip_gait_direction, extract_info
    )
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
        "DLC", flip_this_data, direction_joint, flip_gait_direction, extract_info
    )
    assert flip_this_data["Flipped"][0] == True

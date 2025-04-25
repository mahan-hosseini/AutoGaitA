from autogaita.universal3D.universal3D_1_preparation import some_prep
from autogaita.universal3D.universal3D_2_sc_extraction import (
    check_different_angle_joint_coords,
)
import os
import numpy as np
import pytest


# %%................................  fixtures  ........................................
@pytest.fixture
def extract_info(tmp_path):
    info = {}
    info["name"] = "TestSubject"
    info["results_dir"] = os.path.join(tmp_path, info["name"])
    return info


@pytest.fixture
def extract_folderinfo():
    folderinfo = {}
    folderinfo["root_dir"] = "tests/test_data/universal3D_data/test_data"
    folderinfo["sctable_filename"] = "SC Latency Table.xlsx"
    folderinfo["postname_string"] = ""
    return folderinfo


@pytest.fixture
def extract_cfg():
    # note space in end of "Midfoot, left " must be here bc. we don't run our fix and
    # check cfg function of 1_prep_
    cfg = {}
    cfg["sampling_rate"] = 100  # base cfg
    cfg["dont_show_plots"] = True
    cfg["y_acceleration"] = True
    cfg["angular_acceleration"] = True
    cfg["bin_num"] = 25
    cfg["plot_SE"] = True
    cfg["standardise_z_at_SC_level"] = True
    cfg["standardise_z_to_a_joint"] = True
    cfg["z_standardisation_joint"] = ["Midfoot, left "]
    cfg["plot_joint_number"] = 5
    cfg["color_palette"] = "Set2"
    cfg["legend_outside"] = True
    cfg["flip_gait_direction"] = True
    cfg["analyse_average_y"] = True
    cfg["standardise_y_coordinates"] = True
    cfg["y_standardisation_joint"] = ["Midfoot, left "]
    cfg["coordinate_standardisation_xls"] = ""
    cfg["joints"] = [
        "Midfoot",
        "Ankle",
        "Knee",
        "Hip",
    ]
    cfg["angles"] = {
        "name": ["Ankle", "Knee"],
        "lower_joint": ["Midfoot", "Ankle"],
        "upper_joint": ["Knee", "Hip"],
    }
    cfg["direction_joint"] = "Midfoot, left Y"
    return cfg


# ..................................  tests  .........................................


def test_clean_cycles_different_angle_joint_coords(
    extract_info, extract_folderinfo, extract_cfg
):
    # start conditions
    data, _ = some_prep(extract_info, extract_folderinfo, extract_cfg)
    all_cycles = [[[111, 222], [333, 444]], [[555, 666], [777, 888]]]
    # test one: leads to both lists still being non-empty, one SC removed
    data.loc[123, "Ankle, left Y"] = 5.5
    data.loc[123, "Ankle, left Z"] = 2.1
    data.loc[123, "Midfoot, left Y"] = 5.5
    data.loc[123, "Midfoot, left Z"] = 2.1
    all_cycles = check_different_angle_joint_coords(
        all_cycles, data, extract_info, extract_cfg
    )
    assert all_cycles == [[[333, 444]], [[555, 666], [777, 888]]]
    with open(os.path.join(extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert "Run #1 - SC #1" in content
    assert "equal LEFT" in content
    assert "Lower joint: Midfoot" in content
    # test two: leads to one empty list
    data.loc[345, "Hip, right Y"] = 10.1
    data.loc[345, "Hip, right Z"] = 0.333
    data.loc[345, "Ankle, right Y"] = 10.1
    data.loc[345, "Ankle, right Z"] = 0.333
    all_cycles = check_different_angle_joint_coords(
        all_cycles, data, extract_info, extract_cfg
    )
    assert all_cycles == [[], [[555, 666], [777, 888]]]
    with open(os.path.join(extract_info["results_dir"], "Issues.txt")) as f:
        content = f.read()
    assert "RIGHT" in content
    # test three: leads to all_cycles being None
    data.loc[[567, 789], "Hip, right Y"] = 22.2
    data.loc[[567, 789], "Hip, right Z"] = 0.11
    data.loc[[567, 789], "Knee, right Y"] = 22.2
    data.loc[[567, 789], "Knee, right Z"] = 0.11
    assert (
        check_different_angle_joint_coords(all_cycles, data, extract_info, extract_cfg)
        is None
    )

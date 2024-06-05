from autogaita.autogaita_dlc import some_prep
from autogaita.autogaita_dlc import add_angles, add_velocities
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


# %%.......  main analysis: sc-lvl y-norm, features, df-creation & export ..........


def test_dlc_height_normalisation_no_beam():
    """Unit test normalising heights if there is no beam"""
    # Create a sample DataFrame
    data = {
        "first_y": [-10, -5, 0, 10],
        "second_y": [10, 20, 30, 40],
        "third_y": [5, 15, 25, 35],
    }
    step = pd.DataFrame(data)
    y_cols = [col for col in step.columns if col.endswith("y")]
    this_y_min = step[y_cols].min().min()
    step[y_cols] -= this_y_min
    # Expected result
    expected_result = {
        "first_y": [0, 5, 10, 20],
        "second_y": [20, 30, 40, 50],
        "third_y": [15, 25, 35, 45],
    }
    expected_step = pd.DataFrame(expected_result)
    # Compare the result with the expected result
    pdt.assert_frame_equal(step, expected_step)


cases = [
    ((0, 0), (1, 0), (0, 1), 90), 
    ((0, 0), (1, 0), (0, 0.5), 90),
    ((0, 0), (1, 0), (2, 0), 0)
]  # fmt: skip
@pytest.mark.parametrize("angle_x_y, lower_x_y, upper_x_y, expected_angle", cases)
def test_dlc_angles(angle_x_y, lower_x_y, upper_x_y, expected_angle):
    step = (
        pd.Series(
            {
                "angle x": angle_x_y[0],
                "angle y": angle_x_y[1],
                "lower x": lower_x_y[0],
                "lower y": lower_x_y[1],
                "upper x": upper_x_y[0],
                "upper y": upper_x_y[1],
            }
        )
        .to_frame()
        .T
    )

    cfg = {}
    cfg["angles"] = {
        "name": ["angle "],
        "lower_joint": ["lower "],
        "upper_joint": ["upper "],
    }
    step = add_angles(step, cfg)
    assert step["angle Angle"].values == expected_angle


@given(x_y_coordinates = st.tuples(st.one_of(st.integers(), st.floats()), st.one_of(st.integers(), st.floats())))  # fmt: skip
@pytest.mark.filterwarnings("ignore:invalid value encountered")
def test_dlc_angles_is_nan_when_all_points_are_at_same_location(x_y_coordinates):
    angle_x_y = lower_x_y = upper_x_y = x_y_coordinates
    step = (
        pd.Series(
            {
                "angle x": angle_x_y[0],
                "angle y": angle_x_y[1],
                "lower x": lower_x_y[0],
                "lower y": lower_x_y[1],
                "upper x": upper_x_y[0],
                "upper y": upper_x_y[1],
            }
        )
        .to_frame()
        .T
    )

    cfg = {}
    cfg["angles"] = {
        "name": ["angle "],
        "lower_joint": ["lower "],
        "upper_joint": ["upper "],
    }
    step = add_angles(step, cfg)
    assert step["angle Angle"].isna().all()


def test_dlc_velocities():
    """Unit test of how velocities are added
    A Note
    ------
    If you ever consider testing if velocities are expected after flipping x-values using flip_mouse_body - DON'T!
    => We only flip if gait direction is right=>left in the first place and thus: velocities are CORRECT and comparable to non-flipped left=>right videos.
    => NU - write a test that confirms this formally
    """
    data = {
        "Sample x": [0.0, 2.0, 4.0, 8.0, 8.0, 4.0, 2.0, 0.0, -2.0, -10.0],
        "Sample Angle": [-10.0, -8.0, -7.0, -4.0, 0.0, 4.0, 10.0, 20.0, 10.0, 0.0],
    }
    step = pd.DataFrame(data)
    cfg = {
        "hind_joints": ["Sample "],
        "x_acceleration": True,
        "angular_acceleration": True,
    }
    step = add_velocities(step, cfg)
    # expected values were obtained by calling np.gradient on arrays above
    expected_values = {
        "Sample Velocity": [2.0, 2.0, 3.0, 2.0, -2.0, -3.0, -2.0, -2.0, -5.0, -8.0],
        "Sample Acceleration": [0.0, 0.5, 0.0, -2.5, -2.5, 0.0, 0.5, -1.5, -3.0, -3.0],
        "Sample Angle Velocity": [2.0, 1.5, 2.0, 3.5, 4.0, 5.0, 8.0, 0.0, -10.0, -10.0],
        "Sample Angle Acceleration": [
            -0.5,
            0.0,
            1.0,
            1.0,
            0.75,
            2.0,
            -2.5,
            -9.0,
            -5.0,
            0.0,
        ],
    }
    for key in expected_values.keys():
        assert all(expected_values[key] == step[key])


# what happens if we hit run
if __name__ == "__main__":
    test_dlc_velocities()

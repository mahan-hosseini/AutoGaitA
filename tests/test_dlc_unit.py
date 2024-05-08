from autogaita.autogaita_dlc import compute_angle, add_angles, add_velocities
import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest
import pdb

# This script stores all unit tests for AutoGaitA DLC.
#
# Note
# ----
# 1) This script is used with pytest and Github Actions
# 2) Most of these are also present in the tests of AutoGaitA Simi
# 3) We use autogaita_dlc's processing pipeline structure here too

# %%..............................  preparation  ...................................

# %%.......................  step-cycle extraction  ................................

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


def test_dlc_angles():
    """Unit test of how angles are added"""
    # note that np.array line initalises step's joint-coords according to:
    # joint_angle = (0, 0)
    # joint2 = (1, 0)
    # joint3 = (0, 1)
    expected_angle = 90
    step = pd.DataFrame(
        data=np.array([[0, 0, 1, 0, 0, 1]]),
        columns=[
            "angle x",
            "angle y",
            "lower x",
            "lower y",
            "upper x",
            "upper y",
        ],
    )
    cfg = {}
    cfg["angles"] = {
        "name": ["angle "],
        "lower_joint": ["lower "],
        "upper_joint": ["upper "],
    }
    step = add_angles(step, cfg)
    assert step["angle Angle"].values == expected_angle

    # previous approach: testing compute_angles
    # joint_angle = (0, 0)
    # joint2 = (1, 0)
    # joint3 = (0, 1)
    # assert compute_angle(joint_angle, joint2, joint3) == expected_angle


def test_dlc_velocities():
    """Unit test of how velocities are added"""
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


# %%..............................  plots  .........................................

# %%..........................  print finish  ......................................


# what happens if we hit run
if __name__ == "__main__":
    test_dlc_velocities()

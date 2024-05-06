from autogaita.autogaita_dlc import compute_angle, add_angles
import numpy as np
import pandas as pd
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
# test_angles()

# %%..............................  plots  .........................................

# %%..........................  print finish  ......................................


def test_dlc_angles():
    """Unit test of compute_angles local function of dlc"""
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


# what happens if we hit run
if __name__ == "__main__":
    test_dlc_angles()

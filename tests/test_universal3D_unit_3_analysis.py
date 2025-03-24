from autogaita.universal3D.universal3D_3_analysis import (
    standardise_y_z_flip_gait_add_features_to_one_step,
    add_features,
)
from hypothesis import HealthCheck, given, settings, strategies as st
import pytest
import pandas as pd
import pandas.testing as pdt
import numpy as np
import os


# %%................................  fixtures  ........................................
@pytest.fixture
def extract_info(tmp_path):
    info = {}
    info["name"] = "SK"
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


sample_step_len = 10  # 10 datapoints (e.g. time)
sample_step_col_num = 20  # 10 for each Y and Z


@pytest.fixture
def sample_step():
    joint_strings = [
        "Midfoot, left",
        "Ankle, left",
        "Knee, left",
        "Hip, left",
        "Midfoot, right",
        "Ankle, right",
        "Knee, right",
        "Hip, right",
        "Shoulder",
        "Neck",
    ]
    sample_step = {}
    for joint in joint_strings:
        for coord in [" Y", " Z"]:
            sample_step[joint + coord] = list(
                np.random.randint(1, 101, sample_step_len)
            )
    return pd.DataFrame(sample_step)


# ............................  for property tests  ....................................
# 1. define the sample_steps_data strategy using random ints as data
sample_steps_data_strategy = st.lists(
    st.lists(
        st.integers(min_value=-1000, max_value=1000),
        min_size=sample_step_col_num,  # 20 cols (10 for each Y and Z)
        max_size=sample_step_col_num,
    ),
    min_size=sample_step_len,  # 10 rows
    max_size=sample_step_len,
)


# 2. create a custom decorator that can be used instead of writing given/settings
#    always
def sample_data_for_property_tests(func):
    return settings(suppress_health_check=(HealthCheck.function_scoped_fixture,))(
        given(sample_steps_data=sample_steps_data_strategy)(func)
    )


# ..................................  tests  .........................................
# %% workflow step #3 - y-flipping, y-stand, features, df-creation & exports


def test_standardise_z_at_SC_level(sample_step, extract_cfg):
    extract_cfg["standardise_z_at_SC_level"] = True
    extract_cfg["standardise_z_to_a_joint"] = False
    extract_cfg["flip_gait_direction"] = False
    extract_cfg["standardise_y_coordinates"] = False
    z_cols = [col for col in sample_step.columns if col.endswith("Z")]
    function_step = standardise_y_z_flip_gait_add_features_to_one_step(
        sample_step, 10, extract_cfg
    )
    sample_step = add_features(sample_step, extract_cfg)  # otherwise df-shape mismatch
    steps_global_z_minimum = sample_step[z_cols].min().min()  # global == all joints
    expected_step = sample_step.copy()
    expected_step[z_cols] -= steps_global_z_minimum
    pdt.assert_frame_equal(function_step, expected_step)


def test_flip_gait_direction(sample_step, extract_cfg):
    # prepare some vars
    extract_cfg["flip_gait_direction"] = True
    extract_cfg["standardise_y_coordinates"] = False
    global_Y_max = 10
    to_be_flipped_step = sample_step.copy()
    to_not_be_flipped_step = sample_step.copy()
    y_cols = [col for col in sample_step.columns if col.endswith("Y")]
    # step sample is random integers, so first fix the direction of y-values, either
    # increasing or decreasing (decreasing must be flipped)
    for col in y_cols:
        to_be_flipped_step[col] = to_be_flipped_step[col].sort_values(
            ascending=False, ignore_index=True
        )
        to_not_be_flipped_step[col] = to_not_be_flipped_step[col].sort_values(
            ascending=True, ignore_index=True
        )
    to_be_flipped_step = standardise_y_z_flip_gait_add_features_to_one_step(
        to_be_flipped_step, global_Y_max, extract_cfg
    )
    to_not_be_flipped_step = standardise_y_z_flip_gait_add_features_to_one_step(
        to_not_be_flipped_step, global_Y_max, extract_cfg
    )
    # first test if the y-values are flipped (increasing y-cols progressively)
    for col in y_cols:
        assert to_be_flipped_step[col][0] < to_be_flipped_step[col].mean()
    # now, test that if you reverse the impact of global_y_max you get your original df
    # 1. reverse subtraction of global y max before comparison for df-equivalence
    # => e.g. 10 - 2 = 8 || reverse via: 10 - 8 = 2!
    to_be_flipped_step[y_cols] = global_Y_max - to_be_flipped_step[y_cols]
    # 2. reverting of 1. changes y-values to now be decreasing (2 4 8 becomes 8 4 2)
    # => sooo manually make it so that it is increasing again and then you should have
    #    equal dfs
    for col in y_cols:
        to_be_flipped_step[col] = to_be_flipped_step[col].sort_values(
            ascending=True, ignore_index=True
        )
    # 3. remove the cols that were created by add_features, because those won't match
    #    (understandably)
    # fmt:off
    cols_to_drop = [col for col in to_be_flipped_step.columns if not (col.endswith("Z") or col.endswith("Y"))]
    for df in [to_be_flipped_step, to_not_be_flipped_step]:
        df.drop(columns=cols_to_drop, inplace=True)
    # fmt:on
    pdt.assert_frame_equal(to_be_flipped_step, to_not_be_flipped_step)


@sample_data_for_property_tests
def test_standardise_y_coordinates_no_gait_flipping(
    sample_step, extract_cfg, sample_steps_data
):
    extract_cfg["standardise_y_coordinates"] = True
    extract_cfg["flip_gait_direction"] = False
    y_cols = [col for col in sample_step.columns if col.endswith("Y")]
    # prep data
    # => because we are property testing, insert the hypothesis-generated data into the
    #    sample_step df (which has the correct columns)
    sample_step = pd.DataFrame(columns=sample_step.columns, data=sample_steps_data)
    non_stand_step, y_stand_step = standardise_y_z_flip_gait_add_features_to_one_step(
        sample_step, 10, extract_cfg
    )
    steps_y_min = (
        sample_step[extract_cfg["y_standardisation_joint"][0] + "Y"].min().min()
    )
    non_stand_step[y_cols] -= steps_y_min
    pdt.assert_frame_equal(non_stand_step, y_stand_step)


@sample_data_for_property_tests
def test_standardise_y_coordinates_gait_flipping(
    sample_step, extract_cfg, sample_steps_data
):
    # prep vars
    extract_cfg["standardise_y_coordinates"] = True
    extract_cfg["flip_gait_direction"] = True
    global_Y_max = 10
    y_cols = [col for col in sample_step.columns if col.endswith("Y")]
    # prep data
    # => because we are property testing, insert the hypothesis-generated data into the
    #    sample_step df (which has the correct columns)
    sample_step = pd.DataFrame(columns=sample_step.columns, data=sample_steps_data)
    # run function on a to-be-flipped step
    to_be_flipped_step = sample_step.copy()
    for col in y_cols:
        to_be_flipped_step[col] = to_be_flipped_step[col].sort_values(
            ascending=False, ignore_index=True
        )
    non_stand_step, y_stand_step = standardise_y_z_flip_gait_add_features_to_one_step(
        to_be_flipped_step, global_Y_max, extract_cfg
    )
    steps_y_min = (
        non_stand_step[extract_cfg["y_standardisation_joint"][0] + "Y"].min().min()
    )
    # pytest.set_trace()
    reverted_step = y_stand_step.copy()
    reverted_step[y_cols] += steps_y_min
    pdt.assert_frame_equal(reverted_step, non_stand_step)

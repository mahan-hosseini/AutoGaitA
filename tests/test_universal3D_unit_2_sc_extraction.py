from autogaita.universal3D.universal3D_1_preparation import some_prep
from autogaita.universal3D.universal3D_2_sc_extraction import (
    check_different_angle_joint_coords,
    check_tracking_nans,
    warn_about_nans_of_non_analysed_joints,
    get_analysed_coordinate_columns,
    extract_stepcycles,
)
from autogaita.universal3D.universal3D_3_analysis import analyse_and_export_stepcycles
from autogaita.universal3D.universal3D_constants import (
    SWINGSTART_COL,
    STANCEEND_COL,
    MAX_INTERPOLATE_NAN_FRAC,
)
from autogaita.resources.constants import ISSUES_TXT_FILENAME
import os
import pytest
import numpy as np
import pandas as pd

# %%................................  fixtures  ........................................


@pytest.fixture
def extract_data(extract_info, extract_folderinfo, extract_cfg):
    data, _ = some_prep(extract_info, extract_folderinfo, extract_cfg)
    return data


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
    cfg["sc_times_in_frames"] = False
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


@pytest.fixture
def create_a_frames_annotation_table(tmp_path, extract_cfg, extract_folderinfo):

    sampling_rate = extract_cfg["sampling_rate"]
    real_table_path = os.path.join(
        extract_folderinfo["root_dir"], extract_folderinfo["sctable_filename"]
    )
    SCdf = pd.read_excel(real_table_path, engine="openpyxl")

    subj_col = "Subject"
    swing_stance_cols = [
        col for col in SCdf.columns if SWINGSTART_COL in col or STANCEEND_COL in col
    ]
    # make sure that Runs col are ints otherwise it does not find
    runs_col = "Runs"

    # Filter rows belonging to TestSubject (subject cell + following blank-subject rows)
    in_subject_block = False
    rows_to_keep = []
    for _, row in SCdf.iterrows():
        cell_val = row[subj_col]
        if str(cell_val) == "TestSubject":
            in_subject_block = True
        elif not pd.isna(cell_val):
            in_subject_block = False
        if in_subject_block:
            rows_to_keep.append(row.copy())

    frames_df = pd.DataFrame(rows_to_keep, columns=SCdf.columns)

    # Convert only the swing/stance columns from seconds to frames
    for col in swing_stance_cols:
        frames_df[col] = frames_df[col].apply(
            lambda val: (
                int(round(float(val) * sampling_rate, 10)) if not pd.isna(val) else val
            )
        )

    table_path = tmp_path / "frames_SC_Latency_Table.xlsx"
    frames_df.to_excel(table_path, index=False, engine="openpyxl")
    return str(tmp_path), "frames_SC_Latency_Table.xlsx"


@pytest.fixture
def create_a_duplicate_ID_annotation_table(tmp_path, extract_folderinfo):
    """Copy the real Annotation Table but repeat TestSubject's ID on every row of
    their block instead of leaving it blank after the first row - mirrors a user
    filling in the ID column instead of using the blank-continuation-row
    convention. extract_stepcycles should auto-collapse this back to the normal
    format and produce identical all_cycles.
    """
    real_table_path = os.path.join(
        extract_folderinfo["root_dir"], extract_folderinfo["sctable_filename"]
    )
    SCdf = pd.read_excel(real_table_path, engine="openpyxl")

    subj_col = "Subject"
    # find all row-indices belonging to TestSubject's contiguous block (ID row +
    # all following blank-subject rows, up to but excluding the next subject)
    in_subject_block = False
    block_idxs = []
    for idx, row in SCdf.iterrows():
        cell_val = row[subj_col]
        if str(cell_val) == "TestSubject":
            in_subject_block = True
        elif not pd.isna(cell_val):
            in_subject_block = False
        if in_subject_block:
            block_idxs.append(idx)

    SCdf.loc[block_idxs, subj_col] = "TestSubject"  # repeat ID on every block row

    table_path = tmp_path / "duplicate_ID_SC_Latency_Table.xlsx"
    SCdf.to_excel(table_path, index=False, engine="openpyxl")
    return str(tmp_path), "duplicate_ID_SC_Latency_Table.xlsx"


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


# %%................... test NaN checks .............................................


def test_analysed_coordinate_columns_cover_both_legs_and_all_axes(
    extract_data, extract_cfg
):
    joints_before = list(extract_cfg["joints"])
    columns = get_analysed_coordinate_columns(extract_data, extract_cfg)
    # Midfoot, Ankle, Knee & Hip are bodyside-specific => 4 joints x 2 legs x XYZ
    assert len(columns) == 24
    assert "Hip, right X" in columns and "Midfoot, left Z" in columns
    assert "Pelvis Y" not in columns  # not a joint or angle joint in extract_cfg
    assert extract_cfg["joints"] == joints_before  # angle joints must not leak in


def test_clean_cycles_nan_removals(extract_data, extract_info, extract_cfg):
    """An SC is excluded only if an analysed joint is > MAX_INTERPOLATE_NAN_FRAC NaN
    within it - a single NaN is interpolated later and doesn't exclude the SC"""
    data = extract_data
    all_cycles = [[[111, 222], [333, 444]], [[555, 666], [777, 888]]]  # 112 frames
    # right leg's column excludes this (left leg's) SC too - both legs are analysed
    data.loc[111:140, "Knee, right Z"] = np.nan  # 30 / 112 = 27% NaN => exclude
    data.loc[111:150, "Hip, left Y"] = np.nan  # 40 / 112 = 36% NaN => exclude
    data.loc[444, "Ankle, left Y"] = np.nan  # 1 / 112 = 0.9% NaN => keep
    all_cycles = check_tracking_nans(
        all_cycles, data, extract_info, extract_cfg, "left"
    )
    assert all_cycles == [[[333, 444]], [[555, 666], [777, 888]]]
    with open(os.path.join(extract_info["results_dir"], ISSUES_TXT_FILENAME)) as f:
        content = f.read()
    assert "left leg - Run #1 - SC #1" in content
    # all offending columns are listed (in joint order), separated by "; "
    assert "NaN at Knee, right Z (26.8%); Hip, left Y (35.7%) - max" in content
    # removing all remaining SCs returns None (like check_different_angle_joint_coords)
    data.loc[300:900, "Hip, left X"] = np.nan
    assert (
        check_tracking_nans(all_cycles, data, extract_info, extract_cfg, "left") is None
    )


@pytest.mark.parametrize(
    "n_nan_frames, expected_cycles",
    [(10, [[[100, 199]]]), (11, None)],  # SC has 100 frames => 10% is still allowed
)
def test_clean_cycles_nan_fraction_boundary(
    n_nan_frames, expected_cycles, extract_data, extract_info, extract_cfg
):
    data = extract_data
    data.loc[100 : 100 + n_nan_frames - 1, "Midfoot, left Z"] = np.nan
    assert MAX_INTERPOLATE_NAN_FRAC == 0.1  # otherwise update n_nan_frames above
    clean_cycles = check_tracking_nans(
        [[[100, 199]]], data, extract_info, extract_cfg, "left"
    )
    assert clean_cycles == expected_cycles


def test_non_analysed_joint_nans_only_warn(
    extract_data, extract_info, extract_cfg, capsys
):
    """Pelvis is neither a joint nor an angle joint, so its NaNs must not exclude the SC
    - users must be warned though, but only about NaNs within remaining SCs"""
    data = extract_data
    data.loc[333:400, "Pelvis Z"] = np.nan  # 68 / 112 = 61% NaN
    data.loc[1000:1100, "Pelvis Y"] = np.nan  # outside of all SCs => no warning
    all_cycles = check_tracking_nans(
        [[[333, 444]]], data, extract_info, extract_cfg, "left"
    )
    assert all_cycles == [[[333, 444]]]
    capsys.readouterr()  # only check the warning's output below
    warn_about_nans_of_non_analysed_joints(
        {"left": all_cycles, "right": None}, data, extract_info, extract_cfg
    )
    assert "Pelvis Z" in capsys.readouterr().out
    with open(os.path.join(extract_info["results_dir"], ISSUES_TXT_FILENAME)) as f:
        content = f.read()
    assert "WARNING" in content and "Pelvis Z" in content
    assert "Pelvis Y" not in content


def test_nan_handling_from_sc_extraction_to_averages(
    extract_info, extract_folderinfo, extract_cfg
):
    """Set coordinates of TestSubject's data to NaN like marker dropouts would, then
    run SC extraction & analysis on it

    1. frames 0-249 & 1560-1608 (19% of the recording, outside of all SCs): all X/Y/Z
       are NaN => nothing is excluded because of them
    2. left run 1 SC 1 (303-396): 32% NaN in Knee, left Y (analysed) => excluded
    3. left run 2 SC 1 (747-851): 8% NaN in Ankle, right Z (analysed) => kept
    4. left run 3 SC 1 (1202-1312) & right run 3 SC 1 (1145-1257): up to 71% NaN in
       Skull Z (not analysed) => warning only
    => averages & SDs must not contain any NaN
    """
    data, global_Y_max = some_prep(extract_info, extract_folderinfo, extract_cfg)
    clean_cycles = extract_stepcycles(
        data.copy(), extract_info, extract_folderinfo, extract_cfg
    )
    # frames below were chosen for these SCs
    assert len(data) == 1609
    assert clean_cycles["left"][0][0] == [303, 396]
    assert clean_cycles["left"][1][0] == [747, 851]
    assert clean_cycles["left"][2][0] == [1202, 1312]
    assert clean_cycles["right"][2][0] == [1145, 1257]
    xyz_cols = [col for col in data.columns if col.endswith((" X", " Y", " Z"))]
    data.loc[0:249, xyz_cols] = np.nan
    data.loc[1560:1608, xyz_cols] = np.nan
    data.loc[303:332, "Knee, left Y"] = np.nan
    data.loc[780:787, "Ankle, right Z"] = np.nan
    data.loc[1202:1280, "Skull Z"] = np.nan

    # SC extraction - only left run 1 SC 1 is removed
    all_cycles = extract_stepcycles(data, extract_info, extract_folderinfo, extract_cfg)
    expected_cycles = clean_cycles
    expected_cycles["left"][0] = expected_cycles["left"][0][1:]
    assert all_cycles == expected_cycles
    with open(os.path.join(extract_info["results_dir"], ISSUES_TXT_FILENAME)) as f:
        issues = f.read()
    assert issues.count("Tracking failed") == 1
    assert "left leg - Run #1 - SC #1 - Tracking failed" in issues
    assert "NaN at Knee, left Y" in issues
    assert "Skull Z" in issues  # warning about the non-analysed joint

    # analysis - remaining NaNs are interpolated, so results must be NaN-free
    results = analyse_and_export_stepcycles(
        data, all_cycles, global_Y_max, extract_info, extract_cfg
    )
    n_clean_left_scs = sum(len(run_cycles) for run_cycles in clean_cycles["left"])
    assert results["left"]["sc_num"] == n_clean_left_scs  # (already 1 less, see above)
    for output in ["left", "right", "both"]:
        for key in ["average_data", "std_data"]:
            assert not results[output][key].isna().any().any(), f"NaN: {output} {key}"


# %%................... test sc_times_in_frames ...................................


def test_cycles_after_frames_times_matches_original_cycles(
    extract_data,
    extract_info,
    extract_folderinfo,
    extract_cfg,
    create_a_frames_annotation_table,
):
    os.makedirs(extract_info["results_dir"], exist_ok=True)

    data = extract_data

    # now run with frames-based table and assert identical output
    root_dir, sctable_filename = create_a_frames_annotation_table
    frames_cfg = extract_cfg.copy()
    frames_folderinfo = extract_folderinfo.copy()
    frames_cfg["sc_times_in_frames"] = True
    frames_folderinfo["root_dir"] = root_dir
    frames_folderinfo["sctable_filename"] = sctable_filename
    frames_cycles = extract_stepcycles(
        data, extract_info, frames_folderinfo, frames_cfg
    )

    # get expected cycles from the seconds-based path (ground truth)
    extract_cfg["sc_times_in_frames"] = False
    expected_cycles = extract_stepcycles(
        data, extract_info, extract_folderinfo, extract_cfg
    )

    assert frames_cycles == expected_cycles


def test_cycles_after_duplicate_ID_matches_original_cycles(
    extract_data,
    extract_info,
    extract_folderinfo,
    extract_cfg,
    create_a_duplicate_ID_annotation_table,
):
    """A table where TestSubject's ID is repeated (instead of left blank) on every
    row of their contiguous block must auto-collapse and produce identical
    all_cycles to the normal blank-formatted table.
    """
    os.makedirs(extract_info["results_dir"], exist_ok=True)

    data = extract_data

    expected_cycles = extract_stepcycles(
        data, extract_info, extract_folderinfo, extract_cfg
    )

    root_dir, sctable_filename = create_a_duplicate_ID_annotation_table
    duplicate_id_folderinfo = extract_folderinfo.copy()
    duplicate_id_folderinfo["root_dir"] = root_dir
    duplicate_id_folderinfo["sctable_filename"] = sctable_filename
    duplicate_id_cycles = extract_stepcycles(
        data, extract_info, duplicate_id_folderinfo, extract_cfg
    )

    assert duplicate_id_cycles == expected_cycles

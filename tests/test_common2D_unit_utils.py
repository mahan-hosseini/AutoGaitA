import pytest
from autogaita.common2D.common2D_utils import extract_info, find_number
import os
import pytest


# %%..............................  fixtures  ..........................................
# => CALL FIXTURES _fixture SINCE WE HAVE A FUNCTION CALLED extract_info!
@pytest.fixture
def fixture_extract_info(tmp_path):
    info = {}
    info["mouse_num"] = 15
    info["run_num"] = 3
    info["name"] = "ID " + str(info["mouse_num"]) + " - Run " + str(info["run_num"])
    info["results_dir"] = os.path.join(tmp_path, info["name"])
    return info


@pytest.fixture
def fixture_extract_folderinfo():
    folderinfo = {}
    folderinfo["root_dir"] = "tests/test_data/dlc_data"
    folderinfo["sctable_filename"] = (
        "correct_annotation_table.xlsx"  # has to be an excel file
    )
    folderinfo["data_string"] = "SIMINewOct"
    folderinfo["beam_string"] = "BeamTraining"
    folderinfo["premouse_string"] = "Mouse"
    folderinfo["postmouse_string"] = "_25mm"
    folderinfo["prerun_string"] = "run"
    folderinfo["postrun_string"] = "-6DLC"
    return folderinfo


@pytest.fixture
def fixture_extract_cfg():
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


# %%..............................  tests  ..........................................
# 1) Test extract_info function
def test_extract_info_function(fixture_extract_folderinfo):
    # => IT IS CORRECT THAT EXTRACT_INFO RETURNS lists of integers!
    # a. smoke test standard case
    info = extract_info("DLC", fixture_extract_folderinfo)
    assert info["mouse_num"] == [15]
    assert info["run_num"] == [3]
    # b. test that underscores/hyphens are added
    folderinfo = fixture_extract_folderinfo
    folderinfo["postmouse_string"] = "25mm"
    folderinfo["postrun_string"] = "6DLC"
    info = extract_info("DLC", folderinfo)
    assert info["mouse_num"] == [15]
    assert info["run_num"] == [3]
    # c. test that leading zeros are removed
    folderinfo["root_dir"] = "tests/test_data/dlc_data/test_data/leading_zeros/"
    info = extract_info("DLC", folderinfo)
    assert info["mouse_num"] == [12]
    assert info["run_num"] == [3]


# 2) Test find number function - also for leading zeros
def test_find_number_valid_case():
    fullstring = "Mouse1_Run002"
    prestring = "Mouse"
    poststring = "_Run"
    result = find_number(fullstring, prestring, poststring)
    assert result == (1, "")


def test_find_number_prestring_not_found():
    fullstring = "Mouse001_Run002"
    prestring = "Cat"
    poststring = "_Run"
    with pytest.raises(ValueError):
        find_number(fullstring, prestring, poststring)


def test_find_number_poststring_not_found():
    fullstring = "Mouse001_Run002"
    prestring = "Mouse"
    poststring = "_Walk"
    with pytest.raises(ValueError):
        find_number(fullstring, prestring, poststring)


def test_find_number_leading_zeros():
    fullstring = "Mouse001Run002"
    prestring = "Mouse"
    poststring = "Run"
    result = find_number(fullstring, prestring, poststring)
    assert result == (1, "00")

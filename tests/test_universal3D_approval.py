from autogaita.resources.utils import try_to_run_gaita
import pandas as pd
import pandas.testing as pdt
import os
import shutil
import pdb
import pytest


# ............................  SIMI APPROVAL TESTS STRUCTURE  .........................
# 1. Run autogaita.simi for Subject (with the cfg used there)
# 2. Load the "Average Stepcycles".xlsx file from the repo and compare for
#    equivalence to average_data
# 3. Do the same for "Standard Devs. Stepcycle.xlsx" and std_data
# 4. Pass the test if the two df-pairs are equal


# ...............................  PREPARE - FOUR FIXTURES   ...........................


@pytest.fixture
def extract_true_dir():
    return "tests/test_data/universal3D_data/true_data/"


@pytest.fixture
def extract_info(tmp_path):
    info = {}
    info["name"] = "TestSubject"
    info["results_dir"] = os.path.join(tmp_path, info["name"])
    return info


@pytest.fixture
def extract_folderinfo():
    folderinfo = {}
    folderinfo["root_dir"] = "tests/test_data/universal3D_data/test_data/"
    folderinfo["sctable_filename"] = "SC Latency Table"
    folderinfo["postname_string"] = ""
    return folderinfo


@pytest.fixture
def extract_cfg():
    cfg = {}
    cfg["sampling_rate"] = 100
    cfg["dont_show_plots"] = True
    cfg["y_acceleration"] = True
    cfg["angular_acceleration"] = True
    cfg["bin_num"] = 25
    cfg["plot_SE"] = True
    cfg["normalise_height_at_SC_level"] = True
    cfg["plot_joint_number"] = 7
    cfg["legend_outside"] = True
    cfg["color_palette"] = "viridis"
    cfg["analyse_average_y"] = False
    cfg["joints"] = ["Midfoot", "Ankle", "Knee", "Hip", "Pelvis "]
    cfg["angles"] = {
        "name": ["Ankle", "Knee", "Hip"],
        "lower_joint": ["Midfoot", "Ankle", "Knee"],
        "upper_joint": ["Knee", "Hip", "Pelvis "],
    }
    return cfg


# ...............................  RUN - ONE APPROVAL TEST  ............................


@pytest.mark.slow  # https://docs.pytest.org/en/7.1.x/example/markers.html
def test_universal3D_approval(
    extract_true_dir, extract_info, extract_folderinfo, extract_cfg
):
    # run
    try_to_run_gaita(
        "Universal 3D", extract_info, extract_folderinfo, extract_cfg, False
    )
    # load true dfs from xlsx files
    true_av_df = pd.read_excel(
        os.path.join(
            extract_true_dir, extract_info["name"] + " - Average Stepcycle.xlsx"
        )
    )
    true_std_df = pd.read_excel(
        os.path.join(
            extract_true_dir, extract_info["name"] + " - Standard Devs. Stepcycle.xlsx"
        )
    )
    # test dfs are results of current run above
    test_av_df = pd.read_excel(
        os.path.join(
            extract_info["results_dir"],
            extract_info["name"] + " - Average Stepcycle.xlsx",
        )
    )
    test_std_df = pd.read_excel(
        os.path.join(
            extract_info["results_dir"],
            extract_info["name"] + " - Standard Devs. Stepcycle.xlsx",
        )
    )
    # finally assert equivalence of df-pairs
    pdt.assert_frame_equal(test_av_df, true_av_df)
    pdt.assert_frame_equal(test_std_df, true_std_df)

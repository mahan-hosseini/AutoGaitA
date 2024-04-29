from autogaita import autogaita_utils
import pandas as pd
import pandas.testing as pdt
import os
import shutil
import pdb
import pytest


# .............................  1) GLOBAL VARS  .......................................
@pytest.mark.nodata  # https://docs.pytest.org/en/7.1.x/example/markers.html
def test_simi_approval(tmp_path):
    """
    Approval Test of AutoGaitA Simi
    -------------------------------
    1. Run autogaita.simi for Subject (with the cfg used there)
    2. Load the "Average Stepcycles".xlsx file from the repo and compare for equivalence to  average_data
    3. Do the same for "Standard Devs. Stepcycle.xlsx" and std_data
    4. Pass the test if the two df-pairs are equal
    """
    # prepare paths
    results_dir = tmp_path
    true_dir = "tests/test_data/simi_data/true_data/"
    test_dir = "tests/test_data/simi_data/test_data/"
    # folderinfo
    folderinfo = {}
    folderinfo["root_dir"] = test_dir
    folderinfo["sctable_filename"] = "SC Latency Table"
    folderinfo["postname_string"] = ""
    # cfg
    cfg = {}
    cfg["sampling_rate"] = 100
    cfg["dont_show_plots"] = False
    cfg["y_acceleration"] = True
    cfg["angular_acceleration"] = True
    cfg["bin_num"] = 25
    cfg["plot_SE"] = True
    cfg["normalise_height_at_SC_level"] = True
    cfg["plot_joint_number"] = 7
    cfg["joints"] = ["Midfoot", "Ankle", "Knee", "Hip", "Pelvis "]
    cfg["angles"] = {
        "name": ["Ankle", "Knee", "Hip"],
        "lower_joint": ["Midfoot", "Ankle", "Knee"],
        "upper_joint": ["Knee", "Hip", "Pelvis "],
    }
    # info
    info = {}
    info["name"] = "O_09"
    info["results_dir"] = os.path.join(results_dir, info["name"])

    # .............................  2) RUN TEST  ......................................

    # run
    autogaita_utils.try_to_run_gaita("Simi", info, folderinfo, cfg, False)
    # load true dfs from xlsx files
    true_av_df = pd.read_excel(os.path.join(true_dir, "O_09 - Average Stepcycle.xlsx"))
    true_std_df = pd.read_excel(
        os.path.join(true_dir, "O_09 - Standard Devs. Stepcycle.xlsx")
    )
    test_av_df = pd.read_excel(
        os.path.join(results_dir, "O_09/O_09 - Average Stepcycle.xlsx")
    )
    test_std_df = pd.read_excel(
        os.path.join(
            results_dir,
            "O_09/O_09 - Standard Devs. Stepcycle.xlsx",
        )
    )
    # finally assert equivalence of df-pairs
    pdt.assert_frame_equal(test_av_df, true_av_df)
    pdt.assert_frame_equal(test_std_df, true_std_df)

from autogaita import autogaita_utils
import pandas as pd
import pandas.testing as pdt
import os
import shutil
import pdb


# .............................  1) GLOBAL VARS  .......................................
def test_dlc_approval(tmp_path):
    """
    Approval Test of AutoGaitA DLC
    ------------------------------
    1. Run autogaita.dlc for ID 15 - Run 3 (with the cfg used there)
    2. Load the "Average Stepcycles".xlsx file from the repo and compare for equivalence to average_data
    3. Do the same for "Standard Devs. Stepcycle.xlsx" and std_data
    4. Pass the test if the two df-pairs are equal
    """

    # prepare paths
    results_dir = tmp_path  # info["results_dir"] below
    true_dir = "example data/25mm/Results/ID 15 - Run 3/"
    root_dir = "tests/test_data/dlc_data"
    # folderinfo
    folderinfo = {}
    folderinfo["root_dir"] = root_dir
    folderinfo["sctable_filename"] = "25mm.xlsx"  # has to be an excel file
    folderinfo["data_string"] = "SIMINewOct"
    folderinfo["beam_string"] = "BeamTraining"
    folderinfo["premouse_string"] = "Mouse"
    folderinfo["postmouse_string"] = "_25mm"
    folderinfo["prerun_string"] = "run"
    folderinfo["postrun_string"] = "-6DLC"
    # base cfg
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
    # info
    info = {}
    info["mouse_num"] = 15
    info["run_num"] = 3
    info["name"] = "ID " + str(info["mouse_num"]) + " - Run " + str(info["run_num"])
    info["results_dir"] = os.path.join(results_dir, info["name"])

    # .............................  2) RUN TEST  ......................................

    # run
    autogaita_utils.try_to_run_gaita("DLC", info, folderinfo, cfg, False)
    # load true dfs from xlsx files
    true_av_df = pd.read_excel(
        os.path.join(true_dir, "ID 15 - Run 3 - Average Stepcycle.xlsx")
    )
    true_std_df = pd.read_excel(
        os.path.join(true_dir, "ID 15 - Run 3 - Standard Devs. Stepcycle.xlsx")
    )
    test_av_df = pd.read_excel(
        os.path.join(
            results_dir, "ID 15 - Run 3/ID 15 - Run 3 - Average Stepcycle.xlsx"
        )
    )
    test_std_df = pd.read_excel(
        os.path.join(
            results_dir,
            "ID 15 - Run 3/ID 15 - Run 3 - Standard Devs. Stepcycle.xlsx",
        )
    )
    # finally assert equivalence of df-pairs
    pdt.assert_frame_equal(test_av_df, true_av_df)
    pdt.assert_frame_equal(test_std_df, true_std_df)

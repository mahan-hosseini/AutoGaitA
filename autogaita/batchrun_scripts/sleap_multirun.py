from autogaita.common2D.common2D_utils import extract_info, run_singlerun_in_multirun

# %% main function


def sleap_multirun():
    """
    Batchrun script to run AutoGaitA SLEAP for a folder of datasets.
    folderinfo & cfg dictionaries must be configured as explained in our documentation. See the "AutoGaitA without the GUI" section of our documentation for references to in-depth explanations to all dictionary keys (note that each key of dicts corresponds to some object in the AutoGaitA DLC GUI)
    """
    # folderinfo
    folderinfo = {}
    folderinfo["root_dir"] = "/Users/mahan/sciebo/Research/AutoGaitA/Frog Florina/"
    folderinfo["sctable_filename"] = "Frog Text Annotation Table"
    folderinfo["data_string"] = "En1"
    folderinfo["beam_string"] = ""
    folderinfo["premouse_string"] = "half_"
    folderinfo["postmouse_string"] = "stJuv"
    folderinfo["prerun_string"] = "stJuv_"
    folderinfo["postrun_string"] = "_1.mp4"

    # cfg
    cfg = {}
    cfg["sampling_rate"] = 60
    cfg["subtract_beam"] = False
    cfg["dont_show_plots"] = True
    cfg["convert_to_mm"] = False
    cfg["pixel_to_mm_ratio"] = 1
    cfg["x_sc_broken_threshold"] = 200  # optional cfg
    cfg["y_sc_broken_threshold"] = 50
    cfg["x_acceleration"] = True
    cfg["angular_acceleration"] = True
    cfg["save_to_xls"] = True
    cfg["bin_num"] = 25
    cfg["plot_SE"] = True
    cfg["standardise_y_at_SC_level"] = False
    cfg["standardise_y_to_a_joint"] = False
    cfg["y_standardisation_joint"] = ["Midfoot"]
    cfg["plot_joint_number"] = 5
    cfg["color_palette"] = "Set2"
    cfg["legend_outside"] = True
    cfg["invert_y_axis"] = True
    cfg["flip_gait_direction"] = False
    cfg["analyse_average_x"] = False
    cfg["standardise_x_coordinates"] = False
    cfg["x_standardisation_joint"] = ["Midfoot"]
    cfg["coordinate_standardisation_xls"] = ""
    cfg["sc_times_in_frames"] = False
    cfg["results_dir"] = ""
    cfg["hind_joints"] = [
        "Left_Foot",
        "Left_Ankle",
        "Left_Knee",
        "Left_Hip",
    ]
    cfg["fore_joints"] = []
    cfg["beam_col_left"] = []  # list of len == 1
    cfg["beam_col_right"] = []
    cfg["beam_hind_jointadd"] = []
    cfg["beam_fore_jointadd"] = []
    cfg["angles"] = {
        "name": ["Left_Ankle"],
        "lower_joint": ["Left_Foot"],
        "upper_joint": ["Left_Knee"],
    }
    # run a single gaita run for each entry of info
    info = extract_info("SLEAP", folderinfo)
    for idx in range(len(info["name"])):
        run_singlerun_in_multirun("SLEAP", idx, info, folderinfo, cfg)


# %% what happens if we just hit run
if __name__ == "__main__":
    sleap_multirun()

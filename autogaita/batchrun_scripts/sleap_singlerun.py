from autogaita.resources.utils import try_to_run_gaita
import os


# main function
def sleap_singlerun():
    """
    Batchrun script to run AutoGaitA SLEAP for a single dataset.
    folderinfo & cfg dictionaries must be configured as explained in our documentation. (note that each value of these corresponds to some object in the AutoGaitA Simi GUI)
    """
    # folderinfo
    folderinfo = {}
    folderinfo["root_dir"] = (
        "/Users/mahan/sciebo/Research/AutoGaitA/SLEAP/Human/Analysis/Old/"
    )
    folderinfo["results_dir"] = ""
    folderinfo["sctable_filename"] = "AnnotationTableOldSLEAP"
    folderinfo["data_string"] = ""
    folderinfo["beam_string"] = ""
    folderinfo["premouse_string"] = "Human"
    folderinfo["postmouse_string"] = "_Run"
    folderinfo["prerun_string"] = "Run"
    folderinfo["postrun_string"] = "_SLEAP"

    # cfg
    cfg = {}
    # 25 Hz sampling rate for SLEAP's example fly dataset (3000 frames @ 2 minutes)
    # https://github.com/talmolab/sleap/tree/main/docs/notebooks/analysis_example
    cfg["sampling_rate"] = 100
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
    cfg["plot_joint_number"] = 7
    cfg["color_palette"] = "viridis"
    cfg["legend_outside"] = True
    cfg["invert_y_axis"] = True
    cfg["flip_gait_direction"] = True
    cfg["analyse_average_x"] = False
    cfg["standardise_x_coordinates"] = False
    cfg["x_standardisation_joint"] = ["Midfoot"]
    cfg["hind_joints"] = ["Midfoot", "Ankle", "Knee", "Hip"]
    cfg["fore_joints"] = []
    cfg["beam_col_left"] = []  # list of len == 1
    cfg["beam_col_right"] = []
    cfg["beam_hind_jointadd"] = []
    cfg["beam_fore_jointadd"] = []
    cfg["angles"] = {
        "name": ["Ankle", "Knee"],
        "lower_joint": ["Midfoot", "Ankle"],
        "upper_joint": ["Knee", "Hip"],
    }

    # info
    info = {}
    info["mouse_num"] = 20
    info["run_num"] = 1
    info["name"] = "ID " + str(info["mouse_num"]) + " - Run " + str(info["run_num"])
    if folderinfo["results_dir"]:
        info["results_dir"] = os.path.join(folderinfo["results_dir"], info["name"])
    else:
        info["results_dir"] = os.path.join(
            folderinfo["root_dir"], "Results", info["name"]
        )
    # run
    try_to_run_gaita("SLEAP", info, folderinfo, cfg, False)


# %% what happens if we just hit run
if __name__ == "__main__":
    sleap_singlerun()

from autogaita import autogaita_utils
import os


# %% main function
def dlc_singlerun():
    """
    Batchrun script to run AutoGaitA DLC for a single dataset.
    folderinfo & cfg dictionaries must be configured as explained in our documentation. (note that each value of these corresponds to some object in the AutoGaitA DLC GUI)
    """
    # folderinfo
    folderinfo = {}
    folderinfo["root_dir"] = "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/Testing/"
    folderinfo["results_dir"] = ""
    folderinfo["sctable_filename"] = "25mm.xlsx"
    folderinfo["data_string"] = "SIMINewOct"
    folderinfo["beam_string"] = "BeamTraining"
    folderinfo["premouse_string"] = "Mouse"
    folderinfo["postmouse_string"] = "25mm"
    folderinfo["prerun_string"] = "run"
    folderinfo["postrun_string"] = "6DLC"
    # cfg
    cfg = {}
    cfg["sampling_rate"] = 100  # base cfg
    cfg["subtract_beam"] = True
    cfg["dont_show_plots"] = False
    cfg["convert_to_mm"] = True
    cfg["pixel_to_mm_ratio"] = 3.76
    cfg["x_sc_broken_threshold"] = 200  # optional cfg
    cfg["y_sc_broken_threshold"] = 50
    cfg["x_acceleration"] = True
    cfg["angular_acceleration"] = True
    cfg["save_to_xls"] = True
    cfg["bin_num"] = 25
    cfg["plot_SE"] = True
    cfg["normalise_height_at_SC_level"] = True
    cfg["plot_joint_number"] = 3
    cfg["color_palette"] = "viridis"
    cfg["legend_outside"] = True
    cfg["invert_y_axis"] = True
    cfg["flip_gait_direction"] = True
    cfg["export_average_x"] = True
    cfg["hind_joints"] = ["Hind paw tao", "Ankle", "Knee", "Hip", "Iliac Crest"]
    cfg["fore_joints"] = [
        "Front paw tao ",
        "Wrist ",
        "Elbow ",
        "Lower Shoulder ",
        "Upper Shoulder ",
    ]
    cfg["beam_col_left"] = ["BeamLeft"]  # list of len == 1
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
    info["mouse_num"] = 12
    info["run_num"] = 3
    info["name"] = "ID " + str(info["mouse_num"]) + " - Run " + str(info["run_num"])
    if folderinfo["results_dir"]:
        info["results_dir"] = os.path.join(folderinfo["results_dir"], info["name"])
    else:
        info["results_dir"] = os.path.join(
            folderinfo["root_dir"], "Results", info["name"]
        )
    # run
    autogaita_utils.try_to_run_gaita("DLC", info, folderinfo, cfg, False)


# %% what happens if we just hit run
if __name__ == "__main__":
    dlc_singlerun()

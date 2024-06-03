from autogaita import autogaita_utils
import os


# main function
def simi_singlerun():
    """
    Batchrun script to run AutoGaitA Simi for a single dataset.
    folderinfo & cfg dictionaries must be configured as explained in our documentation. (note that each value of these corresponds to some object in the AutoGaitA Simi GUI)
    """
    # folderinfo
    folderinfo = {}
    folderinfo["root_dir"] = "/Users/mahan/sciebo/Research/AutoGaitA/Human/Testing2/"
    folderinfo["results_dir"] = ""
    folderinfo["sctable_filename"] = "SC Latency Table"
    folderinfo["postname_string"] = ""
    # cfg
    cfg = {}
    cfg["sampling_rate"] = 100  # base cfg
    cfg["dont_show_plots"] = False
    cfg["y_acceleration"] = True
    cfg["angular_acceleration"] = True
    cfg["bin_num"] = 25
    cfg["plot_SE"] = True
    cfg["normalise_height_at_SC_level"] = True
    cfg["plot_joint_number"] = 7
    cfg["export_average_y"] = False
    cfg["joints"] = ["Midfoot", "Ankle", "Knee", "Hip", "Pelvis", "Shoulder", "Neck"]
    cfg["angles"] = {
        "name": ["Ankle", "Knee"],
        "lower_joint": ["Midfoot", "Ankle"],
        "upper_joint": ["Knee", "Hip"],
    }
    # info
    info = {}
    info["name"] = "SK"  # analyse this dataset
    if folderinfo["results_dir"]:
        info["results_dir"] = os.path.join(folderinfo["results_dir"], info["name"])
    else:
        info["results_dir"] = os.path.join(
            folderinfo["root_dir"], "Results", info["name"]
        )
    # run
    autogaita_utils.try_to_run_gaita("Simi", info, folderinfo, cfg, False)


# %% what happens if we just hit run
if __name__ == "__main__":
    simi_singlerun()

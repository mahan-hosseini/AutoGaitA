from autogaita.resources.utils import try_to_run_gaita
import os


# main function
def universal3D_singlerun():
    """
    Batchrun script to run AutoGaitA Universal 3D for a single dataset.
    folderinfo & cfg dictionaries must be configured as explained in our documentation. (note that each value of these corresponds to some object in the AutoGaitA Universal 3D GUI)
    """
    # folderinfo
    folderinfo = {}
    folderinfo["root_dir"] = "/Users/mahan/sciebo/Research/AutoGaitA/Human/Testing2/"
    # folderinfo["root_dir"] = "/Users/mahan/sciebo/Research/AutoGaitA/Fly/3D Data/"
    folderinfo["results_dir"] = ""
    folderinfo["sctable_filename"] = "SC Latency Table"
    folderinfo["postname_string"] = ""
    # cfg
    cfg = {}
    cfg["sampling_rate"] = 100  # base cfg
    cfg["dont_show_plots"] = True
    cfg["y_acceleration"] = True
    cfg["angular_acceleration"] = True
    cfg["bin_num"] = 25
    cfg["plot_SE"] = True
    cfg["standardise_z_at_SC_level"] = True
    cfg["standardise_z_to_a_joint"] = True
    cfg["z_standardisation_joint"] = ["Midfoot, left"]
    cfg["plot_joint_number"] = 5
    cfg["color_palette"] = "Set2"
    cfg["legend_outside"] = True
    cfg["flip_gait_direction"] = True
    cfg["analyse_average_y"] = True
    cfg["standardise_y_coordinates"] = True
    cfg["y_standardisation_joint"] = ["Midfoot, left"]
    cfg["coordinate_standardisation_xls"] = ""
    cfg["joints"] = [
        # "R1-ThCx",
        "Midfoot",
        "Ankle",
        "Knee",
        "Hip",
        "Pelvis",
        "Shoulder",
        "Neck",
    ]
    cfg["angles"] = {
        "name": ["Ankle", "Knee"],
        "lower_joint": ["Midfoot", "Ankle"],
        "upper_joint": ["Knee", "Hip"],
    }
    # info
    info = {}
    info["name"] = "SK"  # "A1"  #  # analyse this dataset
    if folderinfo["results_dir"]:
        info["results_dir"] = os.path.join(folderinfo["results_dir"], info["name"])
    else:
        info["results_dir"] = os.path.join(
            folderinfo["root_dir"], "Results", info["name"]
        )
    # run
    try_to_run_gaita("Universal 3D", info, folderinfo, cfg, False)


# %% what happens if we just hit run
if __name__ == "__main__":
    universal3D_singlerun()

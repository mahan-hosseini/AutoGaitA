from autogaita import autogaita_utils
import os
import pdb


# %% main function


def simi_multirun():
    """
    Batchrun script to run AutoGaitA Simi for a folder of datasets.
    folderinfo & cfg dictionaries must be configured as explained in our documentation. See the "AutoGaitA without the GUI" section of our documentation for references to in-depth explanations to all dictionary keys (note that each key of dicts corresponds to some object in the AutoGaitA Simi GUI)
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
    cfg["color_palette"] = "viridis"
    cfg["legend_outside"] = True
    cfg["export_average_y"] = False
    cfg["joints"] = ["Midfoot", "Ankle", "Knee", "Hip", "Pelvis", "Shoulder", "Neck"]
    cfg["angles"] = {
        "name": ["Ankle", "Knee"],
        "lower_joint": ["Midfoot", "Ankle"],
        "upper_joint": ["Knee", "Hip"],
    }
    # run a single gaita run for each entry of info
    info = extract_info(folderinfo)
    for idx, name in enumerate(info["name"]):
        run_singlerun(idx, info, folderinfo, cfg)


# %% local functions


def run_singlerun(idx, info, folderinfo, cfg):
    """Run the main code of individual run-analyses based on current cfg"""
    # extract and pass info of this mouse/run (also update resdir)
    this_info = {}
    keynames = info.keys()
    for keyname in keynames:
        this_info[keyname] = info[keyname][idx]
    # important to only pass this_info to main script here (1 run at a time!)
    autogaita_utils.try_to_run_gaita("Simi", this_info, folderinfo, cfg, True)


def extract_info(folderinfo):
    """Prepare a dict of lists that include unique name infos"""
    root_dir = folderinfo["root_dir"]
    results_dir = folderinfo["results_dir"]
    sctable_filename = folderinfo["sctable_filename"]
    postname_string = folderinfo["postname_string"]
    info = {"name": [], "results_dir": []}
    for filename in os.listdir(root_dir):
        # dont try to combine the two "join" if blocks into one - we want to append
        # results dir WHENEVER we append name!
        if not postname_string:
            # dont use endswith below to catch .xlsx too
            if (".xls" in filename) & (sctable_filename not in filename):
                info["name"].append(filename.split(".xls")[0])
                if results_dir:
                    info["results_dir"].append(
                        os.path.join(results_dir, info["name"][-1])
                    )
                else:
                    info["results_dir"].append(
                        os.path.join(root_dir, "Results", info["name"][-1])
                    )
        else:
            if postname_string in filename:
                info["name"].append(filename.split(postname_string)[0])
                if results_dir:
                    info["results_dir"].append(
                        os.path.join(results_dir, info["name"][-1])
                    )
                else:
                    info["results_dir"].append(
                        os.path.join(root_dir, "Results", info["name"][-1])
                    )
    return info


# %% what happens if we just hit run
if __name__ == "__main__":
    simi_multirun()

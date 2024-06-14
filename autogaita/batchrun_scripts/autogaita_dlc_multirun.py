from autogaita import autogaita_utils
import os
import pdb

# %% main function


def dlc_multirun():
    """
    Batchrun script to run AutoGaitA DLC for a folder of datasets.
    folderinfo & cfg dictionaries must be configured as explained in our documentation. See the "AutoGaitA without the GUI" section of our documentation for references to in-depth explanations to all dictionary keys (note that each key of dicts corresponds to some object in the AutoGaitA DLC GUI)
    """
    # folderinfo
    folderinfo = {}
    folderinfo["root_dir"] = "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/Testing/"
    folderinfo["results_dir"] = ""
    folderinfo["sctable_filename"] = "25mm.xlsx"
    folderinfo["data_string"] = "SIMINewOct"
    folderinfo["beam_string"] = "BeamTraining"
    folderinfo["premouse_string"] = "Mouse"
    folderinfo["postmouse_string"] = "_25mm"
    folderinfo["prerun_string"] = "run"
    folderinfo["postrun_string"] = "-6DLC"
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
    # run a single gaita run for each entry of info
    info = extract_info(folderinfo)
    for idx in range(len(info["name"])):
        run_singlerun(idx, info, folderinfo, cfg)


# %% local functions


def run_singlerun(idx, info, folderinfo, cfg):
    """Run the main code of individual run-analyses based on current cfg"""
    # extract and pass info of this mouse/run (also update resdir)
    this_info = {}
    keynames = info.keys()
    for keyname in keynames:
        this_info[keyname] = info[keyname][idx]
        if folderinfo["results_dir"]:
            this_info["results_dir"] = os.path.join(
                folderinfo["results_dir"], this_info["name"]
            )
        else:
            this_info["results_dir"] = os.path.join(
                folderinfo["root_dir"], "Results", this_info["name"]
            )
    # important to only pass this_info to main script here (1 run at a time!)
    autogaita_utils.try_to_run_gaita("DLC", this_info, folderinfo, cfg, True)


def extract_info(folderinfo):
    """Prepare a dict of lists that include unique name/mouse/run infos"""
    premouse_string = folderinfo["premouse_string"]
    postmouse_string = folderinfo["postmouse_string"]
    prerun_string = folderinfo["prerun_string"]
    postrun_string = folderinfo["postrun_string"]
    info = {"name": [], "mouse_num": [], "run_num": []}
    for filename in os.listdir(folderinfo["root_dir"]):
        if (
            (premouse_string in filename)  # make sure we don't get wrong files
            & (prerun_string in filename)
            & (filename.endswith(".csv"))
        ):
            # we can use COUNT vars as we do here, since we start @ 0 and do
            # not include the last index (so if counts=2, idx=[0:2]=include
            # 0&1 only!)
            this_mouse_num = find_number(filename, premouse_string, postmouse_string)
            this_run_num = find_number(filename, prerun_string, postrun_string)
            this_name = "ID " + str(this_mouse_num) + " - Run " + str(this_run_num)
            if this_name not in info["name"]:  # no data/beam duplicates here
                info["name"].append(this_name)
                info["mouse_num"].append(this_mouse_num)
                info["run_num"].append(this_run_num)
    return info


def find_number(fullstring, prestring, poststring):
    """Find (mouse/run) number based on user-defined strings in filenames"""
    start_idx = fullstring.find(prestring) + len(prestring)
    end_idx = fullstring.find(poststring)
    return int(fullstring[start_idx:end_idx])


# %% what happens if we just hit run
if __name__ == "__main__":
    dlc_multirun()

from autogaita.core2D.core2D_constants import FILE_ID_STRING_ADDITIONS
from autogaita.gaita_res.utils import try_to_run_gaita
import os
import tkinter as tk


def run_singlerun_in_multirun(idx, info, folderinfo, cfg):
    """When performing a multirun, either via Batch Analysis in GUI or batchrun scripts dlc.multirun, run the analysis for a given dataset"""
    # extract and pass info of this mouse/run (also update resdir)
    this_info = {}
    keynames = info.keys()
    for keyname in keynames:
        this_info[keyname] = info[keyname][idx]
        if cfg["results_dir"]:
            this_info["results_dir"] = os.path.join(
                cfg["results_dir"], this_info["name"]
            )
        else:
            this_info["results_dir"] = os.path.join(
                folderinfo["root_dir"], "Results", this_info["name"]
            )
    # important to only pass this_info to main script here (1 run at a time!)
    try_to_run_gaita("DLC", this_info, folderinfo, cfg, True)


def extract_info(folderinfo, in_GUI=False):
    """Prepare a dict of lists that include unique name/mouse/run infos"""

    # unpack
    premouse_string = folderinfo["premouse_string"]
    postmouse_string = folderinfo["postmouse_string"]
    prerun_string = folderinfo["prerun_string"]
    postrun_string = folderinfo["postrun_string"]

    # prepare output info dict and run
    info = {"name": [], "mouse_num": [], "run_num": []}
    for filename in os.listdir(folderinfo["root_dir"]):
        # make sure we don't get wrong files
        if (
            (premouse_string in filename)
            & (prerun_string in filename)
            & (filename.endswith(".csv"))
        ):
            # ID number - fill in "_" for user if needed
            this_mouse_num = False
            for string_addition in FILE_ID_STRING_ADDITIONS:
                try:
                    candidate_postmouse_string = string_addition + postmouse_string
                    this_mouse_num = find_number(
                        filename,
                        premouse_string,
                        candidate_postmouse_string,
                    )
                except:
                    pass
            if this_mouse_num is False:
                no_ID_num_found_msg = (
                    "Unable to extract ID numbers from file identifiers! "
                    + "Check unique subject [B] and unique task [C] identifiers"
                )
                # if we're in the GUI, show an error message & stop here
                if in_GUI:
                    tk.messagebox.showerror(
                        title="No ID number found!", message=no_ID_num_found_msg
                    )
                    return
            # Do the same for run number
            this_run_num = False
            for string_addition in FILE_ID_STRING_ADDITIONS:
                try:
                    candidate_postrun_string = string_addition + postrun_string
                    this_run_num = find_number(
                        filename, prerun_string, candidate_postrun_string
                    )
                except:
                    pass
            if this_run_num is False:
                no_run_num_found_msg = (
                    "Unable to extract trial numbers from file identifiers! "
                    + "Check unique trial [D] and unique camera [E] identifiers"
                )
                if in_GUI:
                    tk.messagebox.showerror(
                        title="No Trial number found!", message=no_run_num_found_msg
                    )
                    return
            # if we found both an ID and a run number, create this_name & add to dict
            if this_mouse_num and this_run_num:  # are truthy since not False if found
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

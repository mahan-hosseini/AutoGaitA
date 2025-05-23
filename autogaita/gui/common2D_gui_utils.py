import os
import tkinter as tk
from threading import Thread
from autogaita.common2D.common2D_utils import run_singlerun_in_multirun, extract_info
from autogaita.resources.utils import try_to_run_gaita

# %%..........  functions preparing and calling runs of 2D autogaita  ..................


def runanalysis(tracking_software, analysis, this_runs_results, this_runs_cfg):
    """Run the main program"""
    if analysis == "single":
        run_thread = Thread(
            target=analyse_single_run,
            args=(tracking_software, this_runs_results, this_runs_cfg),
        )
    elif analysis == "multi":
        run_thread = Thread(
            target=analyse_multi_run,
            args=(tracking_software, this_runs_results, this_runs_cfg),
        )
    run_thread.start()


def analyse_single_run(tracking_software, this_runs_results, this_runs_cfg):
    """Prepare for one execution of autogaita_dlc & execute"""
    # prepare (folderinfo first to handle root_dir "/" issue if needed)
    folderinfo = prepare_folderinfo(this_runs_results)
    if folderinfo is None:
        error_msg = (
            "No directory found at: " + this_runs_results["root_dir"] + " - try again!"
        )
        tk.messagebox.showerror(title="Try again", message=error_msg)
        print(error_msg)
        return
    info = {}  # info dict: run-specific info
    info["mouse_num"] = this_runs_results["mouse_num"]
    info["run_num"] = this_runs_results["run_num"]
    info["name"] = "ID " + str(info["mouse_num"]) + " - Run " + str(info["run_num"])
    if this_runs_cfg["results_dir"]:
        info["results_dir"] = os.path.join(this_runs_cfg["results_dir"], info["name"])
    else:
        info["results_dir"] = os.path.join(
            folderinfo["root_dir"], "Results", info["name"]
        )
    # execute
    try_to_run_gaita(tracking_software, info, folderinfo, this_runs_cfg, False)


def analyse_multi_run(tracking_software, this_runs_results, this_runs_cfg):
    """Prepare for multi-execution of autogaita_dlc & loop-execute"""
    # prepare (folderinfo first to handle root_dir "/" issue if needed)
    folderinfo = prepare_folderinfo(this_runs_results)
    if folderinfo is None:
        error_msg = (
            "No directory found at: " + this_runs_results["root_dir"] + " - try again!"
        )
        tk.messagebox.showerror(title="Try again", message=error_msg)
        print(error_msg)
        return
    # folderinfo has info of individual runs - extract individual runs info
    # => tracking_software because of file_type - else identical
    info = extract_info(tracking_software, folderinfo, in_GUI=True)
    # this can fail for DLC which will return None - use this to handle the error and
    # stop execution
    if info is None:
        return
    # if there was no error, loop through individual runs
    for idx in range(len(info["name"])):
        run_singlerun_in_multirun(
            tracking_software, idx, info, folderinfo, this_runs_cfg
        )


def prepare_folderinfo(this_runs_results):
    # IMPORTANT NOTE
    # This function should only return None if there are issues with root_dir
    # since we handle the error in outside functions because of this (i.e. the meaning
    # behind the None should NOT change in the future!)
    if len(this_runs_results["root_dir"]) == 0:
        return
    folderinfo = {}
    folderinfo["root_dir"] = this_runs_results["root_dir"]
    # to make sure root_dir works under windows
    # (windows is okay with all dir-separators being "/", so make sure it is!)
    folderinfo["root_dir"] = folderinfo["root_dir"].replace(os.sep, "/")
    if folderinfo["root_dir"][-1] != "/":
        folderinfo["root_dir"] = folderinfo["root_dir"] + "/"
    if not os.path.exists(folderinfo["root_dir"]):
        return
    folderinfo["sctable_filename"] = this_runs_results["sctable_filename"]
    folderinfo["data_string"] = this_runs_results["data_string"]
    folderinfo["beam_string"] = this_runs_results["beam_string"]
    folderinfo["premouse_string"] = this_runs_results["premouse_string"]
    folderinfo["postmouse_string"] = this_runs_results["postmouse_string"]
    folderinfo["prerun_string"] = this_runs_results["prerun_string"]
    folderinfo["postrun_string"] = this_runs_results["postrun_string"]
    return folderinfo


# %%...............  important function getting values from tk vars  ...................


def get_results_and_cfg(results, cfg, analysis, variable_dict):
    """Before calling analysis, use .get() to extract values from tk-vars"""

    # unpack var dict
    FLOAT_VARS = variable_dict["FLOAT_VARS"]
    INT_VARS = variable_dict["INT_VARS"]
    LIST_VARS = variable_dict["LIST_VARS"]
    DICT_VARS = variable_dict["DICT_VARS"]

    # 1) We make sure to return and use for all "run"-purposes (i.e. everything
    #    that follows this local function) "this_" dicts (stuff is dangerous
    #    otherwise!)
    # 2) I implemented the usage & transformation of FLOAT_&INT_VARS the way I
    #    do here (instead of initialising as (e.g.) tk.IntVar because otherwise
    #    tkinter complains whenever an Entry is empty @ any time, just because
    #    the user is inputting their values.
    output_dicts = [{}, {}]
    for i in range(len(output_dicts)):
        if i == 0:
            input_dict = results
        elif i == 1:
            input_dict = cfg
        for key in input_dict.keys():
            # exclude mouse_num and run_num from int conversion
            # in case analysis is multi
            if analysis == "multi" and (key == "mouse_num" or key == "run_num"):
                output_dicts[i][key] = input_dict[key].get()
            elif key in FLOAT_VARS:
                # make sure that if user doesn't want to convert then we just use 0 so
                # the float() statement doesn't throw an error
                # => set the outer dict directly instead of modulating the input_dict,
                #    since that would also modify cfg which might be dangerous for
                #    future runs
                if (key == "pixel_to_mm_ratio") & (cfg["convert_to_mm"].get() is False):
                    output_dicts[i][key] = 0
                else:
                    try:
                        output_dicts[i][key] = float(input_dict[key].get())
                    except ValueError:
                        return (
                            key
                            + " value was not a decimal number, but "
                            + input_dict[key].get()
                        )
            elif key in INT_VARS:
                try:
                    output_dicts[i][key] = int(input_dict[key].get())
                except ValueError:
                    return (
                        key
                        + " value was not an integer number, but "
                        + input_dict[key].get()
                    )
            elif key in LIST_VARS:
                # if list of strings, initialise output empty list and get & append vals
                output_dicts[i][key] = []
                for list_idx in range(len(input_dict[key])):
                    output_dicts[i][key].append(input_dict[key][list_idx].get())
            elif key in DICT_VARS:
                # if dict of list of strings, initialise as empty dict and assign stuff
                # key = "angles" or other DICT_VAR
                # inner_key = "name" & "lower_ / upper_joint"
                # list_idx = idx of list of strings of inner_key
                output_dicts[i][key] = {}
                for inner_key in input_dict[key]:
                    output_dicts[i][key][inner_key] = []
                    for list_idx in range(len(input_dict[key][inner_key])):
                        output_dicts[i][key][inner_key].append(
                            input_dict[key][inner_key][list_idx].get()
                        )
            else:
                output_dicts[i][key] = input_dict[key].get()
    this_runs_results = output_dicts[0]
    this_runs_cfg = output_dicts[1]
    return this_runs_results, this_runs_cfg

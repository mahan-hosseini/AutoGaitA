# %% imports
from autogaita.common2D.common2D_constants import FILE_ID_STRING_ADDITIONS
from autogaita.resources.utils import try_to_run_gaita, write_issues_to_textfile
import os
import copy
import numpy as np
import tkinter as tk

# %% constants
from autogaita.resources.constants import TIME_COL


def run_singlerun_in_multirun(tracking_software, idx, info, folderinfo, cfg):
    """When performing a multirun, either via Batch Analysis in GUI or batchrun scripts, run the analysis for a given dataset"""
    # extract and pass info of this mouse/run or name (also update resdir)
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
    # make a deep copy of cfg that used in each run, otherwise changes to the cfg dict
    # would translate to subsequent runs
    # ==> see https://stackoverflow.com/questions/2465921/
    #         how-to-copy-a-dictionary-and-only-edit-the-copy
    this_cfg = copy.deepcopy(cfg)
    # important to only pass this_info to main script here (1 run at a time!)
    try_to_run_gaita(tracking_software, this_info, folderinfo, this_cfg, True)


def extract_info(tracking_software, folderinfo, in_GUI=False):
    """Prepare a dict of lists that include unique infos for each dataset in a folder"""

    # unpack
    root_dir = folderinfo["root_dir"]
    premouse_string = folderinfo["premouse_string"]
    postmouse_string = folderinfo["postmouse_string"]
    prerun_string = folderinfo["prerun_string"]
    postrun_string = folderinfo["postrun_string"]
    # IMPORTANT
    # ---------
    # different file types based on which software did the tracking!
    if tracking_software == "DLC":
        file_type = ".csv"
    elif tracking_software == "SLEAP":
        file_type = ".h5"
    # prepare output info dict and run
    info = {"name": [], "mouse_num": [], "run_num": []}
    for filename in os.listdir(folderinfo["root_dir"]):
        # make sure we don't get wrong files
        if (
            (premouse_string in filename)
            & (prerun_string in filename)
            & (filename.endswith(file_type))
        ):
            # ID number - fill in "_" for user if needed
            this_mouse_num = False
            for string_addition in FILE_ID_STRING_ADDITIONS:
                try:
                    candidate_postmouse_string = string_addition + postmouse_string
                    this_mouse_num, leading_mouse_num_zeros = find_number(
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
                    this_run_num, leading_run_num_zeros = find_number(
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
    # if we had to fix leading zeros, make sure to save them so we can use them in
    # move_data_to_folders function later
    # => make sure it's lists of strings because this is needed by the
    #    run_singlerun_in_multiruns function later
    if leading_mouse_num_zeros:
        info["leading_mouse_num_zeros"] = [leading_mouse_num_zeros]
    if leading_run_num_zeros:
        info["leading_run_num_zeros"] = [leading_run_num_zeros]
    # this might happen if user entered wrong identifiers or folder
    if len(info["name"]) < 1:
        no_files_message = (
            f"Unable to find any files at {root_dir}!" + "\ncheck your inputs!"
        )
        if in_GUI:
            tk.messagebox.showerror(
                title="No files found!",
                message=no_files_message,
            )
        else:
            print(no_files_message)
    return info

    # SLEAP BACKUP
    # => Note this previously was taking tracking_software input back when SLEAP was
    #    not identical to DLC - keep this here in case you need it at some point (note
    #    there is another return info below this)
    # elif tracking_software == "SLEAP":
    #     # unpack
    #     root_dir = folderinfo["root_dir"]
    #     data_string = folderinfo["data_string"]
    #     # prepare output info dict and run
    #     info = {"name": []}
    #     for filename in os.listdir(root_dir):
    #         if data_string + ".csv" in filename:
    #             info["name"].append(filename.split(data_string + ".csv")[0])
    #         if data_string + ".h5" in filename:
    #             info["name"].append(filename.split(data_string + ".h5")[0])
    #     info["name"] = list(set(info["name"]))  # no duplicates
    # return info


def find_number(fullstring, prestring, poststring):
    """Find (mouse/run) number based on user-defined strings in filenames"""
    start_idx = fullstring.find(prestring) + len(prestring)
    end_idx = fullstring.find(poststring)
    # handle leading zeros
    leading_zeros = ""
    while fullstring[start_idx] == "0" and start_idx < end_idx - 1:
        start_idx += 1
        leading_zeros += "0"
    return int(fullstring[start_idx:end_idx]), leading_zeros


# ...........................  SC extraction helpers  ..................................
def check_cycle_out_of_bounds(all_cycles):
    """Check if user provided SC latencies that were not in video/data bounds"""
    clean_cycles = None
    for cycle in all_cycles:
        # below checks if values are any type of int (just in case this should
        # for some super random reason change...)
        if isinstance(cycle[0], (int, np.integer)) & isinstance(
            cycle[1], (int, np.integer)
        ):
            if clean_cycles is None:
                clean_cycles = []
            clean_cycles.append(cycle)
    return clean_cycles


def check_cycle_duplicates(all_cycles):
    """Check if there are any duplicate SC latencies.
    This would break our plotting functions, which use .loc on all_steps_data - thus,
    all indices of all_cycles have to be unique. If any duplicates found, add one
    datapoint to the start latency.
    """
    for c, cycle in enumerate(all_cycles):
        if c > 0:
            if cycle[0] == all_cycles[c - 1][1]:
                all_cycles[c][0] += 1
    return all_cycles


def check_cycle_order(all_cycles, info):
    """Check if user input flawed SC latencies

    Two cases
    1. Start latency earlier than end latency of previous SC
    2. End latency earlier then start latency of current SC
    """
    clean_cycles = []
    current_max_time = 0
    for c, cycle in enumerate(all_cycles):
        if cycle[0] > current_max_time:
            if cycle[1] > cycle[0]:
                clean_cycles.append(cycle)  # only append if both tests passed
                current_max_time = cycle[1]
            else:
                this_message = (
                    "\n***********\n! WARNING !\n***********\n"
                    + "SC #"
                    + str(c + 1)
                    + " has a later start than end latency - Skipping!"
                )
                print(this_message)
                write_issues_to_textfile(this_message, info)
        else:
            this_message = (
                "\n***********\n! WARNING !\n***********\n"
                + "SC #"
                + str(c + 1)
                + " has an earlier start than previous SC's end latency - Skipping!"
            )
            print(this_message)
            write_issues_to_textfile(this_message, info)
    return clean_cycles


def check_differing_angle_joint_coords(all_cycles, data, info, cfg):
    """Check if none of the joints used for angle computations later have equal values (since this would lead to math.domain errors due to floating point precision)"""

    # Note
    # ----
    # In theory, I could fix this programatically in the add_angle function, but I feel
    # like joint-coords should not often be exactly equal like this in a meaningful way
    # We can still change it in the future.

    # unpack
    angles = cfg["angles"]

    clean_cycles = None
    for c, cycle in enumerate(all_cycles):  # for each SC
        cycle = check_a_single_cycle_for_joint_coords(cycle, angles, data, c, info)
        if cycle:  # if cycle was not valid (equal-joint-coords) this returns None
            if clean_cycles == None:
                clean_cycles = [cycle]  # also makes a 2xscs list of lists
            else:
                clean_cycles.append(cycle)
    return clean_cycles


def check_a_single_cycle_for_joint_coords(cycle, angles, data, c, info):
    for a in range(len(angles["name"])):  # for each angle configuration
        # prepare a dict that has only the data of this angle config's joints
        this_angle_data = {"name": [], "lower_joint": [], "upper_joint": []}
        for key in this_angle_data.keys():
            this_joint = angles[key][a]
            this_angle_data[key] = np.array(
                [data[this_joint + "x"], data[this_joint + "y"]]
            )
        # now check if any of the joints have the same coord at any idx
        for idx in range(cycle[0], cycle[1]):
            if (
                np.array_equal(
                    this_angle_data["name"][:, idx],
                    this_angle_data["lower_joint"][:, idx],
                )
                or np.array_equal(
                    this_angle_data["name"][:, idx],
                    this_angle_data["upper_joint"][:, idx],
                )
                or np.array_equal(
                    this_angle_data["lower_joint"][:, idx],
                    this_angle_data["upper_joint"][:, idx],
                )
            ):
                this_message = (
                    "\n***********\n! WARNING !\n***********\n"
                    + f"SC #{c + 1} has equal joint coordinates at "
                    + f"{round(data[TIME_COL][idx],4)}s:"
                    + "\n\nAngle - [x y]:\n"
                    + angles["name"][a]
                    + " - "
                    + str(this_angle_data["name"][:, idx])
                    + "\nLower joint: "
                    + angles["lower_joint"][a]
                    + " - "
                    + str(this_angle_data["lower_joint"][:, idx])
                    + "\nUpper joint: "
                    + angles["upper_joint"][a]
                    + " - "
                    + str(this_angle_data["upper_joint"][:, idx])
                    + "\nRemoving the SC from "
                    + f"{round(data[TIME_COL][cycle[0]], 4)}-"
                    + f"{round(data[TIME_COL][cycle[1]], 4)}s"
                )
                print(this_message)
                write_issues_to_textfile(this_message, info)
                return None  # removes this SC
    return cycle  # if we never returned None, this SC is valid


def check_tracking_xy_thresholds(all_cycles, data, info, cfg):
    """Check if any x/y column of any joint has broken datapoints"""
    # unpack
    convert_to_mm = cfg["convert_to_mm"]
    x_sc_broken_threshold = cfg["x_sc_broken_threshold"]
    y_sc_broken_threshold = cfg["y_sc_broken_threshold"]
    pixel_to_mm_ratio = cfg["pixel_to_mm_ratio"]
    hind_joints = cfg["hind_joints"]
    if convert_to_mm:
        x_sc_broken_threshold = x_sc_broken_threshold / pixel_to_mm_ratio
        y_sc_broken_threshold = y_sc_broken_threshold / pixel_to_mm_ratio
    columns = []
    clean_cycles = None
    for joint in hind_joints:
        columns.append(joint + "x")
        columns.append(joint + "y")
    for c, cycle in enumerate(all_cycles):
        exclude_this_cycle = False  # reset
        for col in columns:
            if col.endswith("x"):
                this_threshold = x_sc_broken_threshold
            elif col.endswith("y"):
                this_threshold = y_sc_broken_threshold
            this_data = data.loc[cycle[0] : cycle[1], col]
            for i in range(len(this_data) - 1):
                if (this_data.iloc[i + 1] > (this_data.iloc[i] + this_threshold)) | (
                    this_data.iloc[i + 1] < (this_data.iloc[i] - this_threshold)
                ):
                    exclude_this_cycle = True
        if exclude_this_cycle == True:
            this_message = (
                "\n...excluding SC #"
                + str(c + 1)
                + " - Tracking failed (coordinate-jump larger than x/y threshold)!"
            )
            print(this_message)
            write_issues_to_textfile(this_message, info)
        else:
            if clean_cycles == None:
                clean_cycles = [cycle]  # also makes a 2xscs list of lists
            else:
                clean_cycles.append(cycle)
    return clean_cycles


def check_tracking_SLEAP_nans(all_cycles, data, info, cfg):
    """In SLEAP if tracking fails it generates NaNs - make sure we don't have those in any SC in any joint or angle-joint"""
    # unpack
    hind_joints = cfg["hind_joints"]
    angles = cfg["angles"]
    # all joints to test for NaNs
    all_joints = hind_joints
    for key in angles.keys():
        all_joints += angles[key]
    # columns to check
    columns = []
    for joint in all_joints:
        columns.append(joint + "x")
        columns.append(joint + "y")
    # check for NaNs
    clean_cycles = None
    for c, cycle in enumerate(all_cycles):
        exclude_this_cycle = False  # reset
        for col in columns:
            this_data = data.loc[cycle[0] : cycle[1], col]
            if any(this_data.isna()):
                exclude_this_cycle = True
                NaN_joint = col
                break
        if exclude_this_cycle == True:
            this_message = (
                "\n...excluding SC #"
                + str(c + 1)
                + f" - Tracking failed (NaN found at {NaN_joint})!"
            )
            print(this_message)
            write_issues_to_textfile(this_message, info)
        else:
            if clean_cycles == None:
                clean_cycles = [cycle]  # also makes a 2xscs list of lists
            else:
                clean_cycles.append(cycle)
    return clean_cycles


def handle_issues(condition, info):
    """Handle different kind of issues with step-cycles (& the table)"""
    # 1: can also occur bc. all scs when dlc failed
    if condition == "scs_invalid":
        this_message = (
            "\n***********\n! WARNING !\n***********\n"
            + "Skipped since all SCs invalid!"
        )
        print(this_message)
        write_issues_to_textfile(this_message, info)
    # 2: no SCs were provided in XLS table
    elif condition == "no_scs":
        this_message = (
            "\n***********\n! WARNING !\n***********\n"
            + "Skipped since no SCs in Annotation Table!"
        )
        print(this_message)
        write_issues_to_textfile(this_message, info)
    # 3: the mouse was not included in XLS table
    elif condition == "no_mouse":
        this_message = (
            "\n***********\n! WARNING !\n***********\n"
            + "Skipped since ID not in Annotation Table!"
        )
        print(this_message)
        write_issues_to_textfile(this_message, info)
    # 4: user entered wrong column names in XLS table
    elif condition == "wrong_scxls_colnames":
        this_message = (
            "\n******************\n! CRITICAL ERROR !"
            + "\n******************\n"
            + "Annotation Table's Column Names are wrong!\n"
            + "Check Instructions!"
        )
        print(this_message)
        write_issues_to_textfile(this_message, info)
    # 5:
    elif condition == "double_mouse":
        this_message = (
            "\n***********\n! WARNING !\n***********\n"
            + "Skipped since ID found more than once in "
            + "Annotation Table!"
        )
        print(this_message)
        write_issues_to_textfile(this_message, info)
    return

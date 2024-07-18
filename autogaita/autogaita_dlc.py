# %% imports
import os
import sys
import shutil
import json
import warnings
import pandas as pd
import numpy as np
import math
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
import customtkinter as ctk
import seaborn as sns

# %% constants
matplotlib.use("agg")
# Agg is a non-interactive backend for plotting that can only write to files
# this is used to generate and save the plot figures
# later a tkinter backend (FigureCanvasTkAgg) is used for the plot panel
plt.rcParams["figure.dpi"] = 300  # increase resolution of figures
DIRECTION_DLC_THRESHOLD = 0.95  # DLC confidence used for direction-detection
TIME_COL = "Time"
ISSUES_TXT_FILENAME = "Issues.txt"  # filename to which we write issues-info
CONFIG_JSON_FILENAME = "config.json"  # filename to which we write cfg-infos
SCXLS_MOUSECOLS = [
    "Mouse",
    "mouse",
    "Fly",
    "fly",
    "Animal",
    "animal",
    "Subject",
    "subject",
    "ID",
    "id",
]  # SC XLS info
SCXLS_RUNCOLS = ["Run", "run", "Runs", "runs", "Trial", "trial", "Trials", "trials"]
SCXLS_SCCOLS = ["SC Number", "SC number", "sc number", "SC Num", "sc num", "SC num"]
SWINGSTART_COL = "Swing (ti)"
STANCEEND_COL = "Stance (te)"
ORIGINAL_XLS_FILENAME = " - Original Stepcycles"  # filenames of sheet exports
NORMALISED_XLS_FILENAME = " - Normalised Stepcycles"
AVERAGE_XLS_FILENAME = " - Average Stepcycle"
STD_XLS_FILENAME = " - Standard Devs. Stepcycle"
SC_LAT_LEGEND_FONTSIZE = 7


# %% main program


def dlc(info, folderinfo, cfg):
    """Runs the main program for a given mouse's run

    Procedure
    ---------
    1) import & preparation
    2) step cycle extraction
    3) y-normalisation & feature computation for individual step cycles
    4) step cycle normalisation, dataframe creation & XLS-exportation
    5) plots
    """
    # .............. initiate plot panel class and build loading screen ................
    # create class instance independently of "dont_show_plots" to not break the code
    plot_panel_instance = PlotPanel()

    if cfg["dont_show_plots"] is True:
        pass  # going on without building the loading screen

    elif cfg["dont_show_plots"] is False:  # -> show plot panel
        # build loading screen
        plot_panel_instance.build_plot_panel_loading_screen()

    # ................................  preparation  ...................................
    data = some_prep(info, folderinfo, cfg)
    if data is None:
        return

    # .........................  step-cycle extraction  ................................
    all_cycles = extract_stepcycles(data, info, folderinfo, cfg)
    if not all_cycles:
        handle_issues("scs_invalid", info)
        return

    # .........  main analysis: sc-lvl y-norm, features, df-creation & export ..........
    results = analyse_and_export_stepcycles(data, all_cycles, info, folderinfo, cfg)

    # ................................  plots  .........................................
    plot_results(info, results, folderinfo, cfg, plot_panel_instance)

    # ............................  print finish  ......................................
    print_finish(info, cfg)


# %% local functions 1 - preparation


def some_prep(info, folderinfo, cfg):
    """Preparation of the data & cfg file for later analyses"""

    # ............................  unpack stuff  ......................................
    name = info["name"]
    results_dir = info["results_dir"]
    data_string = folderinfo["data_string"]
    beam_string = folderinfo["beam_string"]
    sampling_rate = cfg["sampling_rate"]
    subtract_beam = cfg["subtract_beam"]
    convert_to_mm = cfg["convert_to_mm"]
    pixel_to_mm_ratio = cfg["pixel_to_mm_ratio"]
    normalise_height_at_SC_level = cfg["normalise_height_at_SC_level"]
    invert_y_axis = cfg["invert_y_axis"]
    flip_gait_direction = cfg["flip_gait_direction"]
    export_average_x = cfg["export_average_x"]

    # .............................  move data  ........................................
    # => see if we can delete a previous runs results folder if existant. if not, it's a
    #    bit ugly since we only update results if filenames match...
    # => for example if angle acceleration not wanted in current run, but was stored in
    #    previous run, the previous run's figure is in the folder
    # => inform the user and leave this as is
    if os.path.exists(results_dir):
        try:
            shutil.rmtree(results_dir)
            move_data_to_folders(info, folderinfo)
        except OSError:
            move_data_to_folders(info, folderinfo)
            unable_to_rm_resdir_error = (
                "\n***********\n! WARNING !\n***********\n"
                + "Unable to remove previous Results subfolder of ID: "
                + name
                + "!\n Results will only be updated if filenames match!"
            )
            print(unable_to_rm_resdir_error)
            write_issues_to_textfile(unable_to_rm_resdir_error, info)
    else:
        move_data_to_folders(info, folderinfo)

    # .......  initialise Issues.txt & quick check for file existence  .................
    # Issues.txt - delete if saved in a previous run
    issues_txt_path = os.path.join(results_dir, ISSUES_TXT_FILENAME)
    if os.path.exists(issues_txt_path):
        os.remove(issues_txt_path)
    # read data & beam
    if not os.listdir(results_dir):
        no_files_error = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "Unable to identify ANY RELEVANT FILES for "
            + name
            + "!\nThis is likely due to issues with unique file name identifiers.. "
            + "check capitalisation!"
        )
        write_issues_to_textfile(no_files_error, info)
        print(no_files_error)
        return

    # ............................  import data  .......................................
    datadf = pd.DataFrame(data=None)  # prep stuff for error handling
    datadf_duplicate_error = ""
    if subtract_beam:
        if data_string == beam_string:
            beam_and_data_string_error_message = (
                "\n******************\n! CRITICAL ERROR !\n******************\n"
                + "Your data & baseline (beam) identifiers ([G] in our "
                + "file  naming convention) are identical. "
                + "\nNote that they must be different! \nTry again"
            )
            write_issues_to_textfile(beam_and_data_string_error_message, info)
            return
        beamdf = pd.DataFrame(data=None)
        beamdf_duplicate_error = ""
    for filename in os.listdir(results_dir):  # import
        if filename.endswith(".csv"):
            if data_string in filename:
                if datadf.empty:
                    datadf = pd.read_csv(os.path.join(results_dir, filename))
                else:
                    datadf_duplicate_error = (
                        "\n******************\n! CRITICAL ERROR !\n******************\n"
                        + "Two DATA csv-files found for "
                        + name
                        + "!\nPlease ensure your root directory only has one datafile "
                        + "per video!"
                    )
            if subtract_beam:
                if beam_string in filename:
                    if beamdf.empty:
                        beamdf = pd.read_csv(os.path.join(results_dir, filename))
                    else:
                        beamdf_duplicate_error = (
                            "\n******************\n! CRITICAL ERROR !\n***************"
                            + "***\nTwo BEAM csv-files found for "
                            + name
                            + "!\nPlease ensure your root directory only has one "
                            + "beamfile per video!"
                        )
    # handle import errors
    # => append to empty strings to handle multiple issues at once seemlessly
    import_error_message = ""
    if datadf_duplicate_error:
        import_error_message += datadf_duplicate_error
    if datadf.empty:
        import_error_message += (  # if pd didn't raise errors but dfs still empty
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "Unable to load a DATA csv file for "
            + name
            + "!\nTry again!"
        )
    if subtract_beam:
        if beamdf_duplicate_error:
            import_error_message += beamdf_duplicate_error
        if beamdf.empty:
            import_error_message += (
                "\n******************\n! CRITICAL ERROR !\n******************\n"
                + "Unable to load a BEAM csv file for "
                + name
                + "!\nTry again!"
            )
    if import_error_message:  # see if there was any issues with import, if so: stop
        print(import_error_message)
        write_issues_to_textfile(import_error_message, info)
        return

    # ....  finalise import: rename cols, get rid of unnecessary elements, floatit  ....
    colnamesdata = list()  # data df
    for j in range(datadf.shape[1]):
        colnamesdata.append(datadf.iloc[0, j] + " " + datadf.iloc[1, j])
    datadf.columns = colnamesdata
    datadf = datadf.iloc[2:, 1:]
    datadf.index = range(datadf.shape[0])
    datadf = datadf.astype(float)
    if subtract_beam:  # beam df
        colnamesbeam = list()
        for j in range(beamdf.shape[1]):
            colnamesbeam.append(beamdf.iloc[0, j] + " " + beamdf.iloc[1, j])
        beamdf.columns = colnamesbeam
        beamdf = beamdf.iloc[2:, 1:]
        beamdf.index = range(beamdf.shape[0])
        beamdf = beamdf.astype(float)
        data = pd.concat([datadf, beamdf], axis=1)
    else:
        data = datadf.copy(deep=True)

    # ................  final data checks, conversions & additions  ....................
    # IMPORTANT
    # ---------
    # MAIN TESTS OF USER-INPUT VALIDITY OCCUR HERE!
    cfg = check_and_expand_cfg(data, cfg, info)
    if cfg is None:  # hind joints were empty
        return
    hind_joints = cfg["hind_joints"]
    fore_joints = cfg["fore_joints"]
    angles = cfg["angles"]
    beam_hind_jointadd = cfg["beam_hind_jointadd"]
    beam_fore_jointadd = cfg["beam_fore_jointadd"]
    direction_joint = cfg["direction_joint"]
    # store config json file @ group path
    # !!! NU - do this @ mouse path!
    group_path = results_dir.split(name)[0]
    config_json_path = os.path.join(group_path, CONFIG_JSON_FILENAME)
    config_vars_to_json = {
        "sampling_rate": sampling_rate,
        "convert_to_mm": convert_to_mm,
        "normalise_height_at_SC_level": normalise_height_at_SC_level,
        "export_average_x": export_average_x,
        "hind_joints": hind_joints,
        "fore_joints": fore_joints,
        "angles": angles,
        "tracking_software": "DLC",
    }
    # note - using "w" will overwrite/truncate file, thus no need to remove it if exists
    with open(config_json_path, "w") as config_json_file:
        json.dump(config_vars_to_json, config_json_file, indent=4)
    # a little test to see if columns make sense, i.e., same number of x/y/likelihood
    x_col_count = len([c for c in data.columns if c.endswith(" x")])
    y_col_count = len([c for c in data.columns if c.endswith(" y")])
    likelihood_col_count = len([c for c in data.columns if c.endswith(" likelihood")])
    if x_col_count == y_col_count == likelihood_col_count:
        pass
    else:
        cols_are_weird_message = (
            "\n***********\n! WARNING !\n***********\n"
            + "We detected an unequal number of columns ending with x, y or "
            + "likelihood!\nCounts were:\n"
            + "x: "
            + str(x_col_count)
            + ", y: "
            + str(y_col_count)
            + ", likelihood: "
            + str(likelihood_col_count)
            + "!\n\n"
            + "We continue with the analysis but we strongly suggest you have another "
            + "look at your dataset, this should not happen.\n"
        )
        print(cols_are_weird_message)
        write_issues_to_textfile(cols_are_weird_message, info)
    # if wanted: fix that deeplabcut inverses y
    if invert_y_axis:
        for col in data.columns:
            if col.endswith(" y"):
                data[col] = data[col] * -1
    # if we don't have a beam to subtract, normalise y to global y minimum being 0
    if not subtract_beam:
        global_y_min = float("inf")
        y_cols = [col for col in data.columns if col.endswith("y")]
        global_y_min = min(data[y_cols].min())
        data[y_cols] -= global_y_min
    # convert pixels to millimeters
    if convert_to_mm:
        for column in data.columns:
            if not column.endswith("likelihood"):
                data[column] = data[column] / pixel_to_mm_ratio
    # check gait direction & DLC file validity
    data = check_gait_direction(data, direction_joint, flip_gait_direction, info)
    if data is None:  # this means DLC file is broken
        return
    # subtract the beam from the joints to normalise y
    # => bc. we simulate that all mice run from left to right, we can write:
    #     (note that we also flip beam x columns, but never y-columns!)
    # => & bc. we multiply y values by *-1 earlier, it's a neg_num - - neg_num
    #    pushing it towards zero.
    # => using list(set()) to ensure that we don't have duplicate values (if users
    #    should have provided them in both cfg vars by misstake)
    # => beam_col_left and right is provided by users
    if subtract_beam:
        # note beam_col_left/right are always lists in cfg!
        beam_col_left = cfg["beam_col_left"][0]
        beam_col_right = cfg["beam_col_right"][0]
        for joint in list(set(hind_joints + beam_hind_jointadd)):
            data[joint + "y"] = data[joint + "y"] - data[beam_col_left + "y"]
        for joint in list(set(fore_joints + beam_fore_jointadd)):
            data[joint + "y"] = data[joint + "y"] - data[beam_col_right + "y"]
        data.drop(columns=list(beamdf.columns), inplace=True)  # beam not needed anymore
    # add Time and round based on sampling rate
    data[TIME_COL] = data.index * (1 / sampling_rate)
    if sampling_rate <= 100:
        data[TIME_COL] = round(data[TIME_COL], 2)
    elif 100 < sampling_rate <= 1000:
        data[TIME_COL] = round(data[TIME_COL], 3)
    else:
        data[TIME_COL] = round(data[TIME_COL], 4)
    # reorder the columns we added
    cols = [TIME_COL, "Flipped"]
    data = data[cols + [c for c in data.columns if c not in cols]]
    return data


# ..............................  helper functions  ....................................


def move_data_to_folders(info, folderinfo):
    """Find files, copy data, video, beamdata & beamvideo to new results_dir"""
    # unpack
    results_dir = info["results_dir"]
    postmouse_string = folderinfo["postmouse_string"]
    postrun_string = folderinfo["postrun_string"]
    os.makedirs(results_dir)  # important to do this outside of loop!
    # check if user inputted "_" & "-" for postmouse & postrun strings - if not do it
    # for them
    for candidate_postmouse_string in [postmouse_string, "_" + postmouse_string]:
        for candidate_postrun_string in [postrun_string, "-" + postrun_string]:
            found_it = check_this_filename_configuration(
                info,
                folderinfo,
                candidate_postmouse_string,
                candidate_postrun_string,
                results_dir,
            )
            if found_it:  # if our search was successful, stop searching and continue
                break


def check_this_filename_configuration(
    info, folderinfo, postmouse_string, postrun_string, results_dir
):
    # unpack
    name = info["name"]
    mouse_num = info["mouse_num"]
    run_num = info["run_num"]
    root_dir = folderinfo["root_dir"]
    data_string = folderinfo["data_string"]
    beam_string = folderinfo["beam_string"]
    premouse_string = folderinfo["premouse_string"]
    prerun_string = folderinfo["prerun_string"]
    whichvideo = ""  # initialise
    found_it = False
    for filename in os.listdir(root_dir):
        # the following condition is True for data & beam csv
        if (
            (premouse_string + str(mouse_num) + postmouse_string in filename)
            and (prerun_string + str(run_num) + postrun_string in filename)
            and (filename.endswith(".csv"))
        ):
            found_it = True
            # Copy the Excel file to the new subfolder
            shutil.copy2(
                os.path.join(root_dir, filename), os.path.join(results_dir, filename)
            )
            # Check if there is a video and if so copy it too
            vidname = filename[:-4] + "_labeled.mp4"
            vidpath = os.path.join(root_dir, vidname)
            if os.path.exists(vidpath):
                shutil.copy2(vidpath, os.path.join(results_dir, vidname))
            else:
                if data_string in vidname:
                    whichvideo = "Data"
                elif beam_string in vidname:
                    whichvideo = "Beam"
                this_message = (
                    "\n***********\n! WARNING !\n***********\n"
                    + "No "
                    + whichvideo
                    + "video for "
                    + name
                    + "!"
                )
                print(this_message)
                write_issues_to_textfile(this_message, info)
    return found_it


def check_and_expand_cfg(data, cfg, info):
    """Test some important cfg variables and add new ones based on them

    Procedure
    ---------
    Check that no strings are empty
    Check that all strings end with a space character
    Check that all features are present in the dataset
    Add plot_joints & direction_joint
    Make sure to set dont_show_plots to True if Python is not in interactive mode
    If users subtract a beam, set normalise @ sc level to False
    """

    # run the tests first
    for cfg_key in [
        "angles",
        "hind_joints",
        "fore_joints",
        "beam_col_left",  # note beamcols are lists even though len=1 bc. of
        "beam_col_right",  # check function's procedure
        "beam_hind_jointadd",
        "beam_fore_jointadd",
    ]:
        cfg[cfg_key] = check_and_fix_cfg_strings(data, cfg, cfg_key, info)

    # add plot_joints - used for average plots & stick diagram
    hind_joints = cfg["hind_joints"]
    if cfg["plot_joint_number"] > len(hind_joints):
        fix_plot_joints_message = (
            "\n***********\n! WARNING !\n***********\n"
            + "You asked us to plot more hind limb joints than available!"
            + "\nNumber of joints to plot: "
            + str(cfg["plot_joint_number"])
            + "\nNumber of selected hindlimb joints: "
            + str(len(hind_joints))
            + "\n\nWe'll just plot the most we can :)"
        )
        write_issues_to_textfile(fix_plot_joints_message, info)
        print(fix_plot_joints_message)
        cfg["plot_joints"] = hind_joints
    else:
        cfg["plot_joints"] = hind_joints[: cfg["plot_joint_number"]]

    # check hindlimb joints & add direction_joint - used to determine gait direction
    if not hind_joints:  # no valid string after above cleaning
        no_hind_joint_message = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "After testing your hind limb joint names, no valid joint was left to "
            + "perform gait direction checks on.\nPlease make sure that at least one "
            + "hind limb joint is provided & try again!"
        )
        write_issues_to_textfile(no_hind_joint_message, info)
        print(no_hind_joint_message)
        return
    cfg["direction_joint"] = hind_joints[0]

    # if subtracting beam, check identifier-strings & that beam colnames were valid.
    if cfg["subtract_beam"]:
        beam_col_error_message = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "It seems like you want to normalise heights to a baseline (beam)."
            + "\nUnfortunately we were unable to find the y-columns you listed in "
            + "your beam's csv-file.\nPlease try again.\nInvalid beam side(s) was/were:"
        )
        beam_error = False  # check 3 possible cases
        if (cfg["beam_col_left"]) and (not cfg["beam_col_right"]):
            beam_error = True
            beam_col_error_message += "\n right beam!"
        elif (not cfg["beam_col_left"]) and (cfg["beam_col_right"]):
            beam_error = True
            beam_col_error_message += "\n left beam!"
        elif (not cfg["beam_col_left"]) and (not cfg["beam_col_right"]):
            beam_error = True
            beam_col_error_message += "\n both beams!"
        if beam_error:  # if any case was True, stop everything
            write_issues_to_textfile(beam_col_error_message, info)
            print(beam_col_error_message)
            return

    # never normalise @ SC level if user subtracted a beam
    if cfg["subtract_beam"]:
        cfg["normalise_height_at_SC_level"] = False

    return cfg


def check_and_fix_cfg_strings(data, cfg, cfg_key, info):
    """Check and fix strings in our joint & angle lists so that:
    1) They don't include empty strings
    2) All strings end with the space character (since we do string + "y")
    3) All strings are valid columns of the DLC dataset
    """

    # work on this variable (we return to cfg[key] outside of here)
    string_variable = cfg[cfg_key]

    # easy checks: lists
    if type(string_variable) is list:
        string_variable = [s for s in string_variable if s]
        string_variable = [s if s.endswith(" ") else s + " " for s in string_variable]
        clean_string_list = []
        invalid_strings_message = ""
        for s, string in enumerate(string_variable):
            if string + "y" in data.columns:
                clean_string_list.append(string)
            else:
                invalid_strings_message += "\n" + string
        if invalid_strings_message:
            # print and save warning
            strings_warning = (
                "\n***********\n! WARNING !\n***********\n"
                + "Unable to find all "
                + cfg_key
                + " joints/key points you entered!"
                + "\n\nInvalid and thus removed were:"
                + invalid_strings_message
            )
            print(strings_warning)
            write_issues_to_textfile(strings_warning, info)
            # clean the string
            string_variable = clean_string_list
            # print & save info about remaining ("clean") strings
            clean_strings_message = "\nRemaining joints / key points are:"
            for string in clean_string_list:
                clean_strings_message += "\n" + string
            clean_strings_message += (
                "\n\nNote that capitalisation matters."
                + "\nIf you are running a batch analysis, we'll use this updated cfg "
                + "throughout\nCheck out the config.json file for the full cfg used."
            )
            print(clean_strings_message)
            write_issues_to_textfile(clean_strings_message, info)

    # things are more involved for angle dicts
    elif type(string_variable) is dict:
        # 1) test if the lists of all keys are equally long, if not throw out last idxs
        key_lengths = [len(string_variable[key]) for key in string_variable.keys()]
        if not all(key_length == key_lengths[0] for key_length in key_lengths):
            min_length = min(key_lengths)
            for key in string_variable:  # remove invalid idxs
                string_variable[key] = string_variable[key][:min_length]
            key_length_mismatch_message = (  # inform user
                "\n***********\n! WARNING !\n***********\n"
                + "\nLength-mismatch in angle configuration!"
                + "\nCheck angles' name/upper/lower-joint entries."
                + "\nOnly processing first "
                + str(min_length)
                + " entries."
            )
            print(key_length_mismatch_message)
            write_issues_to_textfile(key_length_mismatch_message, info)
        # 2) check if all strings in the angle dict are valid columns
        invalid_angletrio_message = ""
        invalid_idxs = []  # these idxs hold across the 3 keys of our angles-dict
        for key in string_variable:
            # important to do this first (else string + "y" is invalid)
            string_variable[key] = [
                s if s.endswith(" ") else s + " " for s in string_variable[key]
            ]
            # remove any empty or invalid (i.e. not in data) strings from our angletrio
            this_keys_missing_strings = ""
            for idx, string in enumerate(string_variable[key]):
                if string + "y" not in data.columns:  # checks for empty strings too
                    invalid_idxs.append(idx)
                    if not this_keys_missing_strings:  # first occurance
                        this_keys_missing_strings += "\nAngle's " + key + " key: "
                    this_keys_missing_strings += string + "(#" + str(idx + 1) + ") / "
            # string concat outside of idx-forloop above please
            invalid_angletrio_message += this_keys_missing_strings
        # if we have to remove idxs from all keys of our angles dict
        if invalid_angletrio_message:
            # print and save
            angles_warning = (
                "\n***********\n! WARNING !\n***********\n"
                + "Unable to find all "
                + cfg_key
                + " joints/key points you entered!"
                + "\n\nInvalid and thus removed were:"
                + invalid_angletrio_message
            )
            print(angles_warning)
            write_issues_to_textfile(angles_warning, info)
            # clean the dict
            invalid_idxs = list(set(invalid_idxs))  # remove duplicates
            for key in string_variable:
                string_variable[key] = [
                    string
                    for i, string in enumerate(string_variable[key])
                    if i not in invalid_idxs
                ]
            # print & save info about the remaining ("clean") angles dict
            clean_angles_message = "\nRemaining angle configuration is:"
            for i in range(len(string_variable["name"])):
                clean_angles_message += "\n\nAngle #" + str(i + 1)
                clean_angles_message += "\nName: " + string_variable["name"][i]
                clean_angles_message += (
                    "\nLower Joint: " + string_variable["lower_joint"][i]
                )
                clean_angles_message += (
                    "\nUpper Joint: " + string_variable["upper_joint"][i]
                )
            clean_angles_message += (
                "\n\nNote that capitalisation matters."
                + "\nIf you are running a batch analysis, we'll use this updated cfg "
                + "throughout\nCheck out the config.json file for the full cfg used."
            )
            print(clean_angles_message)
            write_issues_to_textfile(clean_angles_message, info)

    return string_variable


def flip_mouse_body(data, info):
    """If the mouse ran through the video frame from right to left simulate
    that it ran from left to right. For this just subtract all x-values of
    all x-columns from their respective maxima.
    ==> This preserves time-information important for SC extraction via table
    ==> This preserves y-information too
    ==> All analyses & plots are therefore comparable to mice that did really
        run from left to right
    """

    # 0) Tell the user that we are flipping their mouse
    message = (
        "\nDetermined gait direction of right => left - simulating it to be left => "
        + "right"
    )
    print(message)
    write_issues_to_textfile(message, info)

    # 1) Flip all rows in x columns only and subtract max from all vals
    flipped_data = data.copy()
    x_cols = [col for col in flipped_data.columns if col.endswith(" x")]
    for col in x_cols:
        flipped_data[col] = max(flipped_data[col]) - flipped_data[col]
    return flipped_data


def check_gait_direction(data, direction_joint, flip_gait_direction, info):
    """Check direction of gait - reverse it if needed

    Note
    ----
    Also using this check to check for DLC files being broken
    flip_gait_direction is only used after the check for DLC files being broken
    """

    data["Flipped"] = False
    enterframe = 0
    idx = 0
    flip_error_message = ""
    while enterframe == 0:  # first find out when mouse was in the video frame.
        if (
            np.mean(data[direction_joint + "likelihood"][idx : idx + 5])
            > DIRECTION_DLC_THRESHOLD
        ):  # +5 to increase conf.
            enterframe = idx + 5
        idx += 1
        if (idx > len(data)) | (enterframe > len(data)):
            flip_error_message += (
                "\n******************\n! CRITICAL ERROR !\n******************\n"
                + "Unable to determine gait direction!"
                + "\nThis hints a critical issue with DLC tracking, e.g., likelihood "
                + "\ncolumns being low everywhere or tables being suspiciously short!"
                + "\nTo be sure, we cancel everything here."
                + "\nPlease check your input DLC csv files for correctness & try again!"
            )
            break
    leaveframe = 0
    idx = 1
    while leaveframe == 0:  # see where mouse left frame (same logic from back)
        if (
            np.mean(data[direction_joint + "likelihood"][-idx - 5 : -idx])
            > DIRECTION_DLC_THRESHOLD
        ):
            leaveframe = len(data) - idx - 5
        idx += 1
        if idx > len(data):
            if not flip_error_message:
                flip_error_message += (
                    "\n******************\n! CRITICAL ERROR !\n******************\n"
                    + "Unable to determine gait direction!"
                    + "\nThis hints a critical issue with DLC tracking, e.g., "
                    + "likelihood \ncolumns being low everywhere or tables being "
                    + "suspiciously short!\nTo be sure, we cancel everything here."
                    + "\nPlease check your input DLC csv files for correctness & try "
                    + "again!"
                )
            break
    if flip_error_message:
        write_issues_to_textfile(flip_error_message, info)
        print(flip_error_message)
        return
    if (
        data[direction_joint + "x"][enterframe]
        > data[direction_joint + "x"][leaveframe]
    ):  # i.e.: right to left
        # simulate that mouse ran from left to right (only if user wants it)
        if flip_gait_direction:
            data = flip_mouse_body(data, info)
            data["Flipped"] = True
    return data


def write_issues_to_textfile(message, info):
    """If there are any issues with this data, inform the user in this file"""
    textfile = os.path.join(info["results_dir"], ISSUES_TXT_FILENAME)
    with open(textfile, "a") as f:
        f.write(message)


# %% local functions 2 - SC extraction (reading user-provided SC Table)


def extract_stepcycles(data, info, folderinfo, cfg):
    """Read XLS file with SC annotations, find correct row & return all_cycles"""

    # ...............................  preparation  ....................................
    # unpack
    mouse_num = info["mouse_num"]
    run_num = info["run_num"]
    root_dir = folderinfo["root_dir"]
    sctable_filename = folderinfo["sctable_filename"]
    sampling_rate = cfg["sampling_rate"]

    # check if excel file is .xlsx or .xls, if none found try to fix it
    if (".xls" in sctable_filename) | (".xlsx" in sctable_filename):
        if os.path.exists(os.path.join(root_dir, sctable_filename)):
            SCdf = pd.read_excel(os.path.join(root_dir, sctable_filename))
        else:
            raise FileNotFoundError(
                "No Annotation Table found! sctable_filename has to be @ root_dir"
            )
    else:
        # in cases below use string-concat (+) - otherwise xls added as path
        if os.path.exists(os.path.join(root_dir, sctable_filename + ".xls")):
            SCdf = pd.read_excel(os.path.join(root_dir, sctable_filename + ".xls"))
        elif os.path.exists(os.path.join(root_dir, sctable_filename + ".xlsx")):
            SCdf = pd.read_excel(os.path.join(root_dir, sctable_filename + ".xlsx"))
        else:
            raise FileNotFoundError(
                "No Annotation Table found! sctable_filename has to be @ root_dir"
            )
    # see if table columns are labelled correctly (try a couple to allow user typos)
    valid_col_flags = [False, False, False]
    header_columns = ["", "", ""]
    for h, header in enumerate([SCXLS_MOUSECOLS, SCXLS_RUNCOLS, SCXLS_SCCOLS]):
        for header_col in header:
            if header_col in SCdf.columns:
                valid_col_flags[h] = True
                header_columns[h] = header_col
                break
    if not all(valid_col_flags):
        handle_issues("wrong_scxls_colnames", info)
        return
    # find our info columns & rows
    mouse_col = SCdf.columns.get_loc(header_columns[0])  # INDEXING! (see list above)
    run_col = SCdf.columns.get_loc(header_columns[1])
    sc_col = SCdf.columns.get_loc(header_columns[2])
    # mouse_row will always be start of this mouse's runs
    mouse_row = SCdf.index[SCdf[header_columns[0]] == mouse_num]
    # this mouse was not included in sc xls
    if len(mouse_row) == 0:
        handle_issues("no_mouse", info)
        return
    # this mouse was included more than once
    if len(mouse_row) > 1:
        handle_issues("double_mouse", info)
        return

    next_mouse_idx = mouse_row  # search idx of first row of next mouse

    # ..............................  main xls read  ...................................
    # if while is False, we arrived at the next mouse/end & dont update next_mouse_idx
    # 3 conditions (continue if true):
    # 1) First row of this mouse
    # 2) None means a different run of this mouse or an empty row
    # 3) Last line of SC Table
    # ==> Important that there are parentheses around mouse & runs cond!!!
    while (
        (SCdf.iloc[next_mouse_idx, mouse_col].values[0] == mouse_num)
        | (np.isnan(SCdf.iloc[next_mouse_idx, mouse_col].values[0]))
    ) & (next_mouse_idx[0] != len(SCdf) - 1):
        next_mouse_idx += 1  # this becomes first idx of next mouse's runs
    # slicing is exclusive, so indexing the first row of next mouse means we
    # include (!) the last row of correct mouse
    if next_mouse_idx[0] != (len(SCdf) - 1):
        mouse_runs = SCdf.iloc[int(mouse_row[0]) : int(next_mouse_idx[0]), run_col]
    else:
        # SPECIAL CASE: the last row of SCdf is a mouse with only one run!!!
        # ==> E.g.: SCdf's last idx is 25.
        #     SCdf.iloc[25:25, run_col] == Empty Series (slicing exclusive)
        # NOTE THAT: if this mouse should have two runs, e.g. 24 & 25:
        #     SCdf.iloc[24:25, run_col] == Correct series because 25 is treated
        #     as SCdf.iloc[24:, run_col]
        # TO BE SURE: if our while loop broke out bc. we arrived at SCdf's end,
        #     just index with a colon iloc[mouse_row:]
        mouse_runs = SCdf.iloc[int(mouse_row[0]) :, run_col]
    if run_num not in mouse_runs.values:
        handle_issues("no_scs", info)
        return  # return None and stop everything
    # find out the total number of scs & see if it matches user-provided values
    # => also exclude run if no scs found
    info_row = mouse_runs[mouse_runs == run_num].index  # where is this run
    sc_num = 0
    for column in SCdf.columns:
        if STANCEEND_COL in column:
            if np.isnan(SCdf[column][info_row].values[0]) == False:
                sc_num += 1
    if sc_num == 0:
        handle_issues("no_scs", info)
        return
    user_scnum = SCdf.iloc[info_row, sc_col].values[0]  # sanity check input
    if user_scnum != sc_num:  # warn the user, take the values we found
        this_message = (
            "\n***********\n! WARNING !\n***********\n"
            + "Mismatch between stepcycle number of SC Number column & "
            + "entries in swing/stance latency columns!"
            + "\nUsing all valid swing/stance entries."
        )
        print(this_message)
        write_issues_to_textfile(this_message, info)

    # ...........................  idxs to all_cycles  .................................
    # use value we found, loop over all runs, throw all scs into all_cycles
    all_cycles = [[None, None] for s in range(sc_num)]  # fill :sc_num x 2 list
    for s in range(sc_num):
        if s == 0:
            start_col = SCdf.columns.get_loc(SWINGSTART_COL)
            end_col = SCdf.columns.get_loc(STANCEEND_COL)
        else:
            # str(s) because colnames match s for s>0!
            start_col = SCdf.columns.get_loc(SWINGSTART_COL + "." + str(s))
            end_col = SCdf.columns.get_loc(STANCEEND_COL + "." + str(s))
        user_scnum += 1
        # extract the SC times
        start_in_s = float(SCdf.iloc[info_row, start_col].values[0])
        end_in_s = float(SCdf.iloc[info_row, end_col].values[0])
        if sampling_rate <= 100:
            float_precision = 2  # how many decimals we round to
        elif 100 < sampling_rate <= 1000:
            float_precision = 3
        else:
            float_precision = 4
        start_in_s = round(start_in_s, float_precision)
        end_in_s = round(end_in_s, float_precision)
        try:
            all_cycles[s][0] = np.where(data[TIME_COL] == start_in_s)[0][0]
            all_cycles[s][1] = np.where(data[TIME_COL] == end_in_s)[0][0]
        except IndexError:
            this_message = (
                "\n***********\n! WARNING !\n***********\n"
                + "SC latencies of: "
                + str(start_in_s)
                + "s to "
                + str(end_in_s)
                + "s not in data/video range!\n"
                + "Skipping!"
            )
            print(this_message)
            write_issues_to_textfile(this_message, info)

    # ............................  clean all_cycles  ..................................
    # check if we skipped latencies because they were out of data-bounds
    all_cycles = check_cycle_out_of_bounds(all_cycles)
    # check if there are any duplicates (e.g., SC2's start-lat == SC1's end-lat)
    all_cycles = check_cycle_duplicates(all_cycles)
    # check if user input progressively later latencies
    all_cycles = check_cycle_order(all_cycles, info)
    # check if DLC tracking broke for any SCs - if so remove them
    all_cycles = check_DLC_tracking(data, info, all_cycles, cfg)
    return all_cycles


# ..............................  helper functions  ....................................
def check_cycle_out_of_bounds(all_cycles):
    """Check if user provided SC latencies that were not in video/data bounds"""
    clean_cycles = []
    for cycle in all_cycles:
        # below checks if values are any type of int (just in case this should
        # for some super random reason change...)
        if isinstance(cycle[0], (int, np.integer)) & isinstance(
            cycle[1], (int, np.integer)
        ):
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


def check_DLC_tracking(data, info, all_cycles, cfg):
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
                "\n...excluding SC #" + str(c + 1) + " - DLC tracking failed!"
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


# %% local functions 3 - normalise SCs & export (orig. & norm.) XLS files
# Note
# ----
# There is quite a lot going on in this function. We:
# 1) loop through all step cycles for one leg at a time and extract data
# 2) for each step's data we normalise all y (height) values to the body's minimum
#    if wanted
# 3) we compute and add features (angles, velocities, accelerations)
#    ==> see norm_y_and_add_features_to_one_step & helper functions a
# 4) immediately after adding features, we normalise a step to bin_num
#    ==> see normalise_one_steps_data & helper functions b
# 5) we add original and normalised steps to all_steps_data and normalised_steps_data
# 6) once we are done with this we create average and std dataframes7
# 7) we finally output all df-lists in a results dict and export each df-list as xls/csv
#   ==> see helper functions d


def analyse_and_export_stepcycles(data, all_cycles, info, folderinfo, cfg):
    """Export original-length and normalised XLS files of extracted steps"""
    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    save_to_xls = cfg["save_to_xls"]
    export_average_x = cfg["export_average_x"]
    bin_num = cfg["bin_num"]
    # do everything on a copy of the data df
    data_copy = data.copy()
    # exactly 1 step
    if len(all_cycles) == 1:
        this_step = data_copy.loc[all_cycles[0][0] : all_cycles[0][1]]
        all_steps_data = norm_y_and_add_features_to_one_step(this_step, cfg)
        normalised_steps_data = normalise_one_steps_data(all_steps_data, bin_num)
    # 2 or more steps - build dataframe
    elif len(all_cycles) > 1:
        # first- step is added manually
        first_step = data_copy.loc[all_cycles[0][0] : all_cycles[0][1]]
        first_step = norm_y_and_add_features_to_one_step(first_step, cfg)
        all_steps_data = first_step
        normalised_steps_data = normalise_one_steps_data(first_step, bin_num)
        # some prep for addition of further steps
        sc_num = len(all_cycles)
        nanvector = data_copy.loc[[1]]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            nanvector[:] = np.nan
        # ..............................  step-loop  ...................................
        for s in range(1, sc_num, 1):
            # get step separators
            numvector = data_copy.loc[[1]]
            # we are ignoring this because we wont work with the incompatible dtypes ourselves much anymore (just export as xlsx and plot) - so its fine
            # https://docs.python.org/3/library/warnings.html#temporarily-suppressing-warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                numvector[:] = s + 1
            all_steps_data = add_step_separators(all_steps_data, nanvector, numvector)
            # this_step
            this_step = data_copy.loc[all_cycles[s][0] : all_cycles[s][1]]
            this_step = norm_y_and_add_features_to_one_step(this_step, cfg)
            all_steps_data = pd.concat([all_steps_data, this_step], axis=0)
            # this_normalised_step
            this_normalised_step = normalise_one_steps_data(this_step, bin_num)
            normalised_steps_data = add_step_separators(
                normalised_steps_data, nanvector, numvector
            )
            normalised_steps_data = pd.concat(
                [normalised_steps_data, this_normalised_step], axis=0
            )
    # compute average & std data
    average_data, std_data = compute_average_and_std_data(
        name, normalised_steps_data, bin_num, export_average_x
    )
    # save to results dict
    results = {}
    results["all_steps_data"] = all_steps_data
    results["average_data"] = average_data
    results["std_data"] = std_data
    results["all_cycles"] = all_cycles
    # save to files
    save_results_sheet(
        all_steps_data,
        save_to_xls,
        os.path.join(results_dir, name + ORIGINAL_XLS_FILENAME),
    )
    save_results_sheet(
        normalised_steps_data,
        save_to_xls,
        os.path.join(results_dir, name + NORMALISED_XLS_FILENAME),
    )
    save_results_sheet(
        average_data,
        save_to_xls,
        os.path.join(results_dir, name + AVERAGE_XLS_FILENAME),
    )
    save_results_sheet(
        std_data, save_to_xls, os.path.join(results_dir, name + STD_XLS_FILENAME)
    )
    return results


# ......................................................................................
# ...............  helper functions a - norm z and add features  .......................
# ......................................................................................


def norm_y_and_add_features_to_one_step(step, cfg):
    """For a single step cycle's data, normalise z if wanted, flip y columns if needed
    (to simulate equal run direction) and add features (angles & velocities)
    """
    # if user wanted this, normalise z (height) at step-cycle level
    step_copy = step.copy()
    if cfg["normalise_height_at_SC_level"] is True:
        y_cols = [col for col in step_copy.columns if col.endswith("y")]
        this_y_min = step_copy[y_cols].min().min()
        step_copy[y_cols] -= this_y_min
    # add angles and velocities
    step_copy = add_features(step_copy, cfg)
    return step_copy


def add_features(step, cfg):
    """Add Features, i.e. Angles & Velocities"""
    # unpack
    hind_joints = cfg["hind_joints"]
    angles = cfg["angles"]
    if angles["name"]:  # if there is at least 1 string in the list
        step = add_angles(step, cfg)
    if hind_joints:
        step = add_velocities(step, cfg)
    return step


def add_angles(step, cfg):
    """Feature #1: Joint Angles"""
    # unpack
    angles = cfg["angles"]
    for a, angle in enumerate(angles["name"]):
        # initialise 2d (x/y coords) arrays
        joint_angle = np.zeros((len(step), 2), dtype=float)
        joint2 = np.zeros((len(step), 2), dtype=float)
        joint3 = np.zeros((len(step), 2), dtype=float)
        # unpack joint names for current angle
        lower_joint = angles["lower_joint"][a]
        upper_joint = angles["upper_joint"][a]
        # assign values to 2d arrays
        joint_angle[:, 0] = step[angle + "x"]  # joint we want angle of
        joint_angle[:, 1] = step[angle + "y"]
        joint2[:, 0] = step[lower_joint + "x"]  # make sure there is no space
        joint2[:, 1] = step[lower_joint + "y"]
        joint3[:, 0] = step[upper_joint + "x"]
        joint3[:, 1] = step[upper_joint + "y"]
        # initialise the angle vector and assign looping over timepoints
        this_angle = np.zeros(len(joint_angle))
        for t in range(len(joint_angle)):
            this_angle[t] = compute_angle(joint_angle[t, :], joint2[t, :], joint3[t, :])
        this_colname = angle + "Angle"
        step[this_colname] = this_angle
    return step


def compute_angle(joint_angle, joint2, joint3):
    """Compute a given angle at a joint & a given timepoint"""
    # Get vectors between the joints
    v1 = (joint_angle[0] - joint2[0], joint_angle[1] - joint2[1])
    v2 = (joint_angle[0] - joint3[0], joint_angle[1] - joint3[1])
    # dot product, magnitude of vectors, angle in radians & convert 2 degrees
    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    mag_v1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    mag_v2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
    angle = math.acos(dot_product / (mag_v1 * mag_v2))
    return math.degrees(angle)


def add_velocities(step, cfg):
    """Feature #2: Joint x and Angular Velocities"""
    # unpack
    hind_joints = cfg["hind_joints"]
    x_acceleration = cfg["x_acceleration"]
    angular_acceleration = cfg["angular_acceleration"]
    # compute velocities (& acceleration if wanted) for hind joints first
    for joint in hind_joints:
        step[joint + "Velocity"] = 0.0
        if x_acceleration:
            step[joint + "Acceleration"] = 0.0
        # step[joint + "Accel. Gradient"] = 0.0
    for joint in hind_joints:
        step.loc[:, joint + "Velocity"] = np.gradient(step.loc[:, joint + "x"])
        if x_acceleration:
            step.loc[:, joint + "Acceleration"] = np.gradient(
                step.loc[:, joint + "Velocity"]
            )
        # step.loc[:, joint + "Accel. Gradient"]= np.gradient(
        #     step.loc[:, joint + "Acceleration"])
    # compute velocities (& acceleration) for the angles too
    angle_cols = [c for c in step.columns if "Angle" in c]
    for angle in angle_cols:
        step[angle + " Velocity"] = 0.0  # space is correct here
        if angular_acceleration:
            step[angle + " Acceleration"] = 0.0
    for angle in angle_cols:
        step.loc[:, angle + " Velocity"] = np.gradient(step.loc[:, angle])
        if angular_acceleration:
            step.loc[:, angle + " Acceleration"] = np.gradient(
                step.loc[:, angle + " Velocity"]
            )
    return step


# ......................................................................................
# .................  helper functions b - sc length normalisation  .....................
# ......................................................................................


def normalise_one_steps_data(step, bin_num):
    """Normalise all steps to be of length 25 - uses define_bins

    Important
    ---------
    The input step here is a pd dataframe that only captures ONE stepcycle!
    (concatenation happens in exportsteps function)
    """
    normalised_step = pd.DataFrame()
    for c, col in enumerate(step.columns):
        thistrial = step[col]
        if c == 0:  # if first column, define bins anew
            bins = define_bins(int(len(thistrial)), bin_num)
        normtrial = np.zeros(bin_num)
        if type(bins[0]) == list:  # we need to average
            for i in range(bin_num):
                normtrial[i] = np.mean(thistrial.iloc[bins[i]])
        else:  # no need to average, repeat or assign
            for i in range(bin_num):
                normtrial[i] = thistrial.iloc[bins[i]]
        normalised_step[col] = normtrial
    return normalised_step


def define_bins(triallength, bin_num):
    """Define bins to know which indices move which bin for normalisation"""
    indices = list(range(triallength))
    bins = [[] for i in range(bin_num)]
    # moving average to make the trial shorter
    if triallength > bin_num:
        idx = 0
        for i in indices:
            idx += 1
            if i % bin_num == 0:
                idx = 0
            bins[idx].append(i)  # this means that bins[0] = [0, 25, 50, etc.]
        for i in range(len(bins)):
            for j in range(len(bins[i])):
                if i == 0:
                    bins[i][j] = j
                else:  # here we make sure it gets: bins[0] = [0, 1, 2, etc.]
                    bins[i][j] = j + np.max(bins[i - 1]) + 1  # +1 bc. idx from 0
    # repeat the same values to make the trial longer
    elif triallength < bin_num:
        final_list = []
        # use remainder to fill list after triallength val until len = bin_num
        # e.g. if triallength = 17 it goes 16, 17, 0, 1, 2, 3, 4, 5, 6
        for i in range(bin_num):
            idx = indices[i % len(indices)]
            final_list.append(idx)
        final_list.sort()  # need to sort (see above for initial order)
        bins = final_list
        if (len(bins) != bin_num) | (np.max(bins) != triallength - 1):
            raise Exception("Binning bugged (shouldn't happen) - contact me.")
    # if exactly 25 points originally
    else:
        for i in range(triallength):
            bins[i] = i
    return bins


# ......................................................................................
# ....................  helper functions c - xls file stuff  ...........................
# ......................................................................................


def compute_average_and_std_data(
    name, normalised_steps_data, bin_num, export_average_x
):
    """Export XLS tables that store all averages & std of y-coords & angles"""
    # initialise col of % of SC over time for plotting first
    percentages = [int(((s + 1) / bin_num) * 100) for s in range(bin_num)]
    average_data = pd.DataFrame(
        data=percentages, index=range(bin_num), columns=["SC Percentages"]
    )
    std_data = pd.DataFrame(
        data=percentages, index=range(bin_num), columns=["SC Percentages"]
    )
    sc_num = len(np.where(normalised_steps_data.index == 0)[0])
    for c, col in enumerate(normalised_steps_data.columns):
        if export_average_x:
            condition = (
                (not col.endswith("likelihood"))
                & (col != TIME_COL)
                & (col != "Flipped")
            )
        else:
            condition = (
                (not col.endswith("x"))
                & (not col.endswith("likelihood"))
                & (col != TIME_COL)
                & (col != "Flipped")
            )
        if condition:
            this_data = np.zeros([bin_num, sc_num])
            for s in range(sc_num):
                # with this_end it's bin_num & not bin_num -1 because iloc
                # does not include last index
                this_start = np.where(normalised_steps_data.index == 0)[0][s]
                this_end = np.where(normalised_steps_data.index == 0)[0][s] + bin_num
                this_data[:, s] = normalised_steps_data.iloc[this_start:this_end, c]
            this_average = np.mean(this_data, axis=1)
            this_std = np.std(this_data, axis=1)
            average_data[col] = this_average
            std_data[col] = this_std
    return average_data, std_data


def save_results_sheet(dataframe, save_to_xls, fullfilepath):
    """Save a csv or xls of results"""
    if save_to_xls:
        dataframe.to_excel(fullfilepath + ".xlsx", index=False)
    else:
        dataframe.to_csv(fullfilepath + ".csv", index=False)


# ......................................................................................
# ....................  helper functions d - miscellaneous  ............................
# ......................................................................................


def add_step_separators(dataframe, nanvector, numvector):
    """Add nan & num vector separators between step cycles to dataframes"""
    dataframe = pd.concat([dataframe, nanvector], axis=0)  # nan
    dataframe = pd.concat([dataframe, numvector], axis=0)  # num
    dataframe = pd.concat([dataframe, nanvector], axis=0)  # nan
    return dataframe


# %% local functions 4 - extract SCs from all_steps_data (# !!! NU - load XLS) and plot


# ..............................  master function  .............................

# A note on updated colour cyclers after pull request that was merged 20.06.2024
# => Using color palettes instead of colour maps as I had previously means that
#    we cycle through neighbouring colours
# => I initially implemented an "equally distant" approach.
# => So for viridis and n=2 (e.g. if 2 groups) it would be purple and yellow
#    (as far away as possible)
# => Now it is dark blue and green
# => Updated approach is aesthetically more pleasing IMO.
# => However it does have the risk of not being able to tell the colours in
#    some cases - e.g. if some accelerations are very overlapping.
# => But - because users can in theses cases just choose a colour palette that
#    in itself has categorical colours (Set1, Dark2, etc.) I still keep the new
#    behaviour
# => Nonetheless, in case you want to use the "old behaviour" at some point it
#    would be coded as commented out in plot_joint_y_by_x


def plot_results(info, results, folderinfo, cfg, plot_panel_instance):
    """Plot results - y coords by x coords & average angles over SC %"""
    # unpack
    fore_joints = cfg["fore_joints"]
    angles = cfg["angles"]
    all_steps_data = results["all_steps_data"]
    average_data = results["average_data"]
    std_data = results["std_data"]
    x_acceleration = cfg["x_acceleration"]
    angular_acceleration = cfg["angular_acceleration"]
    dont_show_plots = cfg["dont_show_plots"]
    if dont_show_plots:
        plt.switch_backend("Agg")

    # ....................0 - extract SCs from all_steps_data...........................
    sc_idxs = extract_sc_idxs(all_steps_data)
    cfg["sc_num"] = len(sc_idxs)  # add number of scs for plotting SE if wanted

    # .........................1 - y coords by x coords.................................
    plot_joint_y_by_x(all_steps_data, sc_idxs, info, cfg, plot_panel_instance)

    # ...............................2 - angles by time.................................
    if angles["name"]:
        plot_angles_by_time(all_steps_data, sc_idxs, info, cfg, plot_panel_instance)

    # ..........................3 - hindlimb stick diagram..............................
    plot_hindlimb_stickdiagram(all_steps_data, sc_idxs, info, cfg, plot_panel_instance)

    # ...........................4 - forelimb stick diagram.............................
    if fore_joints:
        plot_forelimb_stickdiagram(
            all_steps_data, sc_idxs, info, cfg, plot_panel_instance
        )

    # .....................5 - average joints' y over SC percentage.....................
    plot_joint_y_by_average_SC(average_data, std_data, info, cfg, plot_panel_instance)

    # ........................6 - average angles over SC percentage.....................
    if angles["name"]:
        plot_angles_by_average_SC(
            average_data, std_data, info, cfg, plot_panel_instance
        )

    # .................7 - average x velocities over SC percentage......................
    plot_x_velocities_by_average_SC(
        average_data, std_data, info, cfg, plot_panel_instance
    )

    # ..............8 - average angular velocities over SC percentage...................
    if angles["name"]:
        plot_angular_velocities_by_average_SC(
            average_data, std_data, info, cfg, plot_panel_instance
        )

    # ............optional - 9 - average x acceleration over SC percentage..............
    if x_acceleration:
        plot_x_acceleration_by_average_SC(
            average_data, std_data, info, cfg, plot_panel_instance
        )

    # .........optional - 10 - average angular acceleration over SC percentage..........
    if angles["name"]:
        if angular_acceleration:
            plot_angular_acceleration_by_average_SC(
                average_data, std_data, info, cfg, plot_panel_instance
            )

    # ........................optional - 11 - build plot panel..........................
    print("paramter", cfg["dont_show_plots"])
    if cfg["dont_show_plots"] is True:
        pass  # going on without building the plot window
    elif cfg["dont_show_plots"] is False:  # -> show plot panel
        # Destroy loading screen and build plot panel with all figures
        plot_panel_instance.destroy_plot_panel_loading_screen()
        plot_panel_instance.build_plot_panel()


# ..................................  inner functions  .................................


def extract_sc_idxs(all_steps_data):
    """0 - Prepare stepcycles on original-length (non-normalised) SCs"""
    # A note on all_steps_data & nan (see xls_separations):
    # ==> (Using range & iloc so we don't have to subtract 1 to nan-idxs)
    # ==> if there is more than 1 SC found, the first row of nan indicates the
    #     END of SC 1
    # ==> the last row of nan indicates the START of the last SC
    # ==> everything inbetween is alternatingly: (if you add 1 to nan-idx) the
    #     start of an SC + (if you subtract -1 to nan-idx) the end of that SC
    # ==> E.g.: separations[1]+1 is 1st idx of SC2 - separations[2]-1 is last
    #     idx of SC2
    check_col = all_steps_data.columns[0]  # take the first col to find nan-separators
    xls_separations = np.where(pd.isnull(all_steps_data[check_col]))[0]
    sc_idxs = []
    # the next line means that we have exactly one step, because we would not
    # build all_steps_data (and have results in the first place) if there was no step
    # Thus, if xls_sep. is empty (len=0) it means that no separations were
    # there, i.e., 1 SC
    if len(xls_separations) == 0:
        sc_idxs.append(range(0, len(all_steps_data)))  # I can do this bc. only 1 SC
    else:
        for b in range(len(xls_separations)):
            if b == 0:
                # SC1 - 0 to (not including) nan/end-idx
                sc_idxs.append(range(xls_separations[b]))
            elif b > 0:  # inbetween SCs
                if (b % 2) == 0:
                    sc_idxs.append(
                        range(
                            xls_separations[b - 1] + 1,  # add 1=start
                            xls_separations[b],
                        )
                    )
            # last SC - I can write it this way because b will always be odd if
            # it refers to the start of a stepcycle & thus: possibly the last
            if xls_separations[b] == xls_separations[-1]:
                sc_idxs.append(range(xls_separations[-1] + 1, len(all_steps_data)))
    return sc_idxs


def plot_joint_y_by_x(all_steps_data, sc_idxs, info, cfg, plot_panel_instance):
    """1 - Plot joints' y coordinates as a function of their x for each SC"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    convert_to_mm = cfg["convert_to_mm"]
    plot_joints = cfg["plot_joints"]
    sampling_rate = cfg["sampling_rate"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    sc_num = len(sc_idxs)
    f = [[] for _ in range(len(plot_joints))]
    ax = [[] for _ in range(len(plot_joints))]

    # plot
    for j, joint in enumerate(plot_joints):  # joint loop (figures)
        f[j], ax[j] = plt.subplots(1, 1)
        # What "Old" colormap approach would look like with seaborn
        # this_map = sns.color_palette(cfg["color_palette"], as_cmap=True)
        # ax[j].set_prop_cycle(plt.cycler("color", this_map(np.linspace(0, 1, sc_num))))
        ax[j].set_prop_cycle(  # New color palette approach
            plt.cycler("color", sns.color_palette(color_palette, sc_num))
        )
        ax[j].set_title(name + " - " + joint)
        x_col_idx = all_steps_data.columns.get_loc(joint + "x")
        y_col_idx = all_steps_data.columns.get_loc(joint + "y")
        time_col_idx = all_steps_data.columns.get_loc(TIME_COL)
        for s in range(sc_num):
            this_x = all_steps_data.iloc[sc_idxs[s], x_col_idx]
            this_y = all_steps_data.iloc[sc_idxs[s], y_col_idx]
            this_label = generate_sc_latency_label(
                all_steps_data, sc_idxs[s], sampling_rate, time_col_idx
            )
            ax[j].plot(this_x, this_y, label=this_label)
        ax[j].set_xlabel("x (pixel)")  # will be overwritten if we convert
        ax[j].set_ylabel("y (pixel)")
        # legend adjustments
        if legend_outside is True:
            ax[j].legend(
                fontsize=SC_LAT_LEGEND_FONTSIZE,
                loc="center left",
                bbox_to_anchor=(1, 0.5),
            )
        elif legend_outside is False:
            ax[j].legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
        if convert_to_mm:
            tickconvert_mm_to_cm(ax[j], "both")
        figure_file_string = " - " + joint + "y by x coordinates"
        save_figures(f[j], results_dir, name, figure_file_string)
        if dont_show_plots:
            plt.close(f[j])

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f[j])


def plot_angles_by_time(all_steps_data, sc_idxs, info, cfg, plot_panel_instance):
    """2 - Plot joints' angles as a function of time for each SC"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    angles = cfg["angles"]
    sampling_rate = cfg["sampling_rate"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    sc_num = len(sc_idxs)
    f = [[] for _ in range(len(angles["name"]))]
    ax = [[] for _ in range(len(angles["name"]))]

    # plot
    for a, angle in enumerate(angles["name"]):  # angle loop (figures)
        f[a], ax[a] = plt.subplots(1, 1)
        ax[a].set_prop_cycle(
            plt.cycler("color", sns.color_palette(color_palette, sc_num))
        )
        ax[a].set_title(name + " - " + angle)
        ax[a].set_ylabel("Angle")
        ax[a].set_xlabel("Time (s)")
        x_col_idx = all_steps_data.columns.get_loc(TIME_COL)
        y_col_idx = all_steps_data.columns.get_loc(angle + "Angle")
        time_col_idx = all_steps_data.columns.get_loc(TIME_COL)
        for s in range(sc_num):
            this_x = all_steps_data.iloc[sc_idxs[s], x_col_idx]
            this_y = all_steps_data.iloc[sc_idxs[s], y_col_idx]
            this_label = generate_sc_latency_label(
                all_steps_data, sc_idxs[s], sampling_rate, time_col_idx
            )
            ax[a].plot(this_x, this_y, label=this_label)
        # legend adjustments
        if legend_outside is True:
            ax[a].legend(
                fontsize=SC_LAT_LEGEND_FONTSIZE,
                loc="center left",
                bbox_to_anchor=(1, 0.5),
            )
        elif legend_outside is False:
            ax[a].legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
        figure_file_string = " - " + angle + "Angle by Time"
        save_figures(f[a], results_dir, name, figure_file_string)
        if dont_show_plots:
            plt.close(f[a])

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f[a])


def plot_hindlimb_stickdiagram(all_steps_data, sc_idxs, info, cfg, plot_panel_instance):
    """3 - Plot a stick diagram of the hindlimb"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    convert_to_mm = cfg["convert_to_mm"]
    plot_joints = cfg["plot_joints"]
    sampling_rate = cfg["sampling_rate"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    sc_num = len(sc_idxs)
    f, ax = plt.subplots(1, 1)
    color_cycle = plt.cycler("color", sns.color_palette(color_palette, sc_num))
    ax.set_prop_cycle(color_cycle)
    time_col_idx = all_steps_data.columns.get_loc(TIME_COL)

    # plot
    # => for timepoints from SC1 to SCend - plot(joint1x, joint1y)
    for s, this_color_dict in zip(range(sc_num), color_cycle):  # SC loop (colors)
        this_color = this_color_dict["color"][:3]
        this_label = generate_sc_latency_label(
            all_steps_data, sc_idxs[s], sampling_rate, time_col_idx
        )
        for i in sc_idxs[s]:  # loop over timepoints of current SC
            this_xs = list()  # for each timepoint, define joints' xy coord new
            this_ys = list()
            for joint in plot_joints:
                x_col_idx = all_steps_data.columns.get_loc(joint + "x")
                y_col_idx = all_steps_data.columns.get_loc(joint + "y")
                this_xs.append(all_steps_data.iloc[i, x_col_idx])
                this_ys.append(all_steps_data.iloc[i, y_col_idx])
            if i == sc_idxs[s][0]:
                ax.plot(this_xs, this_ys, color=this_color, label=this_label)
            else:
                ax.plot(this_xs, this_ys, color=this_color)
    ax.set_title(name + " - Hindlimb Stick Diagram")
    ax.set_xlabel("x (pixel)")
    ax.set_ylabel("y (pixel)")
    if convert_to_mm:
        tickconvert_mm_to_cm(ax, "both")
    # legend adjustments
    if legend_outside is True:
        ax.legend(
            fontsize=SC_LAT_LEGEND_FONTSIZE, loc="center left", bbox_to_anchor=(1, 0.5)
        )
    elif legend_outside is False:
        ax.legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
    figure_file_string = " - Hindlimb Stick Diagram"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_forelimb_stickdiagram(all_steps_data, sc_idxs, info, cfg, plot_panel_instance):
    """4 - Plot a stick diagram of the forelimb (for hindlimb stepcycles)"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    convert_to_mm = cfg["convert_to_mm"]
    fore_joints = cfg["fore_joints"]
    sampling_rate = cfg["sampling_rate"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    sc_num = len(sc_idxs)
    f, ax = plt.subplots(1, 1)
    color_cycle = plt.cycler("color", sns.color_palette(color_palette, sc_num))
    ax.set_prop_cycle(color_cycle)
    time_col_idx = all_steps_data.columns.get_loc(TIME_COL)

    # plot
    for s, this_color in zip(range(sc_num), color_cycle):  # SC loop (colors)
        this_color = this_color["color"][:3]
        this_label = generate_sc_latency_label(
            all_steps_data, sc_idxs[s], sampling_rate, time_col_idx
        )
        for i in sc_idxs[s]:
            this_xs = list()
            this_ys = list()
            for joint in fore_joints:
                x_col_idx = all_steps_data.columns.get_loc(joint + "x")
                y_col_idx = all_steps_data.columns.get_loc(joint + "y")
                this_xs.append(all_steps_data.iloc[i, x_col_idx])
                this_ys.append(all_steps_data.iloc[i, y_col_idx])
            if i == sc_idxs[s][0]:
                ax.plot(this_xs, this_ys, color=this_color, label=this_label)
            else:
                ax.plot(this_xs, this_ys, color=this_color)
    ax.set_title(name + " - Forelimb Stick Diagram")
    ax.set_xlabel("x (pixel)")
    ax.set_ylabel("y (pixel)")
    if convert_to_mm:
        tickconvert_mm_to_cm(ax, "both")
    # legend adjustments
    if legend_outside is True:
        ax.legend(
            fontsize=SC_LAT_LEGEND_FONTSIZE, loc="center left", bbox_to_anchor=(1, 0.5)
        )
    elif legend_outside is False:
        ax.legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
    figure_file_string = " - Forelimb Stick Diagram"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_joint_y_by_average_SC(average_data, std_data, info, cfg, plot_panel_instance):
    """5 - Plot joints' y as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    convert_to_mm = cfg["convert_to_mm"]
    bin_num = cfg["bin_num"]
    plot_SE = cfg["plot_SE"]
    sc_num = cfg["sc_num"]
    hind_joints = cfg["hind_joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(hind_joints)))
    )
    x = np.linspace(0, 100, bin_num)
    for joint in hind_joints:  # joint loop (lines)
        y_col_idx = average_data.columns.get_loc(joint + "y")
        this_y = average_data.iloc[:, y_col_idx]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col_idx] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col_idx]
        ax.plot(x, this_y, label=joint)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_title(name + " - Joint Y over average step cycle")
    ax.set_xlabel("Percentage")
    ax.set_ylabel("y (pixel)")
    if convert_to_mm:
        tickconvert_mm_to_cm(ax, "y")
    figure_file_string = " - Joint y-coord.s over average step cycle"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_angles_by_average_SC(average_data, std_data, info, cfg, plot_panel_instance):
    """6 - Plot Angles as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    plot_SE = cfg["plot_SE"]
    sc_num = cfg["sc_num"]
    angles = cfg["angles"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(angles["name"])))
    )
    x = np.linspace(0, 100, bin_num)
    ax.set_title(name + " - Joint angles over average step cycle")
    ax.set_xlabel("Percentage")
    ax.set_ylabel("Angle (degree)")
    for angle in angles["name"]:  # angle loop (lines)
        y_col_idx = average_data.columns.get_loc(angle + "Angle")
        this_y = average_data.iloc[:, y_col_idx]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col_idx] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col_idx]
        ax.plot(x, this_y, label=angle)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    figure_file_string = " - Joint angles over average step cycle"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_x_velocities_by_average_SC(
    average_data, std_data, info, cfg, plot_panel_instance
):
    """7 - Plot x velocities as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    convert_to_mm = cfg["convert_to_mm"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    sc_num = cfg["sc_num"]
    hind_joints = cfg["hind_joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(hind_joints)))
    )
    x = np.linspace(0, 100, bin_num)
    ax.set_title(name + " - Joint velocities over average step cycle")
    for joint in hind_joints:  # joint loop (lines)
        y_col_idx = average_data.columns.get_loc(joint + "Velocity")
        this_y = average_data.iloc[:, y_col_idx]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col_idx] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col_idx]
        ax.plot(x, this_y, label=joint)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel(
        "Velocity (x in pixel / " + str(int((1 / sampling_rate) * 1000)) + "ms)"
    )
    if convert_to_mm:
        tickconvert_mm_to_cm(ax, "y")
        ax.set_ylabel(
            "Velocity (x in cm / " + str(int((1 / sampling_rate) * 1000)) + "ms)"
        )
    figure_file_string = " - Joint velocities over average step cycle"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_angular_velocities_by_average_SC(
    average_data, std_data, info, cfg, plot_panel_instance
):
    """8 - Plot angular velocities as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    sc_num = cfg["sc_num"]
    angles = cfg["angles"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(angles["name"])))
    )
    x = np.linspace(0, 100, bin_num)
    ax.set_title(name + " - Angular velocities over average step cycle")
    ax.set_xlabel("Percentage")
    ax.set_ylabel("Velocity (degree / " + str(int((1 / sampling_rate) * 1000)) + "ms)")
    for angle in angles["name"]:  # angle loop (lines)
        y_col_idx = average_data.columns.get_loc(angle + "Angle Velocity")  # space
        this_y = average_data.iloc[:, y_col_idx]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col_idx] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col_idx]
        ax.plot(x, this_y, label=angle)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    figure_file_string = " - Angular velocities over average step cycle"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_x_acceleration_by_average_SC(
    average_data, std_data, info, cfg, plot_panel_instance
):
    """9 - (optional) Plot x acceleration as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    convert_to_mm = cfg["convert_to_mm"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    sc_num = cfg["sc_num"]
    hind_joints = cfg["hind_joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(hind_joints)))
    )
    x = np.linspace(0, 100, bin_num)
    ax.set_title(name + " - Joint accelerations over average step cycle")
    for joint in hind_joints:  # joint loop (lines)
        y_col_idx = average_data.columns.get_loc(joint + "Acceleration")  # no space
        this_y = average_data.iloc[:, y_col_idx]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col_idx] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col_idx]
        ax.plot(x, this_y, label=joint)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel(
        "Acceleration (x in pixel / " + str(int((1 / sampling_rate) * 1000)) + "ms)"
    )
    if convert_to_mm:
        tickconvert_mm_to_cm(ax, "y")
        ax.set_ylabel(
            "Acceleration (x in cm / " + str(int((1 / sampling_rate) * 1000)) + "ms)"
        )
    figure_file_string = " - Joint acceleration over average step cycle"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_angular_acceleration_by_average_SC(
    average_data, std_data, info, cfg, plot_panel_instance
):
    """10 - (optional) Plot angular acceleration as a function of average SC's
    percentage
    """

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    sc_num = cfg["sc_num"]
    angles = cfg["angles"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(angles["name"])))
    )
    x = np.linspace(0, 100, bin_num)
    ax.set_title(name + " - Angular accelerations over average step cycle")
    ax.set_xlabel("Percentage")
    ax.set_ylabel(
        "Acceleration (degree / " + str(int((1 / sampling_rate) * 1000)) + "ms)"
    )
    for angle in angles["name"]:  # angle loop (lines)
        y_col_idx = average_data.columns.get_loc(angle + "Angle Acceleration")
        this_y = average_data.iloc[:, y_col_idx]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col_idx] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col_idx]
        ax.plot(x, this_y, label=angle)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    figure_file_string = " - Angular acceleration over average step cycle"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def save_figures(figure, results_dir, name, figure_file_string):
    """Save figures as pngs to results_dir and as svgs to separate subfolders"""
    # pngs to results_dir
    figure.savefig(
        os.path.join(results_dir, name + figure_file_string + ".png"),
        bbox_inches="tight",
    )
    # svgs to subfolders
    svg_dir = os.path.join(results_dir, "SVG Figures")
    if not os.path.exists(svg_dir):
        os.makedirs(svg_dir)
    figure.savefig(
        os.path.join(svg_dir, name + figure_file_string + ".svg"), bbox_inches="tight"
    )


def tickconvert_mm_to_cm(axis, whichlabel):
    """Convert axis-ticks from mm (of data) to cm"""
    if whichlabel == "both":
        x_ticks = axis.get_xticks()
        x_ticklabels = []
        for t in x_ticks:
            x_ticklabels.append(str(round(t / 10, 2)))
        axis.set_xticks(x_ticks, labels=x_ticklabels)
        axis.set_xlabel("x (cm)")
    if (whichlabel == "both") | (whichlabel == "y"):
        y_ticks = axis.get_yticks()
        y_ticklabels = []
        for t in y_ticks:
            y_ticklabels.append(str(round(t / 10, 2)))
        axis.set_yticks(y_ticks, labels=y_ticklabels)
        axis.set_ylabel("y (cm)")


def generate_sc_latency_label(all_steps_data, this_sc_idx, sampling_rate, time_col_idx):
    if sampling_rate <= 100:
        float_precision = 2  # how many decimals we round to
    else:
        float_precision = 4
    this_label = (
        str(
            round(
                all_steps_data.iloc[this_sc_idx[0], time_col_idx],
                float_precision,
            )
        )
        + "-"
        + str(
            round(
                all_steps_data.iloc[this_sc_idx[-1], time_col_idx],
                float_precision,
            )
        )
        + "s"
    )
    return this_label


class PlotPanel:
    def __init__(self):
        self.figures = []
        self.current_fig_index = 0

    # .........................  loading screen  ................................
    def build_plot_panel_loading_screen(self):
        """Builds a loading screen that is shown while plots are generated"""
        # Build window
        self.loading_screen = ctk.CTkToplevel()
        self.loading_screen.title("Loading...")
        self.loading_screen.geometry("300x300")
        self.loading_label_strings = [
            "Plots are generated, please wait.",
            "Plots are generated, please wait..",
            "Plots are generated, please wait...",
        ]
        self.loading_label = ctk.CTkLabel(
            self.loading_screen, text=self.loading_label_strings[0]
        )
        self.loading_label.pack(pady=130, padx=40, anchor="w")

        # Animate the text
        self.animate(counter=1)

    # Cycle through loading labels to animate the loading screen
    def animate(self, counter):
        self.loading_label.configure(text=self.loading_label_strings[counter])
        self.loading_screen.after(
            500, self.animate, (counter + 1) % len(self.loading_label_strings)
        )

    def destroy_plot_panel_loading_screen(self):
        self.loading_screen.destroy()

    # .........................  plot panel   ................................
    def build_plot_panel(self):
        """Creates the window/"panel" in which the plots are shown"""
        # Set up of the plotpanel
        ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
        ctk.set_default_color_theme("green")  # Themes: blue , dark-blue, green
        self.plotwindow = ctk.CTkToplevel()
        self.plotwindow.title("AutoGaitA Plot Panel")

        # Set size to 50% of screen
        screen_width = self.plotwindow.winfo_screenwidth()
        window_width = int(screen_width * 0.5)
        # 0.75 to gain a ration of 1.333 (that of matplotlib figures) and 1.05 for toolbar + buttons
        window_height = window_width * 0.75 * 1.05
        self.plotwindow.geometry(f"{window_width}x{window_height}")

        # Adjust figures for the plot panel
        for fig in self.figures:
            # dpi adjusted to increase visibilty/readability
            fig.set_dpi(100)
            # to adjust margins within the figure
            # in case there are a lot of steps in one run (-> the legend is super long)
            # the figure won't be displayed properly.
            fig.set_constrained_layout(True)

        # Initialize the plot panel with the first figure
        self.plot_panel = FigureCanvasTkAgg(
            self.figures[self.current_fig_index], master=self.plotwindow
        )  # index used for buttons
        self.plot_panel.get_tk_widget().grid(
            row=0, column=0, padx=10, pady=10, sticky="nsew"
        )

        # Create toolbar frame and place it in the middle row
        self.toolbar_frame = tk.Frame(self.plotwindow)
        self.toolbar_frame.grid(row=1, column=0, sticky="ew")

        self.toolbar = NavigationToolbar2Tk(self.plot_panel, self.toolbar_frame)
        self.toolbar.update()

        # Create navigation buttons frame
        self.button_frame = tk.Frame(self.plotwindow)
        self.button_frame.grid(row=2, column=0, sticky="ew")

        self.prev_button = ctk.CTkButton(
            self.button_frame, text="<< Previous", command=self.show_previous
        )
        self.next_button = ctk.CTkButton(
            self.button_frame, text="Next >>", command=self.show_next
        )
        self.prev_button.grid(row=0, column=0, sticky="ew")
        self.next_button.grid(row=0, column=1, sticky="ew")

        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        # Configure grid layout
        self.plotwindow.grid_rowconfigure(0, weight=1)
        self.plotwindow.grid_rowconfigure(1, weight=0)
        self.plotwindow.grid_rowconfigure(2, weight=0)
        self.plotwindow.grid_columnconfigure(0, weight=1)

    def show_previous(self):
        if self.current_fig_index > 0:
            self.current_fig_index -= 1
            self.update_plot_and_toolbar()

    def show_next(self):
        if self.current_fig_index < len(self.figures) - 1:
            self.current_fig_index += 1
            self.update_plot_and_toolbar()

    def update_plot_and_toolbar(self):
        # Clear the current plot panel
        self.plot_panel.get_tk_widget().grid_forget()

        # Update the plot panel with the new figure
        self.plot_panel = FigureCanvasTkAgg(
            self.figures[self.current_fig_index], master=self.plotwindow
        )
        self.plot_panel.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.plot_panel.draw()

        # Destroy toolbar and create a new one
        # (This has to be done, otherwise the toolbar won't function for a new plot)
        self.toolbar.destroy()
        self.toolbar = NavigationToolbar2Tk(self.plot_panel, self.toolbar_frame)
        self.toolbar.update()


# %% local functions 5 - print finish


def print_finish(info, cfg):
    """Print that we finished this program"""
    print("\n***************************************************")
    print("* GAITA FINISHED - RESULTS WERE SAVED HERE:       *")
    print("* " + info["results_dir"] + " *")
    print("***************************************************")


# %% what happens if we just hit run
if __name__ == "__main__":
    dlc_info_message = (
        "\n*************\nnot like this\n*************\n"
        + "You are trying to execute autogaita.dlc as a script, but that is not "
        + "possible.\nIf you prefer a non-GUI approach, please either: "
        + "\n1. Call this as a function, i.e. autogaita.dlc(info, folderinfo, cfg)"
        + "\n2. Use the single or multirun scripts in the batchrun_scripts folder"
    )
    print(dlc_info_message)

# %% imports
import os
import sys
import shutil
import json
import pandas as pd
import numpy as np
import math
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
import customtkinter as ctk
import warnings
import seaborn as sns

# %% constants
matplotlib.use("agg")
# Agg is a non-interactive backend for plotting that can only write to files
# this is used to generate and save the plot figures
# later a tkinter backend (FigureCanvasTkAgg) is used for the plot panel
# increase resolution of figures
plt.rcParams["figure.dpi"] = 300
# general
LEGS = ["left", "right"]
LEGS_COLFORMAT = [", left ", ", right "]
OUTPUTS = LEGS + ["both"]
ISSUES_TXT_FILENAME = "Issues.txt"  # filename to which we write issues-info
CONFIG_JSON_FILENAME = "config.json"  # filename to which we write cfg-infos
# sc extraction
SCXLS_SUBJCOLS = [
    "Participant",
    "participant",
    "Animal",
    "animal",
    "Subject",
    "subject",
    "ID",
    "id",
]  # SC XLS info
SCXLS_LEGCOLS = ["Leg", "leg", "Legs", "legs", "Side", "side"]
SCXLS_RUNCOLS = ["Run", "run", "Runs", "runs", "Trial", "trial", "Trials", "trials"]
SCXLS_SCCOLS = ["SC Number", "SC number", "sc number", "SC Num", "sc num", "SC num"]
SWINGSTART_COL = "Swing (ti)"
STANCEEND_COL = "Stance (te)"
# simulate walking direction being left to right
SEARCH_WIN_TURN_TIME = 500  # 5 seconds
# export results as xlsx
ORIGINAL_XLS_FILENAME = " - Original Stepcycles"  # filenames of sheet exports
NORMALISED_XLS_FILENAME = " - Normalised Stepcycles"
AVERAGE_XLS_FILENAME = " - Average Stepcycle"
STD_XLS_FILENAME = " - Standard Devs. Stepcycle"
SEPARATOR_IDX = 1  # idx of dfs whenever we have separator rows
DF_TIME_COL = "Time"
DF_LEG_COL = "Leg"
DF_SCPERCENTAGE_COL = "SC Percentages"
EXCLUDED_COLS_IN_AV_STD_DFS = [DF_TIME_COL, DF_LEG_COL]
REORDER_COLS_IN_STEP_NORMDATA = [DF_TIME_COL, DF_LEG_COL]
# plot stuff
SC_LAT_LEGEND_FONTSIZE = 6
ANGLE_PLOTS_YLIMITS = [80, 190]
STICK_LINEWIDTH = 0.5
# Plot GUI colors
FG_COLOR = "#c0737a"  # dusty rose
HOVER_COLOR = "#b5485d"  # dark rose

# %%
# ......................................................................................
# ........................  an important note for yourself  ............................
# ......................................................................................
# Please read this (& check_data_column_names!) when you are confused about col-names.
# It's a bit tricky in this code, see comments & doc about this issue in:
# 1. check_and_fix_cfg_strings (why am I here, read the others)
# 2. check_data_column_names (read me first)
# 3. add_features (then me)
# 4. plot_results (me if you really have to)
# => mainly (from 2.):
# Bodyside-specific colnames have to end WITHOUT a space (because we concat
# "name" + ", leg " + "Z" - so leg ends with a space)
# Bodyside-nonspecific colnames have to end WITH a space (because we concat "name "
# + "Z" so name has to end with a space)
# ......................................................................................


# %% main program


def simi(info, folderinfo, cfg):
    """Runs the main program for a given subject's run

    Procedure
    ---------
    1) import & preparation
    2) step cycle extraction
    3) z-normalisation, y-flipping & feature computation for individual step cycles
    4) step cycle normalisaion, dataframe creation & XLS-exportation
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

    # ...............................  preparation  ....................................
    data, global_Y_max = some_prep(info, folderinfo, cfg)
    if (data is None) & (global_Y_max is None):
        return

    # ..........................  step-cycle extraction  ...............................
    all_cycles = extract_stepcycles(data, info, folderinfo, cfg)
    all_cycles = check_stepcycles(all_cycles, info)
    if not all_cycles:  # only None if both leg's SCs were None
        if cfg["dont_show_plots"] is False:  # otherwise stuck at loading
            plot_panel_instance.destroy_plot_panel()
        return

    # ......  main analysis: y-flipping, features, df-creation & exports  ..............
    results = analyse_and_export_stepcycles(data, all_cycles, global_Y_max, info, cfg)

    # ..................................  plots  .......................................
    plot_results(results, all_cycles, info, cfg, plot_panel_instance)

    # ..............................  print finish  ....................................
    print_finish(info, cfg)


# %% local functions 1 - preparation


# ................................  main function  .....................................
def some_prep(info, folderinfo, cfg):
    """Preparation of the data for later analyses"""
    # ............................  unpack stuff  ......................................
    name = info["name"]
    results_dir = info["results_dir"]
    postname_string = folderinfo["postname_string"]
    sampling_rate = cfg["sampling_rate"]
    normalise_height_at_SC_level = cfg["normalise_height_at_SC_level"]
    analyse_average_y = cfg["analyse_average_y"]

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
    issue_txt_path = os.path.join(results_dir, ISSUES_TXT_FILENAME)
    if os.path.exists(issue_txt_path):
        os.remove(issue_txt_path)
    # read data
    # => note that this catches xls and xlsx files. can do this since we previously
    #    handle cases of both being @ root_dir in move_data_to_folders function
    # => using empty data df & empty string for error handling
    data = pd.DataFrame(data=None)
    data_duplicate_error = ""
    for filename in os.listdir(results_dir):
        if name + postname_string + ".xls" in filename:
            if data.empty:
                try:
                    data = pd.read_excel(os.path.join(results_dir, filename))
                except:
                    data = pd.read_excel(
                        os.path.join(results_dir, filename), engine="openpyxl"
                    )
            else:
                data_duplicate_error = (
                    "\n******************\n! CRITICAL ERROR !\n******************\n"
                    + "Two DATA xls-files found for "
                    + name
                    + "!\nPlease ensure your root directory only has one "
                    + "datafile per ID"
                )

    # ............................  import data  .......................................
    import_error_message = ""  # prep stuff for error handling
    if data_duplicate_error:
        import_error_message += data_duplicate_error
    if data.empty:
        import_error_message += (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "Unable to load an xls/xlsx file with data for "
            + name
            + "!\nTry again!"
        )
    if import_error_message:  # see if there was any issues with import, if so: stop
        print(import_error_message)
        write_issues_to_textfile(import_error_message, info)
        return

    # ................  final data checks, conversions & additions  ....................
    # IMPORTANT
    # ---------
    # MAIN TESTS OF USER-INPUT VALIDITY OCCUR HERE!
    cfg = test_and_expand_cfg(data, cfg, info)
    if cfg == (None, None):  # joints were empty
        return (None, None)  # => return the tuple bc. some prep returns 2 variables
    joints = cfg["joints"]
    angles = cfg["angles"]
    # store config json file @ group path
    # !!! NU - do this @ ID path
    group_path = results_dir.split(name)[0]
    config_json_path = os.path.join(group_path, CONFIG_JSON_FILENAME)
    config_vars_to_json = {
        "sampling_rate": sampling_rate,
        "normalise_height_at_SC_level": normalise_height_at_SC_level,
        "joints": joints,
        "angles": angles,
        "analyse_average_y": analyse_average_y,
        "tracking_software": "Simi",
    }
    # note - using "w" will overwrite/truncate file, thus no need to remove it if exists
    with open(config_json_path, "w") as config_json_file:
        json.dump(config_vars_to_json, config_json_file, indent=4)

    # For some reason there are two Time = 0 @ start. Take the second/last.
    if len(np.where(data[DF_TIME_COL] == 0)[0]) > 1:
        real_start_idx = np.where(data[DF_TIME_COL] == 0)[0][-1]
        data = data.iloc[real_start_idx:, :]
        data.index = range(len(data))  # update index
    try:
        data = data.astype(float)
    except:
        # simi sometimes does weird things with their data (e.g., storing 99cm as 0,99
        # and 1 metre 10cm something something as 101.222.333 or so) - catch it
        unable_to_convert_message = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "Unable to convert data to numbers for "
            + name
            + ".\nThis is likely due to inconsistent or wrong decimal separators in "
            + "some columns."
            + "\nTry again!"
        )
        print(unable_to_convert_message)
        write_issues_to_textfile(unable_to_convert_message, info)
        raise ValueError(unable_to_convert_message)
    data[DF_TIME_COL] = data.index * (1 / sampling_rate)

    # Standardise y columns to be positive & afterwards save global y_max for flipping
    y_cols = [col for col in data.columns if col.endswith("Y")]
    global_Y_min = min(data[y_cols].min())
    if global_Y_min < 0:
        data[y_cols] += abs(global_Y_min)
    global_Y_max = max(data[y_cols].max())

    # Finally, standardise all Z columns to global Z minimum being zero
    z_cols = [col for col in data.columns if col.endswith("Z")]  # Find all Z cols
    global_Z_min = min(data[z_cols].min())  # Compute global z min
    data[z_cols] -= global_Z_min  # Subtract global Z min from all Z cols

    return data, global_Y_max

    # ..............................  sanity checks  ...................................
    # below are some old & less efficient ways of computing y min / max & z min
    # => I saved these so you can put breakpoints and copy paste the sanity checks on
    #    (e.g.) data_copy = data.copy() and then check equivalence of dfs using
    #    data.equals(data_copy)

    # 1 - SANITY CHECK FOR Y MIN
    # global_y_min = float("inf")
    # for col in data_copy.columns:
    #     if col.endswith("Y"):
    #         if min(data_copy[col]) < global_y_min:
    #             global_y_min = min(data_copy[col])
    # if global_y_min < 0:
    #     for col in data_copy.columns:
    #         if col.endswith("Y"):
    #             data_copy[col] = data_copy[col] + abs(global_y_min)

    # 2 - SANITY CHECK FOR Y MAX
    # global_Y_max = 0
    # for col in data.columns:
    #     if col.endswith("Y"):
    #         if max(data[col]) > global_Y_max:
    #             global_Y_max = max(data[col])

    # 3 - SANITY CHECK FOR Z MIN
    # global_Z_min = float("inf")
    # for col in data.columns:
    #     if col.endswith("Z"):
    #         if min(data[col]) < global_Z_min:
    #             global_Z_min = min(data[col])
    # for col in data.columns:
    #     if col.endswith("Z"):
    #         data[col] = data[col] - global_Z_min  # a neg num - a neg num = pos num


# ..............................  helper functions  ....................................


def move_data_to_folders(info, folderinfo):
    """Copy data to new results_dir"""
    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    root_dir = folderinfo["root_dir"]
    postname_string = folderinfo["postname_string"]
    # create res dir (has to be first thing because of using issues.txt file here)
    os.makedirs(results_dir)
    # check if there is an xls and an xlsx table for name
    xls_flag = False
    xlsx_flag = False
    for filename in os.listdir(root_dir):
        if not postname_string:
            if filename.endswith(name + ".xls"):
                xls_flag = True
            elif filename.endswith(name + ".xlsx"):
                xlsx_flag = True
        else:
            if filename.endswith(name + postname_string + ".xls"):
                xls_flag = True
            elif filename.endswith(name + postname_string + ".xlsx"):
                xlsx_flag = True
    if (xls_flag is True) & (xlsx_flag is True):
        two_table_warning = (
            "\n***********\n! WARNING !\n***********\n"
            + "We found an xls as well as an xlsx file for ID: "
            + name
            + "!\nWe will use the .xlsx file -  fix & re-run if this is unwanted!"
        )
        print(two_table_warning)
        write_issues_to_textfile(two_table_warning, info)
    # move correct xls(x) file to it
    for filename in os.listdir(root_dir):
        if name + postname_string + ".xls" in filename:
            if filename.endswith(".xls"):
                if xlsx_flag is False:
                    shutil.copy2(
                        os.path.join(root_dir, filename),
                        os.path.join(results_dir, filename),
                    )
            else:
                shutil.copy2(
                    os.path.join(root_dir, filename),
                    os.path.join(results_dir, filename),
                )


def test_and_expand_cfg(data, cfg, info):
    """Test some important cfg variables and add new ones based on them

    Procedure
    ---------
    Check that no strings are empty
    Check that all strings end with a space character
    Check that all features are present in the dataset
    Add plot_joints & direction_joint
    Make sure to set dont_show_plots to True if Python is not in interactive mode
    """

    # run the 3 tests first
    for cfg_key in ["angles", "joints"]:
        cfg[cfg_key] = check_and_fix_cfg_strings(data, cfg, cfg_key, info)

    # add plot_joints - used for average plots & stick diagram
    joints = cfg["joints"]
    if cfg["plot_joint_number"] > len(joints):  # 1) joints to plot in detail
        this_message = (
            "\n***********\n! WARNING !\n***********\n"
            + "You asked us to plot more joints than available!"
            + "\nNumber of joints to plot: "
            + str(cfg["plot_joint_number"])
            + "\nNumber of selected joints: "
            + str(len(joints))
            + "\n\nWe'll just plot the most we can :)"
        )
        write_issues_to_textfile(this_message, info)
        print(this_message)
        cfg["plot_joints"] = joints
    else:
        cfg["plot_joints"] = joints[: cfg["plot_joint_number"]]

    # add direction_joint - used to determine gait direction
    if not joints:  # no valid string after above cleaning
        no_joint_message = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "After testing your joint names, no valid joint was left to "
            + "perform gait direction checks on.\nPlease make sure that at least one "
            + "joint is provided & try again!"
        )
        write_issues_to_textfile(no_joint_message, info)
        print(no_joint_message)
        return (None, None)  # returning tuple bc. some_prep returns 2 variables
    if joints[0] + "Y" in data.columns:
        cfg["direction_joint"] = joints[0] + "Y"
    else:
        cfg["direction_joint"] = joints[0] + LEGS_COLFORMAT[0] + "Y"

    return cfg


def check_and_fix_cfg_strings(data, cfg, cfg_key, info):
    """Check and fix strings in our joint & angle lists so that:
    1) They don't include empty strings
    2) All strings end with the space character (since we do string + "y")
    3) All strings are valid columns of the DLC dataset

    Note
    ----
    This is a bit more involved here than in _dlc since we have to check whether
    a given string is body-specific (e.g., Midfoot, left Z) or not (e.g., Pelvis Z)
    => Based on this the string of the feature itself has to either end or not end with
       a space character (see doc of check_data_column_names for more info)
    """

    # work on this variable (we return to cfg[key] outside of here)
    string_variable = cfg[cfg_key]

    # easy checks: lists
    if type(string_variable) is list:
        string_variable = [string for string in string_variable if string]
        # note that below local func. DOES NOT CLEAN the list - it only corrects space
        # characters and returns invalid_idxs that we'll use next to clean the list
        string_variable, invalid_joint_idxs = check_data_column_names(
            data, string_variable
        )
        # if user gave us joints we didnt find, write, print & save error message
        if invalid_joint_idxs:  # if none found, func returns an empty list (falsey!)
            # backup dirty variable
            dirty_string_variable = string_variable
            # now clean the list
            string_variable = [
                item
                for i, item in enumerate(string_variable)
                if i not in invalid_joint_idxs
            ]
            # now print & save erroneous & remaining joints
            joint_error = (
                "\n***********\n! WARNING !\n***********\n"
                + "\nYou entered joint-names that are not included in your dataset:"
            )
            for idx in invalid_joint_idxs:
                joint_error += "\n" + dirty_string_variable[idx]
            joint_error += "\n\nWe removed these and will analyse the remaining ones:"
            for string in string_variable:
                joint_error += "\n" + string
            joint_error += (
                "\n\nNote that capitalisation matters."
                + "\nIf you are running a batch analysis, we'll use this updated cfg "
                + "throughout.\nCheck out the config.json file for the full cfg used."
            )
            print(joint_error)
            write_issues_to_textfile(joint_error, info)

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
            this_keys_missing_strings = ""
            string_variable[key], this_keys_invalid_idxs = check_data_column_names(
                data, string_variable[key]
            )
            if this_keys_invalid_idxs:  # if none found this is an empty list (falsey!)
                invalid_idxs.append(this_keys_invalid_idxs)
                if not this_keys_missing_strings:  # first occurance
                    this_keys_missing_strings += "\nAngle's " + key + " key: "
                for idx in this_keys_invalid_idxs:
                    this_keys_missing_strings += (
                        string_variable[key][idx] + " (#" + str(idx + 1) + ") / "
                    )
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
            if type(invalid_idxs[0]) is list:  # if needed, flatten to a list of values
                invalid_idxs = [item for sublist in invalid_idxs for item in sublist]
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


def check_data_column_names(data, string_variable):
    """Checks if user-input is present in data columns and changes space-characters
    accordingly
    => Bodyside-specific colnames have to end WITHOUT a space (because we concat
       "name" + ", leg " + "Z" - so leg ends with a space)
    => Bodyside-nonspecific colnames have to end WITH a space (because we concat "name "
       + "Z" so name has to end with a space)

    IMPORTANT NOTE
    --------------
    This function does NOT REMOVE invalid strings from the list!!! It is by design that
    you have to remove those outside of this function using invalid_joint_idx.
    HOWEVER IT DOES fix the space-character thingy for those strings THAT ARE IN THE
    DATASET!
    """
    invalid_joint_idxs = []
    for s, string in enumerate(string_variable):
        # if a string is ending with a space, see if it is non-bodyside-specific
        # if that's not the case, remove the space
        if string.endswith(" "):
            if string + "Y" in data.columns:
                pass
            elif string[:-1] + LEGS_COLFORMAT[0] + "Y" in data.columns:
                string_variable[s] = string[:-1]
            else:
                invalid_joint_idxs.append(s)
        # if a string is not ending with a space, see if it should
        else:
            if string + LEGS_COLFORMAT[0] + "Y" in data.columns:
                pass
            elif string + " Y" in data.columns:
                string_variable[s] = string + " "
            else:
                invalid_joint_idxs.append(s)
    return string_variable, invalid_joint_idxs


def write_issues_to_textfile(message, info):
    """If there are any issues with this data, inform the user in this file"""
    textfile = os.path.join(info["results_dir"], ISSUES_TXT_FILENAME)
    with open(textfile, "a") as f:
        f.write(message)


# %% local functions 2 - SC extraction (reading user-provided SC Table)


# ...............................  outer function  .....................................
def extract_stepcycles(data, info, folderinfo, cfg):
    """Read XLS file with SC annotations, find correct row & return all_cycles"""
    # unpack
    root_dir = folderinfo["root_dir"]
    sctable_filename = folderinfo["sctable_filename"]

    # load the table - try some filename & ending options
    if os.path.exists(os.path.join(root_dir, sctable_filename)):
        SCdf = pd.read_excel(os.path.join(root_dir, sctable_filename))
    elif os.path.exists(os.path.join(root_dir, sctable_filename) + ".xlsx"):
        SCdf = pd.read_excel(os.path.join(root_dir, sctable_filename) + ".xlsx")
    elif os.path.exists(os.path.join(root_dir, sctable_filename) + ".xls"):
        SCdf = pd.read_excel(os.path.join(root_dir, sctable_filename) + ".xls")
    else:
        no_sc_table_message = (
            "No Annotation Table found! sctable_filename has to be @ root_dir"
        )
        raise Exception(no_sc_table_message)

    # extract & return all_cycles
    all_cycles = {"left": [], "right": []}
    for legname in LEGS:
        all_cycles[legname] = read_SC_info(data, SCdf, info, legname, cfg)
    return all_cycles


# ...........................  inner (main) function  ..................................
def read_SC_info(data, SCdf, info, legname, cfg):
    """Read table, and create a list of start/end indices of a leg's SCs"""
    # ...............................  preparation  ....................................
    # unpack
    name = info["name"]
    sampling_rate = cfg["sampling_rate"]

    # very first sanity check - see if table columns are labelled correctly
    valid_col_flags = [
        False,
        False,
        False,
        False,
    ]  # for user typos
    header_columns = ["", "", "", ""]
    for h, header in enumerate(
        [SCXLS_SUBJCOLS, SCXLS_LEGCOLS, SCXLS_RUNCOLS, SCXLS_SCCOLS]
    ):
        for header_col in header:
            if header_col in SCdf.columns:
                valid_col_flags[h] = True
                header_columns[h] = header_col
                break
    if not all(valid_col_flags):
        this_message = (
            "\n******************\n! CRITICAL ERROR !"
            + "\n******************\n"
            + "Annotation Table Column names are wrong!\n"
            + "Check Instructions!"
        )
        print(this_message)
        write_issues_to_textfile(this_message, info)
        return
    # some prep
    leg_col = SCdf.columns.get_loc(header_columns[1])  # INDEXING! (see list above)
    run_col = SCdf.columns.get_loc(header_columns[2])
    sc_col = SCdf.columns.get_loc(header_columns[3])
    # first find the rows of this leg
    # a. find overall start row of this subject
    start_row = SCdf.index[SCdf[header_columns[0]] == name]
    if start_row.empty:
        this_message = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "\nNo timestamp information found for ID: "
            + name
            + "\nCheck your Annotation Table & try again!"
        )
        print(this_message)
        write_issues_to_textfile(this_message, info)
        return
    # b. check if this subjects ID was found more than once, if so - stop!
    if len(start_row) > 1:
        this_message = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "\nID "
            + name
            + " was found more than once in ID column!"
            + "\nCheck your Annotation Table & try again!"
        )
        print(this_message)
        write_issues_to_textfile(this_message, info)
        return
    # c. find start row of current leg (whileloop works for both legs)
    while SCdf.iloc[start_row, leg_col].values[0] != legname:
        start_row += 1
    end_row = start_row
    while (type(SCdf.iloc[end_row, run_col].values[0]) == int) & (
        end_row != len(SCdf) - 1
    ):
        end_row += 1
    # quick sanity checks that user input was correct
    if end_row != start_row:
        if not np.isnan(SCdf.iloc[end_row, leg_col].values[0]):
            this_message = (
                "\n******************\n! CRITICAL ERROR !\n******************\n"
                + "\nID: "
                + name
                + ", Leg: "
                + legname
                + "\nRun & Leg columns of Annotation "
                + "Table seem wrong! \nYou need to have an "
                + "empty row before each new leg or subject!"
                + "\nCheck your table & make sure that it "
                + "matches our template."
            )
            print(this_message)
            write_issues_to_textfile(this_message, info)
            return  # return None for this leg if formatting bad

    # ..............................  main xls read  ...................................
    # extract all runs of this subject / leg combination
    # ==> note that slicing behaves differently based on whether end_row is
    #     the last row of the dataframe or not. handle this here. Particularly:
    # ==> end_row is 1) first row of new subject or 2) SC end. If 1) we want
    #     end_row to not be included, if 2) we want it to be included
    # case 1) - end_row is nan row after last SC. iloc slicing is exclusive for endidx!
    if end_row[0] != (len(SCdf) - 1):
        runs = SCdf.iloc[int(start_row[0]) : int(end_row[0]), run_col]
    # case 2) - end_row is last row df. iloc with [startidx:, col] = inclusive endrow!
    else:
        runs = SCdf.iloc[int(start_row[0]) :, run_col]

    # find out the total number of scs & see if it matches user-provided values
    # (handle same two cases as above for runs with if/else)
    if end_row[0] != (len(SCdf) - 1):
        user_scnum = sum(SCdf.iloc[int(start_row[0]) : int(end_row[0]), sc_col])
    else:
        user_scnum = sum(SCdf.iloc[int(start_row[0]) :, sc_col])
    total_scnum = 0  # for sanity check (before warning-message below)
    run_scnums = [None for s in range(len(runs))]
    for r, run in enumerate(runs):
        run_row = runs[runs == run].index
        run_scnums[r] = 0
        for column in SCdf.columns:
            if STANCEEND_COL in column:
                if np.isnan(SCdf[column][run_row].values[0]) == False:
                    total_scnum += 1
                    run_scnums[r] += 1
    if user_scnum != total_scnum:  # warn the user, take the values we found
        this_message = (
            "\n***********\n! WARNING !\n***********\n"
            + "\nID: "
            + name
            + ", Leg: "
            + legname
            + "\nMismatch between SC num. of XLS SC Column ("
            + str(user_scnum)
            + ") & \nSCs with values in Swing/"
            + "Stance columns ("
            + str(total_scnum)
            + ")!"
            + "\nWe used all valid swing/stance entries ("
            + str(total_scnum)
            + ")."
            + "\nCheck your table."
        )
        print(this_message)
        write_issues_to_textfile(this_message, info)

    # ...........................  idxs to all_cycles  .................................
    # use value we found, loop over all runs, loop over SCs within a run
    # => all_cycles is a list of len = number of runs with lists within that having
    #    len = number of SCs of each run
    all_cycles = [[] for r in range(len(run_scnums))]  # run, not user!
    for r in range(len(run_scnums)):
        all_cycles[r] = [[None, None] for s in range(run_scnums[r])]
    for r, run in enumerate(runs):
        run_row = runs[runs == run].index
        for s in range(run_scnums[r]):
            if s == 0:
                start_col = SCdf.columns.get_loc(SWINGSTART_COL)
                end_col = SCdf.columns.get_loc(STANCEEND_COL)
            else:
                # str(s) because colnames match s for s>0 (& @else our loop starts @ 1)!
                start_col = SCdf.columns.get_loc(SWINGSTART_COL + "." + str(s))
                end_col = SCdf.columns.get_loc(STANCEEND_COL + "." + str(s))
            # time as floats
            start_in_s = float(SCdf.iloc[run_row, start_col].values[0])
            end_in_s = float(SCdf.iloc[run_row, end_col].values[0])
            # see if we are rounding to fix inaccurate user input
            # => account for python's float precision leading to inaccuracies
            # => two important steps here (sanity_check_vals only used for these checks)
            # 1. round to 10th decimal to fix python making
            #    3211.999999999999999995 out of 3212
            sanity_check_start = round(start_in_s * sampling_rate, 10)
            sanity_check_end = round(end_in_s * sampling_rate, 10)
            # 2. comparing abs(sanity check vals) to 1e-7 just to be 1000% sure
            if (abs(sanity_check_start % 1) > 1e-7) | (
                abs(sanity_check_end % 1) > 1e-7
            ):
                round_message = (
                    "\n***********\n! WARNING !\n***********\n"
                    + "SC latencies of "
                    + str(start_in_s)
                    + "s to "
                    + str(end_in_s)
                    + "s were not provided in units of the frame rate!"
                    + "\nWe thus use the previous possible frame(s)."
                    + "\nDouble check if this worked as expected or fix annotation table!"
                )
                print(round_message)
                write_issues_to_textfile(round_message, info)
            # assign to all_cycles (note int() rounds down!)
            all_cycles[r][s][0] = int(start_in_s * sampling_rate)
            all_cycles[r][s][1] = int(end_in_s * sampling_rate)
            # check if we are in data bounds
            if (all_cycles[r][s][0] in data.index) & (
                all_cycles[r][s][1] in data.index
            ):
                pass
            else:
                all_cycles[r][s] = [None, None]  # so they can be cleaned later
                this_message = (
                    "\n***********\n! WARNING !\n***********\n"
                    + legname
                    + " leg"
                    + " - Run #"
                    + str(r + 1)
                    + " - SC #"
                    + str(s + 1)
                    + " is out of data-bounds - Skipping!"
                )
                print(this_message)
                write_issues_to_textfile(this_message, info)

    # ............................  clean all_cycles  ..................................
    # check if we skipped latencies because they were out of data-bounds
    all_cycles = check_cycle_out_of_bounds(all_cycles)
    if all_cycles:  # can be None if all SCs were out of bounds
        # check if there are any duplicates (e.g., SC2's start-lat == SC1's end-lat)
        all_cycles = check_cycle_duplicates(all_cycles)
        # check if user input progressively later latencies
        all_cycles = check_cycle_order(all_cycles, info, legname)
        # NOTE for future self
        # => If you are considering to remove empty lists from run_cycles note that we
        #    need them for the case of Runs 1 & 3 having SCs but 2 not having any
        # => Otherwise SC-level plots arent plotted correctly (ie Run3 could easily
        #    look like Run2 - we need an empty subplot panel for run2 and thus an empty
        #    list!)
    return all_cycles


# ..............................  helper functions  ....................................
def check_cycle_out_of_bounds(all_cycles):
    """Check if user provided SC latencies that were not in video/data bounds"""
    clean_cycles = None
    for r, run_cycles in enumerate(all_cycles):
        for c, cycle in enumerate(run_cycles):
            # below checks if values are any type of int (just in case int-type should
            # for some super random reason change...)
            if isinstance(cycle[0], (int, np.integer)) & isinstance(
                cycle[1], (int, np.integer)
            ):
                if clean_cycles is None:
                    clean_cycles = [[] for s in range(len(all_cycles))]
                clean_cycles[r].append(cycle)
    return clean_cycles


def check_cycle_duplicates(all_cycles):
    """Check if there are any duplicate SC latencies.
    This would break our plotting functions, which use .loc on all_steps_data - thus,
    all indices of all_cycles have to be unique. If any duplicates found, add one
    datapoint to the start latency.
    """
    for r, run_cycles in enumerate(all_cycles):
        for c, cycle in enumerate(run_cycles):
            if c > 0:
                if cycle[0] == run_cycles[c - 1][1]:
                    all_cycles[r][c][0] += 1
    return all_cycles


def check_cycle_order(all_cycles, info, legname):
    """Check if user input flawed SC latencies

    Two cases
    1. Start latency earlier than end latency of previous SC
    2. End latency earlier then start latency of current SC
    """

    clean_cycles = [[] for s in range(len(all_cycles))]
    current_max_time = 0  # outside of for loops so it persists across runs
    for r, run_cycles in enumerate(all_cycles):
        for c, cycle in enumerate(run_cycles):
            if cycle[0] > current_max_time:
                if cycle[1] > cycle[0]:
                    clean_cycles[r].append(cycle)  # only append if both tests passed
                    current_max_time = cycle[1]
                else:
                    this_message = (
                        "\n***********\n! WARNING !\n***********\n"
                        + legname
                        + " - Run #"
                        + str(r + 1)
                        + " - SC #"
                        + str(c + 1)
                        + " has a later start than end latency - Skipping!"
                    )
                    print(this_message)
                    write_issues_to_textfile(this_message, info)
            else:
                this_message = (
                    "\n***********\n! WARNING !\n***********\n"
                    + legname
                    + " - Run #"
                    + str(r + 1)
                    + " - SC #"
                    + str(c + 1)
                    + " has an earlier start than previous SC's end latency - Skipping!"
                )
                print(this_message)
                write_issues_to_textfile(this_message, info)
    return clean_cycles


def check_stepcycles(all_cycles, info):
    """Check results of SC extraction. Cancel everything if None found!"""
    name = info["name"]
    # case 1 - valid SCs for both legs
    if (type(all_cycles["left"]) == list) & (type(all_cycles["right"]) == list):
        return all_cycles
    # case 2 - no valid SCs for left leg
    elif (all_cycles["left"] == None) & (type(all_cycles["right"]) == list):
        this_message = (
            "\n***********\n! ERROR !\n***********\n"
            + "\nID: "
            + name
            + "\nNo valid SCs found for LEFT leg!"
        )
        write_issues_to_textfile(this_message, info)
        print(this_message)
        return all_cycles
    # case 3 - no valid SCs for right leg
    elif (type(all_cycles["left"]) == list) & (all_cycles["right"] == None):
        this_message = (
            "\n***********\n! ERROR !\n***********\n"
            + "\nID: "
            + name
            + "\nNo valid SCs found for RIGHT leg!"
        )
        write_issues_to_textfile(this_message, info)
        print(this_message)
        return all_cycles
    # case 4 - no valid SCs for either leg
    elif (all_cycles["left"] == None) & (all_cycles["right"] == None):
        this_message = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "\nID: "
            + name
            + "\nSkipped because no valid SCs found for any leg!"
        )
        print(this_message)
        write_issues_to_textfile(this_message, info)
        return  # in this case, abort everything (returns None to main)


# %% local functions 3 - y-flipping, features, df-creation & exports
# Note
# ----
# There is quite a lot going on in this function. We:
# 1) loop through all step cycles for one leg at a time and extract individual SCs' data
# 2) for each step's data we normalise all Z (height) values to the mindfoots minimum
#    if wanted
# 3) we then we flip y columns if needed (to simulate equal walking direction)
# 4) immediately after 3 & 4 and for each step's data separately, we compute and add
#    features (angles, velocities, accelerations)
#    ==> see norm_z_flip_y_and_add_features_to_one_step & helper functions a
# 5) immediately after adding features, we normalise a step to bin_num
#    ==> see normalise_one_steps_data & helper functions b
# 6) we add original and normalised steps to all_steps_data and normalised_steps_data
# 7) once we are done with this for a given leg we create average and std dataframes
# 8) we combine legs and store those dfs in a third idx of our dataframe lists
#    ==> see helper functions c for #6 & #7
# 9) we finally output all df-lists in a results dict and export each df-list
#    (of left, right and both legs) in excel files with 3 sheets each
#   ==> see helper functions d


# ...............................  main function  ......................................
def analyse_and_export_stepcycles(data, all_cycles, global_Y_max, info, cfg):
    """Export original-length and normalised XLS files of extracted steps"""
    # ..............................  preparation  .....................................
    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    bin_num = cfg["bin_num"]
    analyse_average_y = cfg["analyse_average_y"]
    # do everything on a copy of the data df
    data_copy = data.copy()
    # for exports, we don't need all_cycles to be separated for runs
    # ==> transform to a list of all SCs for each leg
    all_cycles = flatten_all_cycles(all_cycles)
    # check if there are excel files from a previous run, if so - delete
    delete_previous_xlsfiles(name, results_dir)
    # initialise list of dfs & results
    all_steps_data = [pd.DataFrame(data=None)] * len(OUTPUTS)
    normalised_steps_data = [pd.DataFrame(data=None)] * len(OUTPUTS)
    average_data = [pd.DataFrame(data=None)] * len(OUTPUTS)
    std_data = [pd.DataFrame(data=None)] * len(OUTPUTS)
    sc_num = [None for i in range(len(OUTPUTS))]
    results = {"left": {}, "right": {}, "both": {}}
    # .................  loop over legs and populate dfs  ..............................
    # for each step:
    # 1) extract it from data_copy (this_step)
    # 2) normalise Z if wanted, flip y columns if needed and add features
    # 3) normalise its length to bin_num (this_normalised_step)
    # 4) add this_step to all_steps_data and this_normalised_step to
    #    normalised_steps_data
    for l_idx, legname in enumerate(LEGS):
        # 1 step only (highly unlikely in humans)
        if len(all_cycles[legname]) == 1:
            this_step = data_copy.loc[
                all_cycles[legname][0][0] : all_cycles[legname][0][1]
            ]
            this_step = norm_z_flip_y_and_add_features_to_one_step(
                this_step, l_idx, global_Y_max, cfg
            )
            all_steps_data[l_idx] = this_step
            normalised_steps_data[l_idx] = normalise_one_steps_data(this_step, bin_num)
            sc_num[l_idx] = 1
        # 2 or more steps - build dataframes
        elif len(all_cycles[legname]) > 1:
            # first step is added manually
            first_step = data_copy.loc[
                all_cycles[legname][0][0] : all_cycles[legname][0][1]
            ]
            first_step = norm_z_flip_y_and_add_features_to_one_step(
                first_step, l_idx, global_Y_max, cfg
            )
            all_steps_data[l_idx] = first_step
            normalised_steps_data[l_idx] = normalise_one_steps_data(first_step, bin_num)
            # some prep for addition of further steps
            sc_num[l_idx] = len(all_cycles[legname])
            nanvector = data_copy.loc[[SEPARATOR_IDX]]
            nanvector[:] = np.nan
            # .............................  step-loop  ................................
            for s in range(1, sc_num[l_idx], 1):
                # get step separators
                numvector = data_copy.loc[[SEPARATOR_IDX]]
                numvector[:] = s + 1
                all_steps_data[l_idx] = add_step_separators(
                    all_steps_data[l_idx], nanvector, numvector
                )
                # this_step
                this_step = data_copy.loc[
                    all_cycles[legname][s][0] : all_cycles[legname][s][1]
                ]
                this_step = norm_z_flip_y_and_add_features_to_one_step(
                    this_step, l_idx, global_Y_max, cfg
                )
                all_steps_data[l_idx] = pd.concat(
                    [all_steps_data[l_idx], this_step], axis=0
                )
                # this_normalised_step
                this_normalised_step = normalise_one_steps_data(this_step, bin_num)
                normalised_steps_data[l_idx] = add_step_separators(
                    normalised_steps_data[l_idx], nanvector, numvector
                )
                normalised_steps_data[l_idx] = pd.concat(
                    [normalised_steps_data[l_idx], this_normalised_step], axis=0
                )
        # .............................  after step-loop  ..............................
        # 1) add a column to both dfs informing about leg (important for combining legs)
        all_steps_data[l_idx] = pd.concat(
            [
                all_steps_data[l_idx],  # all_steps_data
                pd.DataFrame(
                    data=legname,
                    index=all_steps_data[l_idx].index,
                    columns=[DF_LEG_COL],
                ),
            ],
            axis=1,
        )
        normalised_steps_data[l_idx] = pd.concat(
            [
                normalised_steps_data[l_idx],  # normalised_steps_data
                pd.DataFrame(
                    data=legname,
                    index=normalised_steps_data[l_idx].index,
                    columns=[DF_LEG_COL],
                ),
            ],
            axis=1,
        )
        # 2) create and save average_ and std_data
        average_data[l_idx], std_data[l_idx] = compute_average_and_std_data(
            normalised_steps_data[l_idx], bin_num, analyse_average_y
        )
    # ................................  after leg-loop  ................................
    # 1a) create "both" sheets for all our data-formats (added to -1 idx of df_list)
    # => note that we only need only_one_valid_leg once so the first 3 functions are
    #    called with [0] to index the output-tuple and get only the df from the function
    all_steps_data = combine_legs(all_steps_data, "concatenate")[0]
    normalised_steps_data = combine_legs(normalised_steps_data, "concatenate")[0]
    average_data = combine_legs(average_data, "average")[0]
    std_data, only_one_valid_leg = combine_legs(std_data, "average")
    # 1b) inform user if only one leg had valid SCs (affects 3rd sheet!)
    if only_one_valid_leg:
        this_message = (
            "\n***********\n! WARNING !\n***********\n"
            + "Only the "
            + only_one_valid_leg
            + " leg had valid step cycles after our sanity checks. "
            + "\nThe third sheet of generated Sheet (XLS) files therefore only "
            + "reflects this leg's data!"
        )
        print(this_message)
        write_issues_to_textfile(this_message, info)
    # 2) loop to assign to results and save to xls-file sheets
    for idx, output in enumerate(OUTPUTS):
        results[output]["all_steps_data"] = all_steps_data[idx]
        results[output]["normalised_steps_data"] = normalised_steps_data[idx]
        results[output]["average_data"] = average_data[idx]
        results[output]["std_data"] = std_data[idx]
        if idx == len(OUTPUTS) - 1:
            if not only_one_valid_leg:
                results[output]["sc_num"] = sc_num[0] + sc_num[1]
            else:
                if only_one_valid_leg == "left":
                    results[output]["sc_num"] = sc_num[0]
                elif only_one_valid_leg == "right":
                    results[output]["sc_num"] = sc_num[1]
        else:
            results[output]["sc_num"] = sc_num[idx]
        save_results_sheet(
            all_steps_data[idx],
            output,
            os.path.join(results_dir, name + ORIGINAL_XLS_FILENAME),
            only_one_valid_leg,
        )
        save_results_sheet(
            normalised_steps_data[idx],
            output,
            os.path.join(results_dir, name + NORMALISED_XLS_FILENAME),
            only_one_valid_leg,
        )
        save_results_sheet(
            average_data[idx],
            output,
            os.path.join(results_dir, name + AVERAGE_XLS_FILENAME),
            only_one_valid_leg,
        )
        save_results_sheet(
            std_data[idx],
            output,
            os.path.join(results_dir, name + STD_XLS_FILENAME),
            only_one_valid_leg,
        )
    return results


# ......................................................................................
# ...........  helper functions a - norm z, flip y and add features  ...................
# ......................................................................................


def norm_z_flip_y_and_add_features_to_one_step(step, l_idx, global_Y_max, cfg):
    """For a single step cycle's data, normalise z if wanted, flip y columns if needed
    (to simulate equal run direction) and add features (angles & velocities)
    """
    # unpack
    direction_joint = cfg["direction_joint"]
    # if user wanted this, normalise z (height) at step-cycle level
    step_copy = step.copy()
    if cfg["normalise_height_at_SC_level"] is True:
        # Finally, standardise all Z columns to global Z minimum being zero
        z_cols = [col for col in step_copy.columns if col.endswith("Z")]
        z_minimum = min(step_copy[z_cols].min())
        step_copy[z_cols] -= z_minimum
    # find out if we need to flip y columns of this step and flip them if we do
    direction_joint_col_idx = step_copy.columns.get_loc(direction_joint)
    direction_joint_mean = np.mean(step_copy[direction_joint])
    if step_copy.iloc[0, direction_joint_col_idx] > direction_joint_mean:
        step_copy = flip_y_columns(step_copy, global_Y_max)
    # add angles and velocities
    step_copy = add_features(step_copy, cfg)
    return step_copy


def flip_y_columns(step, global_Y_max):
    """Flip all y columns if walking direction was right to left
    (i.e., Y was decreasing within a step cycle)
    """
    flipped_step = step.copy()  # do everything on a copy of step
    y_cols = [col for col in step.columns if col.endswith("Y")]
    flipped_step[y_cols] = global_Y_max - flipped_step[y_cols]
    return flipped_step


def add_features(step, cfg):
    """Add Features, i.e. Angles & Velocities

    Note
    ----
    Since adding flexibility with user-defined feature-names (i.e., joints & angles)
    we had to consider the case of a non-bodyside-specific angle to be computed (e.g.,
    Pelvis) using bodyside-specific joints (e.g., Hip).
    => Thus the angle + Y if statements in the local functions
    => Since we loop over left, right body sides and due to how we use the
       step_copy.columns.duplicated() statement below, this means that such angles
       (and corresponding velocities & accelerations) will be computed with reference
       to the left body side by default
       -- Add this to the documentation and tell people to fix their simi-columns if
          they want to have this differently... maybe improve in the future if wanted
       -- This leads to a slight inaccuracy/limitation in that e.g. the Pelvis Angle is
          computed w.r.t. the left side of the body always, even in the XLS sheets of
          step cycles of the right leg

    DONT GET CONFUSED ABOUT STEP'S KEY NAMES WHEN YOU LOOK AT THIS IN A YEAR
    ------------------------------------------------------------------------
    The "Y", "Z", "Angle", "Velocity" strings never start with a space, e.g.
    " Velocity" because we previously ensured that joints that are not bodyside-
    specific end with a space (and thus joint + "Velocity" is correct) and if they
    are bodyside specific legname is of LEGS_COLFORMAT, so that also ends with a
    space character
    """
    # unpack
    angles = cfg["angles"]

    step_copy = step.copy()
    for legname in LEGS_COLFORMAT:
        if angles["name"]:  # if at least 1 string in list
            step_copy = add_angles(step_copy, legname, cfg)
        step_copy = add_velocities(step_copy, legname, cfg)
    # I do this since it's possible that we created two, e.g., "Pelvis Angle" cols due
    # to our leg-loop # !!! NU (see in the doc above)
    step_copy = step_copy.loc[:, ~step_copy.columns.duplicated()]
    return step_copy


def add_angles(step, legname, cfg):
    """Feature #1: Joint Angles

    Note
    ----
    legname here is from LEGS_COLFORMAT!
    """

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
        # ==> for each of our 3 joints, check if they are body-side-specific or not
        # angle (name)
        if angle + "Y" in step.columns:
            joint_angle[:, 0] = step[angle + "Y"]
            joint_angle[:, 1] = step[angle + "Z"]
        else:
            joint_angle[:, 0] = step[angle + legname + "Y"]
            joint_angle[:, 1] = step[angle + legname + "Z"]
        # lower joint
        if lower_joint + "Y" in step.columns:
            joint2[:, 0] = step[lower_joint + "Y"]
            joint2[:, 1] = step[lower_joint + "Z"]
        else:
            joint2[:, 0] = step[lower_joint + legname + "Y"]
            joint2[:, 1] = step[lower_joint + legname + "Z"]
        # upper joint
        if upper_joint + "Y" in step.columns:
            joint3[:, 0] = step[upper_joint + "Y"]
            joint3[:, 1] = step[upper_joint + "Z"]
        else:
            joint3[:, 0] = step[upper_joint + legname + "Y"]
            joint3[:, 1] = step[upper_joint + legname + "Z"]
        # initialise the angle vector and assign looping over timepoints
        this_angle = np.zeros(len(joint_angle))
        for t in range(len(joint_angle)):
            this_angle[t] = compute_angle(joint_angle[t, :], joint2[t, :], joint3[t, :])
        # colnames depend on bodyside-specificity
        if angle + "Y" in step.columns:
            this_colname = angle + "Angle"
        elif angle + legname + "Y" in step.columns:
            this_colname = angle + legname + "Angle"
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
    # try:
    angle = math.acos(dot_product / (mag_v1 * mag_v2))
    # except RuntimeWarning:
    #     print("RuntimeWarning caught. Investigating...")
    return math.degrees(angle)


def add_velocities(step, legname, cfg):
    """Feature #2: Joint Y and Angular Velocities"""

    # unpack
    joints = cfg["joints"]
    angles = cfg["angles"]
    y_acceleration = cfg["y_acceleration"]
    angular_acceleration = cfg["angular_acceleration"]
    original_legname = legname  # in case we overwrite legname to be an empty string

    # compute velocities (& acceleration if wanted) for joints
    for joint in joints:
        if joint + "Y" in step.columns:
            legname = ""
        else:
            legname = original_legname
        step[joint + legname + "Velocity"] = 0.0
        step.loc[:, joint + legname + "Velocity"] = np.gradient(
            step.loc[:, joint + legname + "Y"]
        )
        if y_acceleration:
            step[joint + legname + "Acceleration"] = 0.0
            step.loc[:, joint + legname + "Acceleration"] = np.gradient(
                step.loc[:, joint + legname + "Velocity"]
            )
    # compute velocities (& acceleration) for the angles too
    for angle in angles["name"]:
        if angle + "Angle" in step.columns:
            legname = ""
        else:
            legname = original_legname
        angle_colname = angle + legname + "Angle"
        step[angle_colname + " Velocity"] = 0.0  # spaces in colnames here!
        step.loc[:, angle_colname + " Velocity"] = np.gradient(
            step.loc[:, angle_colname]
        )
        if angular_acceleration:
            step[angle_colname + " Acceleration"] = 0.0
            step.loc[:, angle_colname + " Acceleration"] = np.gradient(
                step.loc[:, angle_colname + " Velocity"]
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

    normalised_step = pd.DataFrame(
        data=None, index=range(bin_num), columns=step.columns
    )
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


def compute_average_and_std_data(normalised_steps_data, bin_num, analyse_average_y):
    """Export XLS tables that store all averages & std of y-coords & angles"""
    # initialise data & columns of average & std dataframes (fill vals in loop)
    initialisation_data = [[int(((s + 1) / bin_num) * 100) for s in range(bin_num)]]
    initialisation_columns = [DF_SCPERCENTAGE_COL]
    if analyse_average_y:
        cols_to_include = [
            c
            for c in normalised_steps_data.columns
            if c not in EXCLUDED_COLS_IN_AV_STD_DFS
        ]
    else:
        cols_to_include = [
            c
            for c in normalised_steps_data.columns
            if (c not in EXCLUDED_COLS_IN_AV_STD_DFS) and (not c.endswith(" Y"))
        ]
    for col in cols_to_include:
        initialisation_data.append([None] * bin_num)
        initialisation_columns.append(col)
    initialisation_data = np.asarray(initialisation_data).transpose()  # match df-shape
    # initialise dataframes
    average_data = pd.DataFrame(
        data=initialisation_data, index=range(bin_num), columns=initialisation_columns
    )
    std_data = pd.DataFrame(
        data=initialisation_data, index=range(bin_num), columns=initialisation_columns
    )
    # loop over step cycles & columns and fill df values as you go
    # => important to note that c corresponds to colidxs of original df
    #    (not of av/std dfs) - we use col strings to assign values to correct cols of
    #    our new dfs
    sc_num = len(np.where(normalised_steps_data.index == 0)[0])
    for c, col in enumerate(
        normalised_steps_data.columns
    ):  # caution! c => normalised_steps_data!!
        if col in cols_to_include:
            this_data = np.zeros([bin_num, sc_num])
            for s in range(sc_num):
                # with this_end it's bin_num & not bin_num -1 because iloc
                # does not include last index
                this_start = np.where(normalised_steps_data.index == 0)[0][s]
                this_end = np.where(normalised_steps_data.index == 0)[0][s] + bin_num
                this_data[:, s] = normalised_steps_data.iloc[this_start:this_end, c]
            average_data[col] = np.mean(this_data, axis=1)
            std_data[col] = np.std(this_data, axis=1)
    return average_data, std_data


def combine_legs(dataframe_list, combination_procedure):
    """Combine the results of left and right legs as a new df to export as Sheet 3"""
    # first check if we only have one valid leg
    # => if av/std dfs are empty they only have SC_COL
    only_one_valid_leg = False
    if combination_procedure == "concatenate":
        # list[0] is left, so right is valid & vice versa
        if dataframe_list[0].empty:
            only_one_valid_leg = "right"
        if dataframe_list[1].empty:
            only_one_valid_leg = "left"
    elif combination_procedure == "average":
        if (
            len(dataframe_list[0].columns) == 1
            and dataframe_list[0].columns[0] == DF_SCPERCENTAGE_COL
        ):
            only_one_valid_leg = "right"
        if (
            len(dataframe_list[1].columns) == 1
            and dataframe_list[1].columns[0] == DF_SCPERCENTAGE_COL
        ):
            only_one_valid_leg = "left"
    if combination_procedure == "concatenate":
        # copy dfs if only one leg, otherwise concatenate
        if only_one_valid_leg == "left":
            dataframe_list[-1] = dataframe_list[0].copy()
        elif only_one_valid_leg == "right":
            dataframe_list[-1] = dataframe_list[1].copy()
        else:
            infovector = dataframe_list[0].iloc[0, :]
            infovector = pd.DataFrame(infovector).T
            infovector.index = [SEPARATOR_IDX]
            infovector[:] = "leg-change"
            nanvector = dataframe_list[0].iloc[0, :]
            nanvector = pd.DataFrame(nanvector).T
            nanvector.index = [SEPARATOR_IDX]
            nanvector[:] = np.nan
            # concatenation (similar separators as between stepcycles)
            # ignoring warnings here temporarily
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dataframe_list[-1] = pd.concat(
                    [dataframe_list[0], nanvector], axis=0
                )  # list0!
            dataframe_list[-1] = pd.concat(
                [dataframe_list[-1], infovector], axis=0
            )  # -1 !
            dataframe_list[-1] = pd.concat([dataframe_list[-1], nanvector], axis=0)
            dataframe_list[-1] = pd.concat(
                [dataframe_list[-1], dataframe_list[1]], axis=0
            )
            # reorder columns
            for i in range(len(dataframe_list)):
                cols = REORDER_COLS_IN_STEP_NORMDATA
                dataframe_list[i] = dataframe_list[i][
                    cols + [c for c in dataframe_list[i].columns if c not in cols]
                ]
    elif combination_procedure == "average":
        # we can assign as we do here since dataframe_lists' dfs are average or std dfs
        # => note that we purposely check against SC col above for these to make sure
        if only_one_valid_leg == "left":
            dataframe_list[-1] = dataframe_list[0].copy()
        elif only_one_valid_leg == "right":
            dataframe_list[-1] = dataframe_list[1].copy()
        else:
            # initialise both df with same idx and cols as left df
            dataframe_list[-1] = pd.DataFrame(
                data=None,
                index=dataframe_list[0].index,
                columns=dataframe_list[0].columns,
            )
            for col in dataframe_list[0].columns:
                this_data = np.zeros([len(dataframe_list[0].index), 2])
                this_data[:, 0] = np.asarray(dataframe_list[0][col])
                this_data[:, 1] = np.asarray(dataframe_list[1][col])
                dataframe_list[-1][col] = np.mean(this_data, axis=1)
    return dataframe_list, only_one_valid_leg


# ......................................................................................
# ....................  helper functions d - miscellaneous  ............................
# ......................................................................................


def flatten_all_cycles(all_cycles):
    """Extract all runs' SC latencies and create a list of len=SC_num for each leg"""
    flattened_cycles = {"left": [], "right": []}
    for legname in LEGS:
        if all_cycles[legname]:  # can be None
            for run_cycles in all_cycles[legname]:
                for cycle in run_cycles:
                    flattened_cycles[legname].append(cycle)
    return flattened_cycles


def delete_previous_xlsfiles(name, results_dir):
    """
    Check and delete previously stored excel files (important since appending sheets)
    """
    all_filenames = [
        ORIGINAL_XLS_FILENAME,
        NORMALISED_XLS_FILENAME,
        AVERAGE_XLS_FILENAME,
        STD_XLS_FILENAME,
    ]
    for filename in all_filenames:
        fullfilepath = results_dir + name + filename + ".xlsx"
        if os.path.exists(fullfilepath):
            os.remove(fullfilepath)


def save_results_sheet(dataframe, sheet, fullfilepath, only_one_valid_leg):
    """Save a xls sheet of given df"""
    fullfilepath = fullfilepath + ".xlsx"
    # pdb.set_trace()
    if os.path.exists(fullfilepath):
        with pd.ExcelWriter(fullfilepath, mode="a") as writer:
            if (only_one_valid_leg == "left" and sheet == "right") or (
                only_one_valid_leg == "right" and sheet == "left"
            ):
                pd.DataFrame(data=None).to_excel(writer, sheet_name=sheet, index=False)
            else:
                dataframe.to_excel(writer, sheet_name=sheet, index=False)
    else:
        with pd.ExcelWriter(fullfilepath) as writer:
            if (only_one_valid_leg == "left" and sheet == "right") or (
                only_one_valid_leg == "right" and sheet == "left"
            ):
                pd.DataFrame(data=None).to_excel(writer, sheet_name=sheet, index=False)
            else:
                dataframe.to_excel(writer, sheet_name=sheet, index=False)


def add_step_separators(dataframe, nanvector, numvector):
    """Add nan & num vector separators between step cycles to dataframes"""
    dataframe = pd.concat([dataframe, nanvector], axis=0)  # nan
    dataframe = pd.concat([dataframe, numvector], axis=0)  # num
    dataframe = pd.concat([dataframe, nanvector], axis=0)  # nan
    return dataframe


# %% local functions 4 - various plots

# A Note
# ------
# I initially decided to use extract_sc_idxs instead of all_cycles when I first wrote
# this for mice data to be independent from the previous pipeline - just so plotting
# stuff could at some point be ran just by loading the XLS files that
# analyse_and_export_stepcycles outputs However, I am now using all_cycles instead of
# sc_idxs because for humans we have multiple runs per subject and I need to understand
# which SC latencies correspond to which run.
# This might change in the future but for now let's do it this way.
# => Idea: you could just save all_cycles to a file and then load that as well as XLS
#          to plot independently from previous things.

# Another 2 (more recent) Notes
# --------------------------
# In all functions below I added checks to see if joints/angles were bodyside-specific
# e.g., "Ankle, left Z" or "Pelvis Z"
# => We still loop over legname in plot_results as before since even though the column
#    might not be bodyside-specific, the data dfs (e.g. all_steps_data) contain
#    different values based on the leg that performed the step-cycles
#
# Only use extract_feature_column when you index using .iloc afterwards (don't be
# surprised that we don't use this local func everywhere, since the first couple of
# plotting functions extract values using .loc!)


# ................................  master function  ...................................
def plot_results(results, all_cycles, info, cfg, plot_panel_instance):
    """Plot various results"""

    # unpack
    angles = cfg["angles"]
    y_acceleration = cfg["y_acceleration"]
    angular_acceleration = cfg["angular_acceleration"]
    analyse_average_y = cfg["analyse_average_y"]
    dont_show_plots = cfg["dont_show_plots"]
    if dont_show_plots:
        plt.switch_backend("Agg")

    # unpack - output specific vars (results to be plotted)
    for legname in LEGS:  # !!! NU - output...
        all_steps_data = results[legname]["all_steps_data"]
        average_data = results[legname]["average_data"]
        std_data = results[legname]["std_data"]
        sc_num = results[legname]["sc_num"]

        if all_cycles[legname]:

            # ....................  1 - z coords by y coords  ..........................
            plot_joint_z_by_y(
                legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
            )

            # ........................  2 - y coords by time  ..........................
            if analyse_average_y:
                plot_joint_y_by_time(
                    legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
                )

            # ..................  3 - angle by time for each SC  .......................
            if angles["name"]:
                plot_angles_by_time(
                    legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
                )
            # regularly closing figures to save memory
            # => no problem to do this since we pass figure-vars to save-functions and Panel
            plt.close("all")

            # ............................  4 - stick diagram  .........................
            plot_stickdiagram(
                legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
            )

            # .................  5 - average 5-joints' z over SC percentage  ...........
            plot_joint_z_by_average_SC(
                legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
            )

            # .................  6 - average 5-joints' y over SC percentage  ...........
            if analyse_average_y:
                plot_joint_y_by_average_SC(
                    legname,
                    average_data,
                    std_data,
                    sc_num,
                    info,
                    cfg,
                    plot_panel_instance,
                )

            # ...................  7 - average angles over SC percentage  ..............
            if angles["name"]:
                plot_angles_by_average_SC(
                    legname,
                    average_data,
                    std_data,
                    sc_num,
                    info,
                    cfg,
                    plot_panel_instance,
                )
            plt.close("all")

            # .............  8 - average y velocities over SC percentage   .............
            plot_y_velocities_by_average_SC(
                legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
            )

            # ..........  9 - average angular velocities over SC percentage  ...........
            if angles["name"]:
                plot_angular_velocities_by_average_SC(
                    legname,
                    average_data,
                    std_data,
                    sc_num,
                    info,
                    cfg,
                    plot_panel_instance,
                )

            # .......  optional - 10 - average x acceleration over SC percentage  ......
            if y_acceleration:
                plot_y_acceleration_by_average_SC(
                    legname,
                    average_data,
                    std_data,
                    sc_num,
                    info,
                    cfg,
                    plot_panel_instance,
                )

            # ....  optional - 11 - average angular acceleration over SC percentage  ...
            if angles["name"]:
                if angular_acceleration:
                    plot_angular_acceleration_by_average_SC(
                        legname,
                        average_data,
                        std_data,
                        sc_num,
                        info,
                        cfg,
                        plot_panel_instance,
                    )
            plt.close("all")
        else:
            no_plots_message = (
                "\n***********\n! WARNING !\n***********\n"
                + "No step cycles found for "
                + legname
                + " leg!"
                + "\nWe thus skip all figures for this leg!\n"
            )
            print(no_plots_message)
            write_issues_to_textfile(no_plots_message, info)

    # ........................optional - 12 - build plot panel..........................
    if dont_show_plots is True:
        pass  # going on without building the plot window
    elif dont_show_plots is False:  # -> show plot panel
        # Destroy loading screen and build plot panel with all figures
        plot_panel_instance.destroy_plot_panel_loading_screen()
        plot_panel_instance.build_plot_panel()


# ................................  inner functions  ...................................


def plot_joint_z_by_y(
    legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
):
    """1 - Plot joints' z coordinates as a function of their y for each SC"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    sampling_rate = cfg["sampling_rate"]
    dont_show_plots = cfg["dont_show_plots"]
    plot_joints = cfg["plot_joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    max_cycle_num = 0
    for cycles in all_cycles[legname]:
        if len(cycles) > max_cycle_num:
            max_cycle_num = len(cycles)
    f = [[] for _ in range(len(plot_joints))]
    ax = [[] for _ in range(len(plot_joints))]

    # plot
    for j, joint in enumerate(plot_joints):  # joint loop (figures)
        f[j], ax[j] = plt.subplots(
            len(all_cycles[legname]),
            1,
            sharex=True,
            sharey=True,
            gridspec_kw={"hspace": 0},
        )
        for r, run_cycles in enumerate(all_cycles[legname]):  # run loop (axis)
            sc_num = len(run_cycles)
            try:  # handle only 1 run in "stuff by y" plots
                ax[j][r].set_prop_cycle(
                    plt.cycler("color", sns.color_palette(color_palette, max_cycle_num))
                )
            except:
                ax[j].set_prop_cycle(
                    plt.cycler("color", sns.color_palette(color_palette, max_cycle_num))
                )
            # check for bodyside-specificity
            if joint + "Y" in all_steps_data.columns:
                y_col_string = joint + "Y"
                z_col_string = joint + "Z"
            else:
                y_col_string = transform_joint_and_leg_to_colname(joint, legname, "Y")
                z_col_string = transform_joint_and_leg_to_colname(joint, legname, "Z")
            for s in range(sc_num):
                this_sc_idx = run_cycles[s]
                this_y = all_steps_data.loc[
                    this_sc_idx[0] : this_sc_idx[1], y_col_string
                ]
                this_z = all_steps_data.loc[
                    this_sc_idx[0] : this_sc_idx[1], z_col_string
                ]
                this_label = generate_sc_latency_label(this_sc_idx, sampling_rate)
                try:
                    ax[j][r].plot(this_y, this_z, label=this_label)
                except:
                    ax[j].plot(this_y, this_z, label=this_label)
            # axis stuff
            try:
                if legend_outside is True:
                    ax[j][r].legend(
                        fontsize=SC_LAT_LEGEND_FONTSIZE,
                        loc="center left",
                        bbox_to_anchor=(1, 0.5),
                    )
                elif legend_outside is False:
                    ax[j][r].legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
                median_z_val = [round(np.median(ax[j][r].get_yticks()), 2)]
                median_z_val_label = [str(median_z_val[0])]  # has to be of same len
                ax[j][r].set_yticks(median_z_val, median_z_val_label)
            except:
                if legend_outside is True:
                    ax[j].legend(
                        fontsize=SC_LAT_LEGEND_FONTSIZE + 3,
                        loc="center left",
                        bbox_to_anchor=(1, 0.5),
                    )
                elif legend_outside is False:
                    ax[j].legend(fontsize=SC_LAT_LEGEND_FONTSIZE + 3)
                median_z_val = [round(np.median(ax[j].get_yticks()), 2)]
                median_z_val_label = [str(median_z_val[0])]  # has to be of same len
                ax[j].set_yticks(median_z_val, median_z_val_label)
            # title
            figure_file_string = (
                name + " - " + legname + " - " + joint + " z by y coordinates"
            )
            try:
                ax[j][0].set_title(figure_file_string)
            except:
                ax[j].set_title(figure_file_string)
        # figure stuff
        f[j].supxlabel("y (m)")
        f[j].supylabel("z (m)")
        save_figures(f[j], results_dir, figure_file_string)
        if dont_show_plots:
            plt.close(f[j])

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f[j])


def plot_joint_y_by_time(
    legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
):
    """2 - Plot joints' y coordinates as a function of time for each SC"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    sampling_rate = cfg["sampling_rate"]
    dont_show_plots = cfg["dont_show_plots"]
    plot_joints = cfg["plot_joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    max_cycle_num = 0
    for cycles in all_cycles[legname]:
        if len(cycles) > max_cycle_num:
            max_cycle_num = len(cycles)
    f = [[] for _ in range(len(plot_joints))]
    ax = [[] for _ in range(len(plot_joints))]

    # plot
    for j, joint in enumerate(plot_joints):  # joint loop (figures)
        f[j], ax[j] = plt.subplots(
            len(all_cycles[legname]),
            1,
            sharex=True,
            sharey=True,
            gridspec_kw={"hspace": 0},
        )
        for r, run_cycles in enumerate(all_cycles[legname]):  # run loop (axis)
            sc_num = len(run_cycles)
            try:  # handle only 1 run in "stuff by y" plots
                ax[j][r].set_prop_cycle(
                    plt.cycler("color", sns.color_palette(color_palette, max_cycle_num))
                )
            except:
                ax[j].set_prop_cycle(
                    plt.cycler("color", sns.color_palette(color_palette, max_cycle_num))
                )
            # check for bodyside-specificity
            if joint + "X" in all_steps_data.columns:
                y_col_string = joint + "Y"
            else:
                y_col_string = transform_joint_and_leg_to_colname(joint, legname, "Y")
            for s in range(sc_num):
                this_sc_idx = run_cycles[s]
                this_time = all_steps_data.loc[
                    this_sc_idx[0] : this_sc_idx[1], DF_TIME_COL
                ]
                this_y = all_steps_data.loc[
                    this_sc_idx[0] : this_sc_idx[1], y_col_string
                ]
                this_label = generate_sc_latency_label(this_sc_idx, sampling_rate)
                try:
                    ax[j][r].plot(this_time, this_y, label=this_label)
                except:
                    ax[j].plot(this_time, this_y, label=this_label)
            # axis stuff
            try:
                if legend_outside is True:
                    ax[j][r].legend(
                        fontsize=SC_LAT_LEGEND_FONTSIZE,
                        loc="center left",
                        bbox_to_anchor=(1, 0.5),
                    )
                elif legend_outside is False:
                    ax[j][r].legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
                median_y_val = [round(np.median(ax[j][r].get_yticks()), 2)]
                median_y_val_label = [str(median_y_val[0])]  # has to be of same len
                ax[j][r].set_yticks(median_y_val, median_y_val_label)
            except:
                if legend_outside is True:
                    ax[j].legend(
                        fontsize=SC_LAT_LEGEND_FONTSIZE + 3,
                        loc="center left",
                        bbox_to_anchor=(1, 0.5),
                    )
                elif legend_outside is False:
                    ax[j].legend(fontsize=SC_LAT_LEGEND_FONTSIZE + 3)
                median_y_val = [round(np.median(ax[j].get_yticks()), 2)]
                median_y_val_label = [str(median_y_val[0])]  # has to be of same len
                ax[j].set_yticks(median_y_val, median_y_val_label)
            # title
            figure_file_string = (
                name + " - " + legname + " - " + joint + " y coordinate by time "
            )
            try:
                ax[j][0].set_title(figure_file_string)
            except:
                ax[j].set_title(figure_file_string)
        # figure stuff
        f[j].supxlabel("Time (s)")
        f[j].supylabel("y (m)")
        save_figures(f[j], results_dir, figure_file_string)
        if dont_show_plots:
            plt.close(f[j])

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f[j])


def plot_angles_by_time(
    legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
):
    """3 - Plot joints' angles as a function of time for each SC"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    sampling_rate = cfg["sampling_rate"]
    dont_show_plots = cfg["dont_show_plots"]
    angles = cfg["angles"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    max_cycle_num = 0
    for cycles in all_cycles[legname]:
        if len(cycles) > max_cycle_num:
            max_cycle_num = len(cycles)
    f = [[] for _ in range(len(angles["name"]))]
    ax = [[] for _ in range(len(angles["name"]))]

    # plot
    for a, angle in enumerate(angles["name"]):  # angle loop (figures)
        f[a], ax[a] = plt.subplots(1, 1)
        for run_cycles in all_cycles[legname]:  # run loop (color-cycler-reset)
            sc_num = len(run_cycles)
            ax[a].set_prop_cycle(
                plt.cycler("color", sns.color_palette(color_palette, max_cycle_num))
            )
            # check for bodyside-specificity
            if angle + "Angle" in all_steps_data.columns:
                angle_col_string = angle + "Angle"
            else:
                angle_col_string = transform_joint_and_leg_to_colname(
                    angle, legname, "Angle"
                )
            for s in range(sc_num):
                this_sc_idx = run_cycles[s]
                this_time = all_steps_data.loc[
                    this_sc_idx[0] : this_sc_idx[1], DF_TIME_COL
                ]
                this_angle = all_steps_data.loc[
                    this_sc_idx[0] : this_sc_idx[1], angle_col_string
                ]
                this_label = generate_sc_latency_label(this_sc_idx, sampling_rate)
                ax[a].plot(this_time, this_angle, label=this_label)
            # legend
            if legend_outside is True:
                ax[a].legend(
                    fontsize=SC_LAT_LEGEND_FONTSIZE,
                    loc="center left",
                    bbox_to_anchor=(1, 0.5),
                )
            elif legend_outside is False:
                ax[a].legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
            # title
            figure_file_string = (
                name + " - " + legname + " - " + angle + " angle by time"
            )
            ax[a].set_title(figure_file_string)
        # figure stuff
        f[a].supxlabel("Time (s)")
        f[a].supylabel("Angle (degree)")
        save_figures(f[a], results_dir, figure_file_string)
        if dont_show_plots:
            plt.close(f[a])

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f[a])


def plot_stickdiagram(
    legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
):
    """4 - Plot a stick diagram"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    sampling_rate = cfg["sampling_rate"]
    dont_show_plots = cfg["dont_show_plots"]
    plot_joints = cfg["plot_joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    max_cycle_num = 0
    for cycles in all_cycles[legname]:
        if len(cycles) > max_cycle_num:
            max_cycle_num = len(cycles)
    f, ax = plt.subplots(
        len(all_cycles[legname]),
        1,
        sharex=True,
        sharey=True,
        gridspec_kw={"hspace": 0},
    )
    color_cycle = plt.cycler("color", sns.color_palette(color_palette, max_cycle_num))

    # plot
    for r, run_cycles in enumerate(all_cycles[legname]):  # run loop (axis)
        this_sc_num = len(run_cycles)
        try:  # handle 1 run with valid SCs
            ax[r].set_prop_cycle(color_cycle)
        except:
            ax.set_prop_cycle(color_cycle)
        for c, this_color_dict in zip(range(this_sc_num), color_cycle):  # SC loop
            this_sc_idx = run_cycles[c]
            this_color = this_color_dict["color"][:3]
            this_label = generate_sc_latency_label(this_sc_idx, sampling_rate)
            # for tps from SC1 to SCend - plot(joint1x, joint1y)
            for i in range(
                this_sc_idx[0], this_sc_idx[1] + 1
            ):  # timepoint loop (of this SC)
                this_ys = list()  # for each timepoint, define joints' xy coord new
                this_zs = list()
                for joint in plot_joints:
                    # check for bodyside-specificity
                    if joint + "Y" in all_steps_data.columns:
                        y_col_string = joint + "Y"
                        z_col_string = joint + "Z"
                    else:
                        y_col_string = transform_joint_and_leg_to_colname(
                            joint, legname, "Y"
                        )
                        z_col_string = transform_joint_and_leg_to_colname(
                            joint, legname, "Z"
                        )
                    this_ys.append(all_steps_data.loc[i, y_col_string])
                    this_zs.append(all_steps_data.loc[i, z_col_string])
                if i == range(this_sc_idx[0], this_sc_idx[1] + 1)[0]:
                    try:
                        ax[r].plot(
                            this_ys,
                            this_zs,
                            color=this_color,
                            lw=STICK_LINEWIDTH,
                            label=this_label,
                        )
                    except:
                        ax.plot(
                            this_ys,
                            this_zs,
                            color=this_color,
                            lw=STICK_LINEWIDTH,
                            label=this_label,
                        )
                else:  # no label
                    try:
                        ax[r].plot(
                            this_ys, this_zs, color=this_color, lw=STICK_LINEWIDTH
                        )
                    except:
                        ax.plot(this_ys, this_zs, color=this_color, lw=STICK_LINEWIDTH)
        # axis stuff
        try:
            if legend_outside is True:
                ax[r].legend(
                    fontsize=SC_LAT_LEGEND_FONTSIZE,
                    loc="center left",
                    bbox_to_anchor=(1, 0.5),
                )
            elif legend_outside is False:
                ax[r].legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
            median_z_val = [round(np.median(ax[r].get_yticks()), 2)]
            median_z_val_label = [str(median_z_val[0])]  # has to be of same len
            ax[r].set_yticks(median_z_val, median_z_val_label)
        except:
            if legend_outside is True:
                ax.legend(
                    fontsize=SC_LAT_LEGEND_FONTSIZE + 3,
                    loc="center left",
                    bbox_to_anchor=(1, 0.5),
                )
            elif legend_outside is False:
                ax.legend(fontsize=SC_LAT_LEGEND_FONTSIZE + 3)
            median_z_val = [round(np.median(ax.get_yticks()), 2)]
            median_z_val_label = [str(median_z_val[0])]  # has to be of same len
            ax.set_yticks(median_z_val, median_z_val_label)
        # title
        figure_file_string = name + " - " + legname + " - Stick Diagram"
        try:
            ax[0].set_title(figure_file_string)
        except:
            ax.set_title(figure_file_string)
    f.supxlabel("y (m)")
    f.supylabel("z (m)")
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_joint_z_by_average_SC(
    legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
):
    """5 - Plot joints' z as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    plot_SE = cfg["plot_SE"]
    joints = cfg["joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(joints)))
    )
    x = np.linspace(0, 100, bin_num)
    for joint in joints:  # joint loop (lines)
        # check for bodyside-specificity
        z_col = extract_feature_column(average_data, joint, legname, "Z")
        this_z = average_data.iloc[:, z_col]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, z_col] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, z_col]
        ax.plot(x, this_z, label=joint)
        ax.fill_between(x, this_z - this_std, this_z + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel("z (m)")
    figure_file_string = (
        name + " - " + legname + " - Joint z-coord.s over average step cycle"
    )
    ax.set_title(figure_file_string)
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_joint_y_by_average_SC(
    legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
):
    """5 - Plot joints' y as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    plot_SE = cfg["plot_SE"]
    joints = cfg["joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(joints)))
    )
    x = np.linspace(0, 100, bin_num)
    for joint in joints:  # joint loop (lines)
        # check for bodyside-specificity
        y_col = extract_feature_column(average_data, joint, legname, "Y")
        this_y = average_data.iloc[:, y_col]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col]
        ax.plot(x, this_y, label=joint)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel("y (m)")
    figure_file_string = (
        name + " - " + legname + " - Joint y-coord.s over average step cycle"
    )
    ax.set_title(figure_file_string)
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_angles_by_average_SC(
    legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
):
    """6 - Plot Angles as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    plot_SE = cfg["plot_SE"]
    angles = cfg["angles"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(angles["name"])))
    )
    x = np.linspace(0, 100, bin_num)
    ax.set_xlabel("Percentage")
    ax.set_ylabel("Angle (degree)")
    for angle in angles["name"]:  # angle loop (lines)
        # check for bodyside-specificity
        feature = "Angle"
        angle_col = extract_feature_column(average_data, angle, legname, feature)
        this_angle_val = average_data.iloc[:, angle_col]
        if plot_SE:
            this_std = std_data.iloc[:, angle_col] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, angle_col]  # average & std_data share colnames
        ax.plot(x, this_angle_val, label=angle)
        ax.fill_between(
            x, this_angle_val - this_std, this_angle_val + this_std, alpha=0.2
        )
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_ylim(ANGLE_PLOTS_YLIMITS)
    figure_file_string = (
        name + " - " + legname + " - Joint angles over average step cycle"
    )
    ax.set_title(figure_file_string)
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_y_velocities_by_average_SC(
    legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
):
    """7 - Plot x velocities as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    joints = cfg["joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(joints)))
    )
    x = np.linspace(0, 100, bin_num)
    for joint in joints:  # joint loop (lines)
        # check for bodyside-specificity
        feature = "Velocity"
        y_col = extract_feature_column(average_data, joint, legname, feature)
        this_y = average_data.iloc[:, y_col]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col]
        ax.plot(x, this_y, label=joint)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel("Velocity (Y in m / " + str(int((1 / sampling_rate) * 1000)) + "ms)")
    figure_file_string = (
        name + " - " + legname + " - Joint y-velocities over average step cycle"
    )
    ax.set_title(figure_file_string)
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_angular_velocities_by_average_SC(
    legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
):
    """8 - Plot angular velocities as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    angles = cfg["angles"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(angles["name"])))
    )
    x = np.linspace(0, 100, bin_num)
    for angle in angles["name"]:  # angle loop (lines)
        # check for bodyside-specificity
        feature = "Angle Velocity"
        y_col = extract_feature_column(average_data, angle, legname, feature)
        this_y = average_data.iloc[:, y_col]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col]
        ax.plot(x, this_y, label=angle)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel("Velocity (degree / " + str(int((1 / sampling_rate) * 1000)) + "ms)")
    figure_file_string = (
        name + " - " + legname + " - Angular velocities over average step cycle"
    )
    ax.set_title(figure_file_string)
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_y_acceleration_by_average_SC(
    legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
):
    """9 - (optional) Plot x acceleration as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    joints = cfg["joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(joints)))
    )
    x = np.linspace(0, 100, bin_num)
    for joint in joints:  # joint loop (lines)
        feature = "Acceleration"
        y_col = extract_feature_column(average_data, joint, legname, feature)
        this_y = average_data.iloc[:, y_col]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col]
        ax.plot(x, this_y, label=joint)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel(
        "Acceleration (Y in m / " + str(int((1 / sampling_rate) * 1000)) + "ms)"
    )
    figure_file_string = (
        name + " - " + legname + " - Joint y-accelerations over average step cycle"
    )
    ax.set_title(figure_file_string)
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_angular_acceleration_by_average_SC(
    legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
):
    """
    10 - (optional) Plot angular acceleration as a function of average SC's percentage
    """

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    angles = cfg["angles"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(angles["name"])))
    )
    x = np.linspace(0, 100, bin_num)
    for angle in angles["name"]:  # angle loop (lines)
        feature = "Angle Acceleration"
        y_col = extract_feature_column(average_data, angle, legname, feature)
        this_y = average_data.iloc[:, y_col]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col]
        ax.plot(x, this_y, label=angle)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel(
        "Acceleration (degree / " + str(int((1 / sampling_rate) * 1000)) + "ms)"
    )
    figure_file_string = (
        name + " - " + legname + " - Angular accelerations over average step cycle"
    )
    ax.set_title(figure_file_string)
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


# ..............................  helper functions  ....................................
def save_figures(figure, results_dir, figure_file_string):
    """Save figures as pngs to results_dir and as svgs to separate subfolders"""
    # pngs to results_dir
    figure.savefig(
        os.path.join(results_dir, figure_file_string + ".png"),
        bbox_inches="tight",
    )
    # svgs to subfolders
    svg_dir = os.path.join(results_dir, "SVG Figures")
    if not os.path.exists(svg_dir):
        os.makedirs(svg_dir)
    figure.savefig(
        os.path.join(svg_dir, figure_file_string + ".svg"), bbox_inches="tight"
    )


def extract_feature_column(df, joint, legname, feature):
    """Extract the column of a given joint (or angle) x legname (or not) x feature combo

    Note
    ----
    Only use this when using .iloc, not .loc!
    ==> the return statement gives the column-index to be used with .iloc!
    """
    if joint + feature in df.columns:
        string = joint + feature
    else:
        string = transform_joint_and_leg_to_colname(joint, legname, feature)
    return df.columns.get_loc(string)


def transform_joint_and_leg_to_colname(joint, legname, feature):
    """Transform a joint and leg name to Simi-column name"""
    return joint + ", " + legname + " " + feature


def generate_sc_latency_label(this_sc_idx, sampling_rate):
    if sampling_rate <= 100:
        float_precision = 2  # how many decimals we round to
    else:
        float_precision = 4
    this_label = (
        str(round(this_sc_idx[0] / sampling_rate, float_precision))
        + "-"
        + str(round(this_sc_idx[1] / sampling_rate, float_precision))
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
        self.plotwindow.title(
            f"AutoGaitA Figure {self.current_fig_index+1}/{len(self.figures)}"
        )

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
            # constrained layout to adjust margins within the figure
            # => note: in case there are a lot of steps in one run (-> the legend is
            #          super long) the figure won't be displayed properly.
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
            self.button_frame,
            text="<< Previous",
            fg_color=FG_COLOR,
            hover_color=HOVER_COLOR,
            command=self.show_previous,
        )
        self.next_button = ctk.CTkButton(
            self.button_frame,
            text="Next >>",
            fg_color=FG_COLOR,
            hover_color=HOVER_COLOR,
            command=self.show_next,
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

        # Update title
        self.plotwindow.title(
            f"AutoGaitA Plot Panel {self.current_fig_index+1}/{len(self.figures)}"
        )

    def destroy_plot_panel(self):
        # Needed if no SCs after checks
        self.loading_screen.destroy()


# %% local functions 5 - print finish


def print_finish(info, cfg):
    """Print that we finished this program"""
    print("\n***************************************************")
    print("* GAITA FINISHED - RESULTS WERE SAVED HERE:       *")
    print("* " + info["results_dir"] + " *")
    print("***************************************************")


# %% what happens if we just hit run
if __name__ == "__main__":
    simi_info_message = (
        "\n*************\nnot like this\n*************\n"
        + "You are trying to execute autogaita.simi as a script, but that is not "
        + "possible.\nIf you prefer a non-GUI approach, please either: "
        + "\n1. Call this as a function, i.e. autogaita.simi(info, folderinfo, cfg)"
        + "\n2. Use the single or multirun scripts in the batchrun_scripts folder"
    )
    print(simi_info_message)

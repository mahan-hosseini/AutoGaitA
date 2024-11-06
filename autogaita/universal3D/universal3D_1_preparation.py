# %% imports
from autogaita.gaita_res.utils import write_issues_to_textfile
import os
import shutil
import json
import pandas as pd
import numpy as np

# %% constants
from autogaita.universal3D.universal3D_constants import (
    LEGS_COLFORMAT,
    ISSUES_TXT_FILENAME,
    CONFIG_JSON_FILENAME,
    DF_TIME_COL,
)

# %% workflow step #1 - preparation


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
        return (None, None)

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
        "tracking_software": "Universal 3D",
    }
    # note - using "w" will overwrite/truncate file, thus no need to remove it if exists
    with open(config_json_path, "w") as config_json_file:
        json.dump(config_vars_to_json, config_json_file, indent=4)

    # Check if data has some col sayin "Time" in any form of capitalisation and if so
    # make sure it's capitalised
    if any(col.lower() == DF_TIME_COL.lower() for col in data.columns):
        data.columns = [
            col.capitalize() if col.lower() == DF_TIME_COL.lower() else col
            for col in data.columns
        ]
    # If for some reason (we had this with simi files) there are two Time = 0s, take
    # the second/last.
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
    # Note - this was before I knew what tests are
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

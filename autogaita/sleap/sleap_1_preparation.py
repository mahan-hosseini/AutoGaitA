# %% imports
from autogaita.resources.utils import write_issues_to_textfile
import os
import shutil
import json
import pandas as pd
import numpy as np
import h5py

# %% constants
from autogaita.resources.constants import (
    TIME_COL,
    ISSUES_TXT_FILENAME,
    CONFIG_JSON_FILENAME,
)


# %% workflow step #1 - preparation


def some_prep(info, folderinfo, cfg):
    """Preparation of the data & cfg file for later analyses"""

    # ............................  unpack stuff  ......................................
    # => DON'T unpack (joint) cfg-keys that are tested later by check_and_expand_cfg
    # SLEAP-specific NOTE
    # => I commented out vars that we dont need but might need in the future
    name = info["name"]
    results_dir = info["results_dir"]
    data_string = folderinfo["data_string"]
    beam_string = folderinfo["beam_string"]
    sampling_rate = cfg["sampling_rate"]
    # IMPORTANT NOTE
    # => subtract_beam is hardcoded to False until I have data that allows me to test
    #    it properly (same for gait direction flipping @ end of this function)
    cfg["subtract_beam"] = False
    subtract_beam = cfg["subtract_beam"]
    convert_to_mm = cfg["convert_to_mm"]
    pixel_to_mm_ratio = cfg["pixel_to_mm_ratio"]
    standardise_y_at_SC_level = cfg["standardise_y_at_SC_level"]
    # invert_y_axis = cfg["invert_y_axis"]
    flip_gait_direction = cfg["flip_gait_direction"]
    analyse_average_x = cfg["analyse_average_x"]
    standardise_x_coordinates = cfg["standardise_x_coordinates"]
    standardise_y_to_a_joint = cfg["standardise_y_to_a_joint"]

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
        )
        write_issues_to_textfile(no_files_error, info)
        print(no_files_error)
        return

    # ............................  import data  .......................................
    # initialise dfs for user error handling
    datadf = pd.DataFrame(data=None)
    datadf_duplicate_error = ""
    beamdf = pd.DataFrame(data=None)
    beamdf_duplicate_error = ""
    # loop through folder and import data
    for filename in os.listdir(results_dir):
        if name + data_string + ".h5" in filename:
            if datadf.empty:
                datadf = h5_to_df(results_dir, filename)
            else:
                datadf_duplicate_error = (
                    "\n******************\n! CRITICAL ERROR !\n******************\n"
                    + "Multiple DATA .h5 files found for "
                    + name
                    + "!\nPlease make sure to only have one data file per ID."
                )
        if subtract_beam and name + beam_string + ".h5" in filename:
            if beamdf.empty:
                beamdf = h5_to_df(results_dir, filename)
            else:
                beamdf_duplicate_error = (
                    "\n******************\n! CRITICAL ERROR !\n******************\n"
                    + "Multiple BEAM .h5 files found for "
                    + name
                    + "!\nPlease make sure to only have one beam file per ID."
                )
    # handle errors now
    import_error_message = ""
    if datadf_duplicate_error:
        import_error_message += datadf_duplicate_error
    if datadf.empty:
        import_error_message += (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "No DATA .h5 file found for "
            + name
            + "!\nTry again!"
        )
    if subtract_beam:
        if beamdf_duplicate_error:
            import_error_message += beamdf_duplicate_error
        if beamdf.empty:
            import_error_message += (
                "\n******************\n! CRITICAL ERROR !\n******************\n"
                + "No BEAM .h5 file found for "
                + name
                + "!\nTry again!"
            )
    if import_error_message:
        write_issues_to_textfile(import_error_message, info)
        print(import_error_message)
        return  # make sure to stop execution if there is an issue!
    # create "data" as floats and depending on whether we subtracted beam or not
    if subtract_beam:
        data = pd.concat([datadf, beamdf], axis=1)
    else:
        data = datadf.copy(deep=True)
    data = data.astype(float)

    # ................  final data checks, conversions & additions  ....................
    # IMPORTANT - MAIN TESTS OF USER-INPUT VALIDITY OCCUR HERE!
    # => UNPACK VARS FROM CFG THAT ARE TESTED BY check_and_expand HERE, NOT EARLIER!
    cfg = check_and_expand_cfg(data, cfg, info)
    if cfg is None:  # some critical error occured
        return
    hind_joints = cfg["hind_joints"]
    fore_joints = cfg["fore_joints"]
    angles = cfg["angles"]
    beam_hind_jointadd = cfg["beam_hind_jointadd"]
    beam_fore_jointadd = cfg["beam_fore_jointadd"]
    direction_joint = cfg["direction_joint"]
    # important to unpack to vars hand not to cfg since cfg is overwritten in multiruns!
    x_standardisation_joint = cfg["x_standardisation_joint"][0]
    y_standardisation_joint = cfg["y_standardisation_joint"][0]
    # store config json file @ group path
    # !!! NU - do this @ mouse path!
    group_path = results_dir.split(name)[0]
    config_json_path = os.path.join(group_path, CONFIG_JSON_FILENAME)
    config_vars_to_json = {
        "sampling_rate": sampling_rate,
        "convert_to_mm": convert_to_mm,
        "standardise_y_at_SC_level": standardise_y_at_SC_level,
        "analyse_average_x": analyse_average_x,
        "standardise_x_coordinates": standardise_x_coordinates,
        "x_standardisation_joint": x_standardisation_joint,
        "standardise_y_to_a_joint": standardise_y_to_a_joint,
        "y_standardisation_joint": y_standardisation_joint,
        "hind_joints": hind_joints,
        "fore_joints": fore_joints,
        "angles": angles,
        "tracking_software": "SLEAP",
    }
    # note - using "w" will overwrite/truncate file, thus no need to remove it if exists
    with open(config_json_path, "w") as config_json_file:
        json.dump(config_vars_to_json, config_json_file, indent=4)
    # if we don't have a beam to subtract, standardise y to a joint's or global ymin = 0
    if not subtract_beam:
        y_min = float("inf")
        y_cols = [col for col in data.columns if col.endswith("y")]
        if standardise_y_to_a_joint:
            y_min = data[y_standardisation_joint + "y"].min()
        else:
            y_min = data[y_cols].min().min()
        data[y_cols] -= y_min
    # convert pixels to millimeters
    if convert_to_mm:
        for column in data.columns:
            # if might be unnecessary but I'm cautious as I don't know SLEAP data much
            if column.endswith("x") or column.endswith("y"):
                data[column] = data[column] / pixel_to_mm_ratio

    # IMPORTANT NOTE
    # => I keep gait direction flipping commented out until receiving data that allows
    #    me to test it properly
    # => Note that subtract_beam is hardcoded to False above for the same reason

    # check gait direction & DLC file validity
    # data = check_gait_direction(data, direction_joint, flip_gait_direction, info)
    data["Flipped"] = False  # because of IMPORTANT NOTE above

    # subtract the beam from the joints to standardise y
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
    # add Time
    data[TIME_COL] = data.index * (1 / sampling_rate)
    # reorder the columns we added
    cols = [TIME_COL, "Flipped"]
    data = data[cols + [c for c in data.columns if c not in cols]]
    return data


# ..............................  helper functions  ....................................


def move_data_to_folders(info, folderinfo):
    """Copy data to new results_dir"""
    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    root_dir = folderinfo["root_dir"]
    data_string = folderinfo["data_string"]
    os.makedirs(results_dir)
    # move csv or h5 files
    for filename in os.listdir(root_dir):
        if name + data_string + ".csv" in filename:
            shutil.copy2(
                os.path.join(root_dir, filename),
                os.path.join(results_dir, filename),
            )
        elif name + data_string + ".h5" in filename:
            shutil.copy2(
                os.path.join(root_dir, filename),
                os.path.join(results_dir, filename),
            )


def h5_to_df(results_dir, filename):
    """Convert a SLEAP h5 file to a pandas dataframe used in gaita"""
    df = pd.DataFrame(data=None)
    with h5py.File(os.path.join(results_dir, filename), "r") as f:
        locations = f["tracks"][:].T
        node_names = [n.decode() for n in f["node_names"][:]]
        df.index = np.arange(np.shape(locations)[0])
        for node_idx, node_name in enumerate(node_names):
            for c, coord in enumerate(["x", "y"]):
                df[node_name + " " + coord] = locations[:, node_idx, c, 0]
    return df


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
    String-checks for standardisation joints
    """

    # run the tests first
    # => note that beamcols & standardisation joints are tested separately further down.
    for cfg_key in [
        "angles",
        "hind_joints",
        "fore_joints",
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
        # first, let's check the strings
        # => note beamcols are lists of len=1 bc. of check function
        for cfg_key in [
            "beam_col_left",
            "beam_col_right",
            "beam_hind_jointadd",
            "beam_fore_jointadd",
        ]:
            cfg[cfg_key] = check_and_fix_cfg_strings(data, cfg, cfg_key, info)
        beam_col_error_message = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "It seems like you want to standardise heights to a baseline (beam)."
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
    # never standardise @ SC level if user subtracted a beam
    if cfg["subtract_beam"] is True:
        cfg["standardise_y_at_SC_level"] = False
    # test x/y standardisation joints if needed
    broken_standardisation_joint = ""
    if cfg["standardise_x_coordinates"]:
        cfg["x_standardisation_joint"] = check_and_fix_cfg_strings(
            data, cfg, "x_standardisation_joint", info
        )
        if not cfg["x_standardisation_joint"]:
            broken_standardisation_joint += "x"
    if cfg["standardise_y_to_a_joint"]:
        cfg["y_standardisation_joint"] = check_and_fix_cfg_strings(
            data, cfg, "y_standardisation_joint", info
        )
        if not cfg["y_standardisation_joint"]:
            if broken_standardisation_joint:
                broken_standardisation_joint += " & y"
            else:
                broken_standardisation_joint += "y"
    if broken_standardisation_joint:
        no_standardisation_joint_message = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "After testing your standardisation joints we found an issue with "
            + broken_standardisation_joint
            + "-coordinate standardisation joint."
            + "\n Cancelling AutoGaitA - please try again!"
        )
        write_issues_to_textfile(no_standardisation_joint_message, info)
        print(no_standardisation_joint_message)
        return

    return cfg


def check_and_fix_cfg_strings(data, cfg, cfg_key, info):
    """Check and fix strings in our joint & angle lists so that:
    1) They don't include empty strings
    2) All strings end with the space character
       => Important note: strings should never have the coordinate in them (since we do
          string + "y" for example throughout this code)
    3) All strings are valid columns of the DLC dataset
       => Note that x_standardisation_joint is tested against ending with "x" - rest
          against "y"
    """

    # work on this variable (we return to cfg[key] outside of here)
    string_variable = cfg[cfg_key]

    # easy checks: lists
    if type(string_variable) is list:
        string_variable = [s for s in string_variable if s]
        string_variable = [s if s.endswith(" ") else s + " " for s in string_variable]
        clean_string_list = []
        invalid_strings_message = ""
        for string in string_variable:
            if cfg_key == "x_standardisation_joint":
                if string + "x" in data.columns:
                    clean_string_list.append(string)
                else:
                    invalid_strings_message += "\n" + string
            else:  # for y_standardisation_joint (& all other cases)!!
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

    # beloow == True means that the mouse ran from right to left
    # => in this case we flip
    if np.median(data[direction_joint + "x"][: len(data) // 2]) > np.median(
        data[direction_joint + "x"][len(data) // 2 :]
    ):
        if flip_gait_direction:
            data = flip_mouse_body(data, info)
            data["Flipped"] = True
    return data

# %% imports
from autogaita.resources.utils import write_issues_to_textfile


# %% common 2D (DLC & SLEAP) preparation functions
# => note that there are separate _1_preparation scripts in the respective first-level
#    folders - this script stores all functions that are constant across DLC & SLEAP


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
            + "your beam-file.\nPlease try again.\nInvalid beam side(s) was/were:"
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
    global_x_max = flipped_data[x_cols].max().max()
    for col in x_cols:
        flipped_data[col] = global_x_max - flipped_data[col]
    return flipped_data

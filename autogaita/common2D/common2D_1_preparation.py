# %% imports
from autogaita.resources.utils import write_issues_to_textfile
from autogaita.common2D.common2D_constants import FILE_ID_STRING_ADDITIONS
import os
import shutil
import json
import pandas as pd
import numpy as np
import h5py

# %% constants
from autogaita.resources.constants import (
    ISSUES_TXT_FILENAME,
    TIME_COL,
    CONFIG_JSON_FILENAME,
)
from autogaita.common2D.common2D_constants import (
    DIRECTION_DLC_THRESHOLD,
)

# %% workflow step #1 - preparation


def some_prep(tracking_software, info, folderinfo, cfg):
    """Preparation of the data & cfg file for dlc analyses"""

    # .........................  unpack & prep stuff  ..................................
    # IMPORTANT
    # ---------
    # file_type_string handles all places (like move_data_to_folders) where it makes a
    # difference if we are processing DLC or SLEAP files
    if tracking_software == "DLC":
        file_type_string = ".csv"
    elif tracking_software == "SLEAP":
        file_type_string = ".h5"
    # DON'T unpack (joint) cfg-keys that are tested later by check_and_expand_cfg
    name = info["name"]
    results_dir = info["results_dir"]
    data_string = folderinfo["data_string"]
    beam_string = folderinfo["beam_string"]
    sampling_rate = cfg["sampling_rate"]
    subtract_beam = cfg["subtract_beam"]
    convert_to_mm = cfg["convert_to_mm"]
    pixel_to_mm_ratio = cfg["pixel_to_mm_ratio"]
    standardise_y_at_SC_level = cfg["standardise_y_at_SC_level"]
    invert_y_axis = cfg["invert_y_axis"]
    flip_gait_direction = cfg["flip_gait_direction"]
    analyse_average_x = cfg["analyse_average_x"]
    standardise_x_coordinates = cfg["standardise_x_coordinates"]
    standardise_y_to_a_joint = cfg["standardise_y_to_a_joint"]

    # .............................  move data  ........................................
    # => slightly different for DLC or SLEAP (see local functions below)
    # => see if we can delete a previous runs results folder if existant. if not, it's a
    #    bit ugly since we only update results if filenames match...
    # => for example if angle acceleration not wanted in current run, but was stored in
    #    previous run, the previous run's figure is in the folder
    # => inform the user and leave this as is
    if os.path.exists(results_dir):
        try:
            shutil.rmtree(results_dir)
            move_data_to_folders(tracking_software, file_type_string, info, folderinfo)
        except OSError:
            move_data_to_folders(tracking_software, file_type_string, info, folderinfo)
            unable_to_rm_resdir_error = (
                "\n***********\n! WARNING !\n***********\n"
                + "Unable to remove previous Results subfolder of ID: "
                + name
                + "!\n Results will only be updated if filenames match!"
            )
            print(unable_to_rm_resdir_error)
            write_issues_to_textfile(unable_to_rm_resdir_error, info)
    else:
        move_data_to_folders(tracking_software, file_type_string, info, folderinfo)

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
        if filename.endswith(file_type_string):
            if data_string in filename:
                if datadf.empty:
                    if tracking_software == "DLC":
                        datadf = pd.read_csv(os.path.join(results_dir, filename))
                    elif tracking_software == "SLEAP":
                        datadf = h5_to_df(results_dir, filename)
                else:
                    datadf_duplicate_error = (
                        "\n******************\n! CRITICAL ERROR !\n******************\n"
                        + f"Two DATA {file_type_string}-files found for {name}"
                        + "!\nPlease ensure your root directory only has one datafile "
                        + "per video!"
                    )
            if subtract_beam:
                if beam_string in filename:
                    if beamdf.empty:
                        if tracking_software == "DLC":
                            beamdf = pd.read_csv(os.path.join(results_dir, filename))
                        elif tracking_software == "SLEAP":
                            beamdf = h5_to_df(results_dir, filename)
                    else:
                        beamdf_duplicate_error = (
                            "\n******************\n! CRITICAL ERROR !\n***************"
                            + f"***\nTwo BEAM {file_type_string}-files found for {name}"
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
            + f"Unable to load a DATA {file_type_string} file for {name}"
            + "!\nTry again!"
        )
    if subtract_beam:
        if beamdf_duplicate_error:
            import_error_message += beamdf_duplicate_error
        if beamdf.empty:
            import_error_message += (
                "\n******************\n! CRITICAL ERROR !\n******************\n"
                + f"Unable to load a BEAM {file_type_string} file for {name}"
                + "!\nTry again!"
            )
    if import_error_message:  # see if there was any issues with import, if so: stop
        print(import_error_message)
        write_issues_to_textfile(import_error_message, info)
        return

    # ....  finalise import: rename cols, get rid of unnecessary elements, floatit  ....
    if tracking_software == "DLC":  # need to prep DLC dfs
        datadf = prepare_DLC_df(datadf)
        if subtract_beam:  # beam df
            beamdf = prepare_DLC_df(beamdf)
    if subtract_beam:
        data = pd.concat([datadf, beamdf], axis=1)
    else:
        data = datadf.copy(deep=True)

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
    # important to unpack to vars and not to cfg since cfg is overwritten in multiruns!
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
        "tracking_software": tracking_software,
    }
    # note - using "w" will overwrite/truncate file, thus no need to remove it if exists
    with open(config_json_path, "w") as config_json_file:
        json.dump(config_vars_to_json, config_json_file, indent=4)
    # a little test to see if columns make sense, i.e., same number of x/y/likelihood
    x_col_count = len([c for c in data.columns if c.endswith(" x")])
    y_col_count = len([c for c in data.columns if c.endswith(" y")])
    likelihood_col_count = "N/A because SLEAP"  # initialise so message doesnt break
    if tracking_software == "DLC":
        likelihood_col_count = len(
            [c for c in data.columns if c.endswith(" likelihood")]
        )
        col_count_condition = x_col_count == y_col_count == likelihood_col_count
    elif tracking_software == "SLEAP":
        col_count_condition = x_col_count == y_col_count
    if col_count_condition:
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
            if not column.endswith("likelihood"):
                data[column] = data[column] / pixel_to_mm_ratio
    # quick warning if cfg is set to not flip gait direction but to standardise x
    if not flip_gait_direction and standardise_x_coordinates:
        message = (
            "\n***********\n! WARNING !\n***********\n"
            + "You are standardising x-coordinates without standardising the direction "
            + "of gait (e.g. all walking from right to left)."
            + "\nThis can be correct if you are doing things like treadmill walking "
            + "but can lead to unexpected behaviour otherwise!"
            + "\nMake sure you know what you are doing!"
        )
        print(message)
        write_issues_to_textfile(message, info)
    # check gait direction & DLC file validity
    data = check_gait_direction(
        tracking_software, data, direction_joint, flip_gait_direction, info
    )
    if data is None:  # this means DLC file is broken
        return
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


# ........................  tracking software specific helpers  ........................
def h5_to_df(results_dir, filename):
    """Convert a SLEAP h5 file to the pandas dataframe used in gaita"""
    df = pd.DataFrame(data=None)
    with h5py.File(os.path.join(results_dir, filename), "r") as f:
        locations = f["tracks"][:].T
        node_names = [n.decode() for n in f["node_names"][:]]
        df.index = np.arange(np.shape(locations)[0])
        for node_idx, node_name in enumerate(node_names):
            for c, coord in enumerate(["x", "y"]):
                df[node_name + " " + coord] = locations[:, node_idx, c, 0]
    return df


def prepare_DLC_df(df, separator=" "):
    """Prepare the DLC dataframe after loading w.r.t. column names & df-index
    Note
    ----
    separator is used in universal3D_datafile_preparation
    """
    new_column_strings = list()  # data df
    for j in range(df.shape[1]):
        new_column_strings.append(df.iloc[0, j] + separator + df.iloc[1, j])
    df.columns = new_column_strings
    # next lines indices are because: scorer row becomes the column, bodypart row is row
    # 0, coords row is row 1 and we thus include row 2 onwards. col 1 onwards is obvious
    df = df.iloc[2:, 1:]
    df.index = range(len(df))
    df = df.astype(float)
    return df


# ...............................  generic helpers  ....................................


def move_data_to_folders(tracking_software, file_type_string, info, folderinfo):
    """Find files, copy data, video, beamdata & beamvideo to new results_dir"""
    # unpack
    results_dir = info["results_dir"]
    postmouse_string = folderinfo["postmouse_string"]
    postrun_string = folderinfo["postrun_string"]
    os.makedirs(results_dir)  # important to do this outside of loop!
    # check if user forgot some underscores or dashes in their filenames
    # => two levels of string additions for two post FILE-ID strings
    # => in theory if the user has some strange cases in which this double forloop
    # would be true twice (because one file is called -6DLC and another is called _6DLC
    # for some reason) it will break after the first time and always ignore the second
    # one - keep this in mind if it should come up but it should be very unlikely
    for mouse_string_addition in FILE_ID_STRING_ADDITIONS:
        candidate_postmouse_string = mouse_string_addition + postmouse_string
        for run_string_addition in FILE_ID_STRING_ADDITIONS:
            candidate_postrun_string = run_string_addition + postrun_string
            found_it = check_this_filename_configuration(
                tracking_software,
                file_type_string,
                info,
                folderinfo,
                candidate_postmouse_string,
                candidate_postrun_string,
                results_dir,
            )
            if found_it:  # if our search was successful, stop searching and continue
                break


def check_this_filename_configuration(
    tracking_software,
    file_type_string,
    info,
    folderinfo,
    postmouse_string,
    postrun_string,
    results_dir,
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
            and (filename.endswith(file_type_string))
        ):
            found_it = True
            # Copy the csv/h5 file to the new subfolder
            shutil.copy2(
                os.path.join(root_dir, filename), os.path.join(results_dir, filename)
            )
            # Check if there is a video and if so copy it too (only for DLC atm)
            if tracking_software == "DLC":
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


def check_gait_direction(
    tracking_software, data, direction_joint, flip_gait_direction, info
):
    """Check direction of gait - reverse it if needed

    Note for DLC
    ------------
    Also using this check to check for DLC files being broken
    flip_gait_direction is only used after the check for DLC files being broken
    """

    # AN IMPORTANT NOTE
    # -----------------
    # The general approach is different for DLC and much more involved. Besides the
    # check for DLC files being broken, the np.median() approach used for SLEAP (in the
    # end) of this function cannot be used too well for DLC IMO because DLC has those
    # huge numbers when estimating without being confident that would mess with the
    # medians

    # INITIALISE FLIPPED COLUMN
    data["Flipped"] = False

    # DLC APPROACH
    if tracking_software == "DLC":
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

    # SLEAP APPROACH
    elif tracking_software == "SLEAP":
        # beloow if condition means that the mouse ran from right to left
        # => in this case we flip
        if np.median(data[direction_joint + "x"][: len(data) // 2]) > np.median(
            data[direction_joint + "x"][len(data) // 2 :]
        ):
            if flip_gait_direction:
                data = flip_mouse_body(data, info)
                data["Flipped"] = True

    # RETURN DATA
    return data


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

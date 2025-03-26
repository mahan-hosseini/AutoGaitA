# %% imports
from autogaita.resources.utils import write_issues_to_textfile
from autogaita.common2D.common2D_1_preparation import (
    check_and_expand_cfg,
    flip_mouse_body,
)
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

    # VERY
    # VERY
    # VERY
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

    # check gait direction
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
    # move h5 files
    for filename in os.listdir(root_dir):
        if name + data_string + ".h5" in filename:
            shutil.copy2(
                os.path.join(root_dir, filename),
                os.path.join(results_dir, filename),
            )


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


def check_gait_direction(data, direction_joint, flip_gait_direction, info):
    """Check direction of gait - reverse it if needed"""

    data["Flipped"] = False

    # beloow if condition means that the mouse ran from right to left
    # => in this case we flip
    if np.median(data[direction_joint + "x"][: len(data) // 2]) > np.median(
        data[direction_joint + "x"][len(data) // 2 :]
    ):
        if flip_gait_direction:
            data = flip_mouse_body(data, info)
            data["Flipped"] = True
    return data

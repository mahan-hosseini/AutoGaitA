# %% imports
from autogaita.resources.utils import (
    write_issues_to_textfile,
    bin_num_to_percentages,
)
import os
import pandas as pd
import numpy as np
import math
import warnings

# %% constants
from autogaita.resources.constants import SC_PERCENTAGE_COL
from autogaita.universal3D.universal3D_constants import (
    LEGS,
    LEGS_COLFORMAT,
    OUTPUTS,
    ORIGINAL_XLS_FILENAME,
    NORMALISED_XLS_FILENAME,
    AVERAGE_XLS_FILENAME,
    STD_XLS_FILENAME,
    SEPARATOR_IDX,
    LEG_COL,
    EXCLUDED_COLS_IN_AV_STD_DFS,
    REORDER_COLS_IN_STEP_NORMDATA,
)

# %% workflow step #3 - y-flipping, features, df-creation & exports
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
                this_step, global_Y_max, cfg
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
                first_step, global_Y_max, cfg
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
                    this_step, global_Y_max, cfg
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
                    columns=[LEG_COL],
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
                    columns=[LEG_COL],
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


def norm_z_flip_y_and_add_features_to_one_step(step, global_Y_max, cfg):
    """For a single step cycle's data, normalise z if wanted, flip y columns if needed
    (to simulate equal run direction) and add features (angles & velocities)
    """
    # unpack
    standardise_z_at_SC_level = cfg["standardise_z_at_SC_level"]
    standardise_z_to_a_joint = cfg["standardise_z_to_a_joint"]
    z_standardisation_joint = cfg["z_standardisation_joint"]
    flip_gait_direction = cfg["flip_gait_direction"]
    direction_joint = cfg["direction_joint"]
    # if user wanted this, normalise z (height) at step-cycle level
    step_copy = step.copy()
    if standardise_z_at_SC_level is True:
        z_cols = [col for col in step_copy.columns if col.endswith("Z")]
        if standardise_z_to_a_joint is True:
            # note the [0] here is important because it's still a list of len=1!!
            z_minimum = step_copy[z_standardisation_joint[0] + "Z"].min()
        else:
            z_minimum = min(step_copy[z_cols].min())
        step_copy[z_cols] -= z_minimum
    # if user wanted flipping & if we need to flip y cols of this given step do so
    if flip_gait_direction:
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
       -- Add this to the documentation and tell people to fix their columns if
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
        if isinstance(bins[0], list):  # we need to average
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
    initialisation_data = bin_num_to_percentages(bin_num)
    # only for 3D - make a list of the percentages list that is output
    initialisation_data = [initialisation_data]
    initialisation_columns = [SC_PERCENTAGE_COL]
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
            and dataframe_list[0].columns[0] == SC_PERCENTAGE_COL
        ):
            only_one_valid_leg = "right"
        if (
            len(dataframe_list[1].columns) == 1
            and dataframe_list[1].columns[0] == SC_PERCENTAGE_COL
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

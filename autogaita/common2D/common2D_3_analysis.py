# %% imports
from autogaita.resources.utils import bin_num_to_percentages, compute_angle
import os
import warnings
import pandas as pd
import numpy as np
import math

# %% constants
from autogaita.resources.constants import TIME_COL, SC_PERCENTAGE_COL
from autogaita.common2D.common2D_constants import (
    ORIGINAL_XLS_FILENAME,
    NORMALISED_XLS_FILENAME,
    AVERAGE_XLS_FILENAME,
    STD_XLS_FILENAME,
    X_STANDARDISED_XLS_FILENAME,
)


# %% workflow step #3 - analysis: normalise SCs & export (orig. & norm.) XLS files
# Note
# ----
# There is quite a lot going on in this function. We:
# 1) loop through all step cycles for one leg at a time and extract data
# 2) for each step's data we normalise all y (height) values to the body's minimum
#    if wanted
# 3) we compute and add features (angles, velocities, accelerations)
#    ==> see standardise_x_y_and_add_features_to_one_step & helper functions a
# 4) immediately after adding features, we normalise a step to bin_num
#    ==> see normalise_one_steps_data & helper functions b
# 5) we add original and normalised steps to all_steps_data and normalised_steps_data
# 6) once we are done with this we create average and std dataframes7
# 7) we finally output all df-lists in a results dict and export each df-list as xls/csv
#   ==> see helper functions d


def analyse_and_export_stepcycles(data, all_cycles, info, cfg):
    """Export original-length and normalised XLS files of extracted steps"""
    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    save_to_xls = cfg["save_to_xls"]
    analyse_average_x = cfg["analyse_average_x"]
    bin_num = cfg["bin_num"]
    standardise_x_coordinates = cfg["standardise_x_coordinates"]
    # do everything on a copy of the data df
    data_copy = data.copy()
    # exactly 1 step
    if len(all_cycles) == 1:
        this_step = data_copy.loc[all_cycles[0][0] : all_cycles[0][1]]
        if standardise_x_coordinates:
            all_steps_data, x_standardised_steps_data = (
                standardise_x_y_and_add_features_to_one_step(this_step, cfg)
            )
            normalised_steps_data = normalise_one_steps_data(
                x_standardised_steps_data, bin_num
            )
        else:
            all_steps_data = standardise_x_y_and_add_features_to_one_step(
                this_step, cfg
            )
            normalised_steps_data = normalise_one_steps_data(all_steps_data, bin_num)
    # 2 or more steps - build dataframe
    elif len(all_cycles) > 1:
        # first- step is added manually
        # NOTE
        # ----
        # normalised_steps_data is created using x_standardised_steps_data or first_step
        first_step = data_copy.loc[all_cycles[0][0] : all_cycles[0][1]]
        if standardise_x_coordinates:
            all_steps_data, x_standardised_steps_data = (
                standardise_x_y_and_add_features_to_one_step(first_step, cfg)
            )
            normalised_steps_data = normalise_one_steps_data(
                x_standardised_steps_data, bin_num
            )
        else:
            all_steps_data = standardise_x_y_and_add_features_to_one_step(
                first_step, cfg
            )
            normalised_steps_data = normalise_one_steps_data(all_steps_data, bin_num)
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
            # this_step
            this_step = data_copy.loc[all_cycles[s][0] : all_cycles[s][1]]
            if standardise_x_coordinates:
                this_step, this_x_standardised_step = (
                    standardise_x_y_and_add_features_to_one_step(this_step, cfg)
                )
                this_normalised_step = normalise_one_steps_data(
                    this_x_standardised_step, bin_num
                )
            else:
                this_step = standardise_x_y_and_add_features_to_one_step(this_step, cfg)
                this_normalised_step = normalise_one_steps_data(this_step, bin_num)
            # step separators & step-to-rest-concatenation
            # => note that normalised_step is already based on x-stand if required
            all_steps_data = add_step_separators(all_steps_data, nanvector, numvector)
            all_steps_data = pd.concat([all_steps_data, this_step], axis=0)
            if standardise_x_coordinates:
                x_standardised_steps_data = add_step_separators(
                    x_standardised_steps_data, nanvector, numvector
                )
                x_standardised_steps_data = pd.concat(
                    [x_standardised_steps_data, this_x_standardised_step], axis=0
                )
            normalised_steps_data = add_step_separators(
                normalised_steps_data, nanvector, numvector
            )
            normalised_steps_data = pd.concat(
                [normalised_steps_data, this_normalised_step], axis=0
            )
    # compute average & std data
    # => note that normalised_steps_data is automatically based on x-standardisation
    #    which translates to average_data & std_data
    average_data, std_data = compute_average_and_std_data(
        normalised_steps_data, bin_num, analyse_average_x
    )
    # save to results dict
    results = {}
    results["all_steps_data"] = all_steps_data
    results["average_data"] = average_data
    results["std_data"] = std_data
    results["all_cycles"] = all_cycles
    if standardise_x_coordinates:
        results["x_standardised_steps_data"] = x_standardised_steps_data
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
    if standardise_x_coordinates:
        save_results_sheet(
            x_standardised_steps_data,
            save_to_xls,
            os.path.join(results_dir, name + X_STANDARDISED_XLS_FILENAME),
        )
    return results


# ......................................................................................
# ............  helper functions a - standardise x, y and add features  ................
# ......................................................................................


def standardise_x_y_and_add_features_to_one_step(step, cfg):
    """For a single step cycle's data, standardise x & y if wanted and add features"""
    # if user wanted this, standardise y (height) at step-cycle level
    step_copy = step.copy()
    if cfg["standardise_y_at_SC_level"] is True:
        y_cols = [col for col in step_copy.columns if col.endswith("y")]
        if cfg["standardise_y_to_a_joint"] is True:
            # note the [0] here is important because it's still a list of len=1!!
            this_y_min = step_copy[cfg["y_standardisation_joint"][0] + "y"].min()
        else:
            this_y_min = step_copy[y_cols].min().min()
        step_copy[y_cols] -= this_y_min
    # if no x-standardisation, just add features & return non-(x-)normalised step
    if cfg["standardise_x_coordinates"] is False:
        non_stand_step = add_features(step_copy, cfg)
        return non_stand_step
        # else standardise x (horizontal dimension) at step-cycle level too
    else:
        non_stand_step = add_features(step_copy, cfg)
        x_stand_step = step_copy.copy()
        x_cols = [col for col in x_stand_step.columns if col.endswith("x")]
        # note the [0] here is important because it's still a list of len=1!!
        min_x_standardisation_joint = x_stand_step[
            cfg["x_standardisation_joint"][0] + "x"
        ].min()
        x_stand_step[x_cols] -= min_x_standardisation_joint
        x_stand_step = add_features(x_stand_step, cfg)
        return non_stand_step, x_stand_step


def add_features(step, cfg):
    """Add Features, i.e. Angles & Velocities"""
    # unpack
    hind_joints = cfg["hind_joints"]
    angles = cfg["angles"]
    if hind_joints:
        step = add_x_velocities(step, cfg)
    if angles["name"]:  # if there is at least 1 string in the list
        step = add_angles(step, cfg)
        step = add_angular_velocities(step, cfg)
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


def add_x_velocities(step, cfg):
    """Feature #2: Joint x Velocities & Accelerations"""
    # unpack
    hind_joints = cfg["hind_joints"]
    x_acceleration = cfg["x_acceleration"]

    for joint in hind_joints:
        step[joint + "Velocity"] = 0.0
        if x_acceleration:
            step[joint + "Acceleration"] = 0.0
    for joint in hind_joints:
        step.loc[:, joint + "Velocity"] = np.gradient(step.loc[:, joint + "x"])
        if x_acceleration:
            step.loc[:, joint + "Acceleration"] = np.gradient(
                step.loc[:, joint + "Velocity"]
            )
    return step


def add_angular_velocities(step, cfg):
    """Feature #3: Angular Velocities & Accelerations"""
    # unpack
    angular_acceleration = cfg["angular_acceleration"]

    angle_cols = [c for c in step.columns if c.endswith("Angle")]
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


def compute_average_and_std_data(normalised_steps_data, bin_num, analyse_average_x):
    """Export XLS tables that store all averages & std of y-coords & angles"""
    # initialise col of % of SC over time for plotting first
    percentages = bin_num_to_percentages(bin_num)
    average_data = pd.DataFrame(
        data=percentages, index=range(bin_num), columns=[SC_PERCENTAGE_COL]
    )
    std_data = pd.DataFrame(
        data=percentages, index=range(bin_num), columns=[SC_PERCENTAGE_COL]
    )
    sc_num = len(np.where(normalised_steps_data.index == 0)[0])
    for c, col in enumerate(normalised_steps_data.columns):
        if analyse_average_x:
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

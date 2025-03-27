# %% imports
from autogaita.resources.utils import bin_num_to_percentages, write_issues_to_textfile
import os
import pandas as pd
import numpy as np
import warnings

# %% constants
from autogaita.resources.constants import (
    ID_COL,
    SC_PERCENTAGE_COL,
)
from autogaita.group.group_constants import (
    NORM_SHEET_NAME,
    ORIG_SHEET_NAME,
    X_STANDARDISED_SHEET_NAME,
    AVG_GROUP_SHEET_NAME,
    STD_GROUP_SHEET_NAME,
    G_AVG_GROUP_SHEET_NAME,
    G_STD_GROUP_SHEET_NAME,
    # SPLIT STRING (for _dlc first-level) & COLS OF DFs CREATED IN THIS SCRIPT
    SPLIT_STRING,
    SC_NUM_COL,
    N_COL,  # for grand average dfs
)


# %% ..........  workflow step #2 - data processing (imports, averages & stds)   .......


# %% .................  local functions #1 - import run-level results  .................


# .................................  main functions  ...................................
def import_data(folderinfo, cfg):
    """Loop over all valid_results_folders of each group's /Results/ folder and create
    dfs of normalised and original (latter called "_raw") step-cycle datasets
    """

    # unpack
    group_names = folderinfo["group_names"]
    group_dirs = folderinfo["group_dirs"]
    results_dir = folderinfo["results_dir"]
    save_to_xls = cfg["save_to_xls"]
    which_leg = cfg["which_leg"]
    tracking_software = cfg["tracking_software"]
    standardise_x_coordinates = False  # update next if needed
    if "standardise_x_coordinates" in cfg.keys():
        standardise_x_coordinates = cfg["standardise_x_coordinates"]

    # prepare lists of group-level dfs
    df_dict = {
        "Normalised": [pd.DataFrame(data=None)] * len(group_names),
        "Original": [pd.DataFrame(data=None)] * len(group_names),
    }
    if standardise_x_coordinates:
        df_dict["X-Standardised"] = [pd.DataFrame(data=None)] * len(group_names)

    # loop over each subfolder in each group-dir (i.e. "Results")
    for g, group_dir in enumerate(group_dirs):
        group_name = group_names[g]  # for import and combine function
        # valid_results_folders is the subset of all_results_folders in which valid
        # results were found (i.e., at least 1 valid SC was extracted & analysed)
        all_results_folders = os.listdir(group_dir)
        valid_results_folders = []
        for folder in all_results_folders:
            if (
                os.path.exists(
                    os.path.join(
                        group_dir,
                        folder,
                        folder + " - " + ORIG_SHEET_NAME + ".csv",
                    )
                )
            ) or (
                os.path.exists(
                    os.path.join(
                        group_dir,
                        folder,
                        folder + " - " + ORIG_SHEET_NAME + ".xlsx",
                    )
                )
            ):
                valid_results_folders.append(folder)
        # loop over all valid results folders and add to the different types
        # of group-dfs (which_df can be Original, Normalised or X-Standardised)
        for which_df in df_dict.keys():
            for name in valid_results_folders:
                df_dict[which_df][g] = import_and_combine_dfs(
                    df_dict[which_df][g],
                    which_df,
                    group_name,
                    group_dir,
                    tracking_software,
                    name,
                    which_leg,
                    folderinfo,
                    cfg,
                )
            df_dict[which_df][g] = final_df_checks_and_save_to_xls(
                df_dict[which_df][g],
                results_dir,
                group_name,
                which_df,
                save_to_xls[g],
                tracking_software,
            )
    # test: is bin_num is consistent across our groups
    # => if so, add it as well as one_bin_in_% to cfg
    cfg["bin_num"] = test_bin_num_consistency(
        df_dict["Normalised"], group_names, folderinfo
    )
    dfs = df_dict["Normalised"]
    raw_dfs = df_dict["Original"]
    return dfs, raw_dfs, cfg


def final_df_checks_and_save_to_xls(
    this_df, results_dir, group_name, which_df, save_to_xls, tracking_software
):
    """Some final checks and saving to xls
    Note
    ----
    this_df is a given df of a given condition and of a given group (we have a nested loop outside of this function!)
    => After valid results folders have been added (i.e. the group-df has been
       completed)
    """
    # reorder the columns we added
    if tracking_software in ["DLC", "SLEAP"]:
        cols = [ID_COL, "Run", "Stepcycle", "Flipped", "Time"]
    elif tracking_software == "Universal 3D":
        cols = [ID_COL, "Leg", "Stepcycle", "Time"]
    this_df = this_df[cols + [c for c in this_df.columns if c not in cols]]
    # check if there's rows with consecutive np.nan entries
    # => this happened while testing for some strange edge case I didn't understand)
    # => if so, remove them so we only have 1 row of np.nan
    all_nan_df = this_df.isna().all(axis=1)
    consecutive_nan_df = all_nan_df & all_nan_df.shift(fill_value=False)
    this_df = this_df[~consecutive_nan_df]
    # save as sheet file and return
    sheet_constant_string = ORIG_SHEET_NAME.split(" ")[1]
    filepath = os.path.join(
        results_dir, group_name + " - " + which_df + " " + sheet_constant_string
    )
    save_results_sheet(this_df, save_to_xls, filepath)
    return this_df


def test_bin_num_consistency(dfs, group_names, folderinfo):
    """Tests if bin number of step-cycle normalisation is consistent across groups"""
    # For this we use sc_breaks [i.e. the nan step-separators]) to see if bin_num is the
    # same value across all individual step-cycles across all groups.
    # Raise ValueError, stop everything & save info to Issues textfile if bin_num
    # should change at some point!
    # ==> check if normalised SC length is equal for all SCs
    # ==> break after SC1 == len of normalised SCs
    # ==> 0:24 = len of 25, with 25 being idx of first (nan) break

    bin_num = 0
    for g, group_name in enumerate(group_names):
        sc_breaks = np.where(pd.isnull(dfs[g][ID_COL]))[0]
        if bin_num == 0:
            bin_num = sc_breaks[0]
        for b in range(1, len(sc_breaks)):
            this_bin_num = sc_breaks[b] - sc_breaks[b - 1] - 1
            if this_bin_num != bin_num:
                bin_num_error_helper_function(
                    folderinfo, dfs, g, group_names, sc_breaks, b
                )
        # handle the last step-cycle of the df (it doesn't have a sc_break after it!)
        if (len(dfs[g]) - sc_breaks[-1] - 1) != this_bin_num:
            bin_num_error_helper_function(folderinfo, dfs, g, group_names, sc_breaks, b)
    return bin_num


def bin_num_error_helper_function(folderinfo, dfs, g, group_names, sc_breaks, b):
    """Handle this error in a separate function for readability"""
    id_col_idx = dfs[g].columns.get_loc(ID_COL)
    message = (
        "\n*********\n! ERROR !\n*********\n"
        + "\nSC Normalisation bin number mismatch for:"
        + "\nGroup: "
        + group_names[g]
        + " - ID: "
        + str(dfs[g].iloc[sc_breaks[b] - 3, id_col_idx])
        + "\nPlease re-run & make sure all bin numbers match!"
    )
    print(message)
    write_issues_to_textfile(message, folderinfo)
    raise ValueError(message)


def check_PCA_and_stats_variables(df, group_name, name, folderinfo, cfg):
    """Tests if PCA & stats variables are present in all groups' datasets"""
    PCA_variables = cfg["PCA_variables"]
    stats_variables = cfg["stats_variables"]
    if PCA_variables:
        if not all(variable in df.columns for variable in PCA_variables):
            missing_PCA_variables = [
                variable for variable in PCA_variables if variable not in df.columns
            ]
            missing_PCA_variables_str = "\n".join(missing_PCA_variables)
            PCA_variable_mismatch_message = (
                "\n*********\n! ERROR !\n*********\n"
                + "\nNot all features you asked us to analyse WITH PCA were present in "
                + "the dataset of:\n"
                + group_name
                + "'s "
                + name
                + "\nMissing variables were:\n"
                + missing_PCA_variables_str
                + "\nPlease re-run & make sure all variables are present!"
            )
            print(PCA_variable_mismatch_message)
            write_issues_to_textfile(PCA_variable_mismatch_message, folderinfo)
            raise ValueError(PCA_variable_mismatch_message)
    if stats_variables:
        if not all(variable in df.columns for variable in stats_variables):
            missing_stats_variables = [
                variable for variable in stats_variables if variable not in df.columns
            ]
            missing_stats_variables_str = "\n".join(missing_stats_variables)
            stats_variable_mismatch_message = (
                "\n*********\n! ERROR !\n*********\n"
                + "\nNot all features you asked us to analyse STATISTICALLY were "
                + "present in the dataset of:\n"
                + group_name
                + "'s "
                + name
                + "\nMissing variables were:\n"
                + missing_stats_variables_str
                + "\nPlease re-run & make sure all variables are present!"
            )
            print(stats_variable_mismatch_message)
            write_issues_to_textfile(stats_variable_mismatch_message, folderinfo)
            raise ValueError(stats_variable_mismatch_message)


def import_and_combine_dfs(
    group_df,
    which_df,
    group_name,
    group_dir,
    tracking_software,
    name,
    which_leg,
    folderinfo,
    cfg,
):
    """Import one run's df at a time and combine to group-level df"""
    if which_df == "Normalised":
        this_sheet_name = NORM_SHEET_NAME
    elif which_df == "Original":
        this_sheet_name = ORIG_SHEET_NAME
    elif which_df == "X-Standardised":
        this_sheet_name = X_STANDARDISED_SHEET_NAME
    fullfilepath = os.path.join(group_dir, name, name + " - " + this_sheet_name)
    if tracking_software in ["DLC", "SLEAP"]:
        df = load_sheet_file(fullfilepath)
    elif tracking_software == "Universal 3D":
        df = load_sheet_file(fullfilepath, which_leg=which_leg)
    if df is None:
        this_message = (
            "\n***********\n! WARNING !\n***********\n"
            + "No "
            + which_df
            + " results sheet file found for "
            + name
            + " at\n"
            + group_dir
            + ".\nSkipping!"
        )
        print(this_message)
        write_issues_to_textfile(this_message, folderinfo)
    else:
        df_copy = df.copy()
        # test: are our PCA & stats variables present in this ID's dataset?
        check_PCA_and_stats_variables(df_copy, group_name, name, folderinfo, cfg)
        # add some final info & append to group_df
        if tracking_software in ["DLC", "SLEAP"]:
            # add this run's info to df (& prepare Stepcycle column)
            # => I call DLC stuff ID NUM - RUN NUM, so we can use temp_split & idxing
            #    as done below
            temp_split = name.split(SPLIT_STRING)
            mouse_num = int(temp_split[0].split(" ")[1])  # temp_split[0] == ID X
            run_num = int(temp_split[1].split(" ")[1])  # temp_split[1] == RUN X
            df_copy["Run"] = run_num
            df_copy[ID_COL] = mouse_num
        elif tracking_software == "Universal 3D":
            df_copy[ID_COL] = name
        df_copy["Stepcycle"] = np.nan
        sc_col_idx = df_copy.columns.get_loc("Stepcycle")
        # add this df to group dfs
        sc_idxs = extract_sc_idxs(df_copy)
        for sc in range(len(sc_idxs)):
            df_copy.iloc[sc_idxs[sc], sc_col_idx] = sc + 1  # stepcycle info column
            if group_df.empty:
                group_df = df_copy.iloc[sc_idxs[sc]]
            else:
                nanvector = df_copy.loc[[1]]
                # new for pandas 2.2.2 - change all cols to floats so its compatible
                # with np.nan concatenation (does this break anything?)
                # => 07.08. - Leaving this for when I have unit tests for universal3D & group
                # => Not sure it'll work well like this I feel like it will take more
                #    than just changing the dtype
                # => For now ignoring warnings so users don't get annoyed (and because
                #    dtype incompatibility doesn't matter too much for us)
                # nanvector = nanvector.astype(float)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    nanvector[:] = np.nan
                group_df = pd.concat([group_df, nanvector], axis=0)
                group_df = pd.concat([group_df, df_copy.iloc[sc_idxs[sc]]], axis=0)
    # if there was no valid sheet file for this name, we are returning group_df without
    # it - we warned the user
    return group_df


# ................................  helper functions  ..................................


def save_results_sheet(dataframe, save_to_xls, fullfilepath):
    """Save a csv or xls of results"""
    if save_to_xls:
        dataframe.to_excel(fullfilepath + ".xlsx", index=False)
    else:
        dataframe.to_csv(fullfilepath + ".csv", index=False)


def load_sheet_file(fullfilepath, **kwargs):
    """Handle that the user might have saved csv or xls files

    Important
    ---------
    ==> We also handle that we have 3 sheets for human analyses, user has to decide
        which leg (sheet) they want to analyse
    ==> We keep this independent of save_to_xls, because save_to_xls allows us to save
        group outputs to xlsx if some IDs were saved to csv and others to xlsx.. But,
        here we have to be sure that we can load both cases, irrespective of what
        save_to_xls is!
    """
    try:  # see if we have an exel file
        if "which_leg" in kwargs:
            which_leg = kwargs["which_leg"]
            df = pd.read_excel(fullfilepath + ".xlsx", sheet_name=which_leg)
        else:
            df = pd.read_excel(fullfilepath + ".xlsx")
        return df
    except FileNotFoundError:
        try:  # see if we have a csv file
            df = pd.read_csv(fullfilepath + ".csv")
            return df
        # if both are not found there are no files
        # => note that this is unlikely since we previously made sure to only
        #    consider valid_results_folders that had a normalised sheet file
        except FileNotFoundError:
            return


def extract_sc_idxs(df):
    """Extract step-cycle indices using original & normalised CSV files"""
    # A note on df & nan (see xls_separations):
    # ==> (Using range & iloc so we don't have to subtract 1 to nan-idxs)
    # ==> if there is more than 1 SC found, the first row of nan indicates the
    #     END of SC 1
    # ==> the last row of nan indicates the START of the last SC
    # ==> everything inbetween is alternatingly: (if you add 1 to nan-idx) the
    #     start of an SC + (if you subtract -1 to nan-idx) the end of that SC
    # ==> E.g.: separations[1]+1 is 1st idx of SC2 - separations[2]-1 is last
    #     idx of SC2
    first_col = df.columns[0]
    xls_separations = np.where(pd.isnull(df[first_col]))[0]
    sc_idxs = []
    # the next line avgs that we have exactly one step, because we would not
    # build df (and have results in the first place) if there was no step
    # Thus, if xls_sep. is empty (len=0) it avgs that no separations were
    # there, i.e., 1 SC
    if len(xls_separations) == 0:
        sc_idxs.append(range(0, len(df)))  # I can do this bc. only 1 SC
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
            # it refers to the start of a stepcycle & thus: possibly the last)
            if xls_separations[b] == xls_separations[-1]:
                sc_idxs.append(range(xls_separations[-1] + 1, len(df)))
    return sc_idxs


# %% ................  local functions #2 - run-level averages & stds  .................


def avg_and_std(dfs, folderinfo, cfg):
    """Compute the avgs & standard deviations for all columns of df"""

    # !!! NU - This function can be significantly optimised. I can initialise
    # colstoexclude, the avg/std dfs as a list of len=2, loop over them, and fix the
    # below NU.
    # => Keep this in mind but for now make sure it works for human data

    # unpack
    group_names = folderinfo["group_names"]
    results_dir = folderinfo["results_dir"]
    bin_num = cfg["bin_num"]
    save_to_xls = cfg["save_to_xls"]
    tracking_software = cfg["tracking_software"]
    if tracking_software in ["DLC", "SLEAP"]:
        analyse_average_x = cfg["analyse_average_x"]
    elif tracking_software == "Universal 3D":
        analyse_average_y = cfg["analyse_average_y"]

    # preparation, initialise avg/std dfs & colnames
    avg_dfs = [pd.DataFrame(data=None)] * len(group_names)
    std_dfs = [pd.DataFrame(data=None)] * len(group_names)

    # loop over all groups' dfs
    for g, group_name in enumerate(group_names):
        # extract this df and IDs
        if tracking_software in ["DLC", "SLEAP"]:
            cols_to_exclude = [ID_COL, "Run", "Stepcycle", "Flipped", "Time"]
            for col in dfs[g].columns:
                if col.endswith("likelihood"):
                    cols_to_exclude.append(col)
                if analyse_average_x is False:
                    if col.endswith(" x"):
                        cols_to_exclude.append(col)
        elif tracking_software == "Universal 3D":
            cols_to_exclude = [ID_COL, "Leg", "Stepcycle", "Time"]
            for col in dfs[g].columns:
                if col.endswith("X"):
                    cols_to_exclude.append(col)
                if analyse_average_y is False:
                    if col.endswith("Y"):
                        cols_to_exclude.append(col)
        this_df = dfs[g]
        IDs = pd.unique(this_df[ID_COL])
        IDs = IDs[~pd.isnull(IDs)]  # get rid of nan separator values
        # loop over all IDs, create an avg & std df for each, concat to groupdf
        for ID in IDs:
            # ID avg and std dfs
            this_ID_avg_df = pd.DataFrame(data=None)
            this_ID_std_df = pd.DataFrame(data=None)
            # indices of this IDs SCs
            this_idxs_list = np.where(this_df[ID_COL] == ID)[0]
            this_SC_idxs = idxs_list_to_list_of_SC_lists(this_idxs_list)
            SC_num = len(this_SC_idxs)
            # loop over all columns that are not ID, compute avg & std dfs
            # of current ID
            for c, col in enumerate(this_df.columns):
                if col not in cols_to_exclude:
                    this_data = np.zeros([len(this_SC_idxs[0]), SC_num])
                    for SC, SC_idx in enumerate(this_SC_idxs):
                        # NOTE - because SC_idx is a list of integers, iloc
                        #        includes all of the indices values. This is
                        #        different to e.g. cases of slicing or using
                        #        ranges. We can thus just forward and use
                        #        the indices found previously as they are in
                        #        the list!
                        this_data[:, SC] = this_df.iloc[SC_idx, c]
                    this_avg = np.mean(this_data, 1)
                    std = np.std(this_data, 1)
                    this_ID_avg_df[col] = this_avg
                    this_ID_std_df[col] = std
            # add ID col
            this_ID_avg_df[ID_COL] = ID
            this_ID_std_df[ID_COL] = ID
            # add SC number col
            this_ID_avg_df[SC_NUM_COL] = SC_num
            this_ID_std_df[SC_NUM_COL] = SC_num
            # SC Percentage column
            this_ID_avg_df[SC_PERCENTAGE_COL] = bin_num_to_percentages(bin_num)
            this_ID_std_df[SC_PERCENTAGE_COL] = bin_num_to_percentages(bin_num)
            # add ID-level avg & std dfs to group-level dfs
            if avg_dfs[g].empty:
                avg_dfs[g] = this_ID_avg_df
                std_dfs[g] = this_ID_std_df
            else:
                avg_dfs[g] = pd.concat([avg_dfs[g], this_ID_avg_df], axis=0)
                std_dfs[g] = pd.concat([std_dfs[g], this_ID_std_df], axis=0)

        # !!! NU - fix this:
        # I'm sure there are better ways of doing this, but we put in ID_COL
        # as first col like this.. Best practice would probably be to
        # initialise these dfs with that column but I'm using .empty above and
        # I also didn't want to introduce bin_num just for this
        first_cols = [ID_COL, SC_NUM_COL, SC_PERCENTAGE_COL]
        avg_dfs[g] = avg_dfs[g][
            first_cols + [c for c in avg_dfs[g].columns if c not in first_cols]
        ]
        std_dfs[g] = std_dfs[g][
            first_cols + [c for c in std_dfs[g].columns if c not in first_cols]
        ]
        # export sheets
        avg_filepath = os.path.join(
            results_dir, group_names[g] + " - " + AVG_GROUP_SHEET_NAME  # av SCs
        )
        save_results_sheet(avg_dfs[g], save_to_xls, avg_filepath)
        std_filepath = os.path.join(
            results_dir, group_names[g] + " - " + STD_GROUP_SHEET_NAME  # std SCs
        )
        save_results_sheet(std_dfs[g], save_to_xls, std_filepath)
    return avg_dfs, std_dfs


def idxs_list_to_list_of_SC_lists(idxs):
    """Convert all idxs that have this ID to a list of ranges with individual
    SC's values being separate entries in list
    """
    SC_idxs = []
    i = 0
    this_sc_idxs = []
    for i in range(1, len(idxs)):
        if idxs[i - 1] == (idxs[i] - 1):
            this_sc_idxs.append(idxs[i - 1])
        else:
            # if we have a SC change, add the -1 idx (last idx of prev SC),
            # then append & reset
            this_sc_idxs.append(idxs[i - 1])
            SC_idxs.append(this_sc_idxs)
            this_sc_idxs = []
        # special case: if i is last element (len-1), we in previous iteration
        #               did add i-1 but we have to make sure to add the last
        #               idx, too (since we can't loop until len+1)
        if i == (len(idxs) - 1):
            this_sc_idxs.append(idxs[i])
            SC_idxs.append(this_sc_idxs)
    return SC_idxs


# %% ..................  local functions #3 - grand averages & stds  ...................


def grand_avg_and_std(avg_dfs, folderinfo, cfg):
    """Compute the grand averages & standard deviations for all columns of df"""
    # unpack
    group_names = folderinfo["group_names"]
    results_dir = folderinfo["results_dir"]
    bin_num = cfg["bin_num"]
    save_to_xls = cfg["save_to_xls"]

    # preparation, initialise g_avg/std dfs
    g_avg_dfs = [pd.DataFrame(data=None)] * len(group_names)
    g_std_dfs = [pd.DataFrame(data=None)] * len(group_names)
    # loop over all groups' dfs
    for g, group_name in enumerate(group_names):
        # extract this df and IDs
        this_df = avg_dfs[g]
        IDs = np.unique(this_df[ID_COL])
        ID_num = len(IDs)  # also: for an "N" column later
        for c, col in enumerate(this_df.columns):
            if col != ID_COL:
                this_data = np.zeros([bin_num, ID_num])
                for i, ID in enumerate(IDs):
                    this_idxs = np.where(this_df[ID_COL] == ID)[0]
                    this_data[:, i] = this_df.iloc[this_idxs, c]
                # assign to grand av dfs
                g_avg_dfs[g][col] = np.mean(this_data, 1)
                g_std_dfs[g][col] = np.std(this_data, 1)
        # add the number of IDs that went into these grand averages and have
        # this be first column & add SC Percentage col and have it be 2nd col
        g_avg_dfs[g][N_COL] = ID_num  # N column
        g_std_dfs[g][N_COL] = ID_num
        # SC Percentage column
        g_avg_dfs[g][SC_PERCENTAGE_COL] = bin_num_to_percentages(bin_num)
        g_std_dfs[g][SC_PERCENTAGE_COL] = bin_num_to_percentages(bin_num)
        # reorder columns (N & SC% first)
        first_cols = [N_COL, SC_PERCENTAGE_COL]
        g_avg_dfs[g] = g_avg_dfs[g][
            first_cols + [c for c in g_avg_dfs[g].columns if c not in first_cols]
        ]
        g_std_dfs[g] = g_std_dfs[g][
            first_cols + [c for c in g_std_dfs[g].columns if c not in first_cols]
        ]
        # export sheets
        g_avg_filepath = os.path.join(
            results_dir, group_names[g] + " - " + G_AVG_GROUP_SHEET_NAME  # g_av SCs
        )
        save_results_sheet(g_avg_dfs[g], save_to_xls, g_avg_filepath)
        g_std_filepath = os.path.join(
            results_dir, group_names[g] + " - " + G_STD_GROUP_SHEET_NAME  # g_std SCs
        )
        save_results_sheet(g_std_dfs[g], save_to_xls, g_std_filepath)
    return g_avg_dfs, g_std_dfs


# %% .................  local functions #4 - load previous dataframes  .................
def load_previous_runs_dataframes(folderinfo, cfg):
    """If user asked for it load previous runs dataframes instead of generating them (i.e., avg_dfs, g_avg_dfs, g_std_dfs)"""
    avg_dfs = [[]] * len(folderinfo["group_names"])
    g_avg_dfs = [[]] * len(folderinfo["group_names"])
    g_std_dfs = [[]] * len(folderinfo["group_names"])
    for g, group_name in enumerate((folderinfo["group_names"])):
        try:
            avg_dfs[g] = pd.read_excel(
                os.path.join(
                    folderinfo["load_dir"],
                    group_name + " - " + AVG_GROUP_SHEET_NAME + ".xlsx",
                )
            )
            g_avg_dfs[g] = pd.read_excel(
                os.path.join(
                    folderinfo["load_dir"],
                    group_name + " - " + G_AVG_GROUP_SHEET_NAME + ".xlsx",
                )
            )
            g_std_dfs[g] = pd.read_excel(
                os.path.join(
                    folderinfo["load_dir"],
                    group_name + " - " + G_STD_GROUP_SHEET_NAME + ".xlsx",
                )
            )
        except FileNotFoundError:
            error_msg = (
                "\n******************\n! CRITICAL ERROR !\n******************\n"
                + f"Unable to load the data of group '{group_name}' from \n"
                + f"{folderinfo['load_dir']}"
                + "\n\nTry again!"
            )
            print(error_msg)
            write_issues_to_textfile(error_msg, folderinfo)
            raise FileNotFoundError
    # re-index avg_dfs based on unique SC Percentages
    array_of_idxs = np.arange(len(avg_dfs[0][SC_PERCENTAGE_COL].unique()))
    for g in range(len(avg_dfs)):
        repeat_index_this_often = len(avg_dfs[g]) // len(array_of_idxs)
        new_idx = np.tile(array_of_idxs, repeat_index_this_often)
        avg_dfs[g] = avg_dfs[g].set_index(new_idx)
    # check if PCA & stats variables are present in all dataframes
    for g, group_name in enumerate(folderinfo["group_names"]):
        check_PCA_and_stats_variables(
            avg_dfs[g], group_name, "Average", folderinfo, cfg
        )
        check_PCA_and_stats_variables(
            g_avg_dfs[g], group_name, "Grand Average", folderinfo, cfg
        )
        check_PCA_and_stats_variables(
            g_std_dfs[g], group_name, "Grand Standard Deviation", folderinfo, cfg
        )
    # since import_data writes bin_num (running a sanity check before) we have to do
    # it here too. No need to run the sanity check again since that was done previously
    cfg["bin_num"] = len(np.unique(avg_dfs[0][SC_PERCENTAGE_COL]))
    if cfg["bin_num"] * len(np.unique(avg_dfs[0][ID_COL])) != len(avg_dfs[0]):
        error_msg = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "Something is wrong with your IDs and SC Percentage columns."
            + "\nThere seem to be duplicates. Make sure that this is not the case."
            + "\nOtherwise, run it again without loading your previous run's results."
        )
        print(error_msg)
        write_issues_to_textfile(error_msg, folderinfo)
        raise ValueError(error_msg)
    else:
        return avg_dfs, g_avg_dfs, g_std_dfs, cfg

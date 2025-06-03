# %% imports
from autogaita.resources.utils import write_issues_to_textfile
import os
import pandas as pd
import numpy as np

# %% constants
from autogaita.universal3D.universal3D_constants import (
    TIME_COL,
    LEGS,
    SCXLS_SUBJCOLS,
    SCXLS_LEGCOLS,
    SCXLS_RUNCOLS,
    SCXLS_SCCOLS,
    SWINGSTART_COL,
    STANCEEND_COL,
)


# %% workflow step #2 - SC extraction (reading user-provided SC Table)


# ...............................  outer function  .....................................
def extract_stepcycles(data, info, folderinfo, cfg):
    """Read XLS file with SC annotations, find correct row & return all_cycles"""
    # unpack
    root_dir = folderinfo["root_dir"]
    sctable_filename = folderinfo["sctable_filename"]

    # load the table - try some filename & ending options
    if os.path.exists(os.path.join(root_dir, sctable_filename)):
        SCdf_full_filename = os.path.join(root_dir, sctable_filename)
    elif os.path.exists(os.path.join(root_dir, sctable_filename) + ".xlsx"):
        SCdf_full_filename = os.path.join(root_dir, sctable_filename) + ".xlsx"
    elif os.path.exists(os.path.join(root_dir, sctable_filename) + ".xls"):
        SCdf_full_filename = os.path.join(root_dir, sctable_filename) + ".xls"
    else:
        no_sc_table_message = (
            "No Annotation Table found! sctable_filename has to be @ root_dir"
        )
        raise FileNotFoundError(no_sc_table_message)
    # check if we need to specify engine (required for xlsx)
    try:
        SCdf = pd.read_excel(SCdf_full_filename)
    except:
        SCdf = pd.read_excel(SCdf_full_filename, engine="openpyxl")

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
    SCdf[header_columns[0]] = SCdf[header_columns[0]].astype(str)  # ensure no ints!
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
    while isinstance(SCdf.iloc[end_row, run_col].values[0], int) & (
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
                if not np.isnan(SCdf[column][run_row].values[0]):
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
        # check that none of the joints used for angles have the same value within SCs
        # => FOR FUTURE SELF: THIS CAN RETURN NONE TOO! CONSIDER WHEN ADDING
        #    ANOTHER CHECK!
        all_cycles = check_different_angle_joint_coords(all_cycles, data, info, cfg)
        # NOTE for future self
        # => If you are considering to remove empty lists from run_cycles note that we
        #    need them for the case of Runs 1 & 3 having SCs but 2 not having any
        # => Otherwise SC-level plots arent plotted correctly (ie Run3 could easily
        #    look like Run2 - we need an empty subplot panel for run2 and thus an empty
        #    list!)
        # MoVi Check
        if (
            all_cycles and legname == "right"
        ):  # because with MoVi we only analyse "right" leg
            all_cycles = check_movi_tracking(all_cycles, data, info)
    return all_cycles


def check_movi_tracking(all_cycles, data, info):
    """For MoVi Data, check if there are tracking failures (i.e. consecutive zeros in a column)"""

    # unpack
    name = info["name"]
    # text file to save stuff
    behaviour_name = info["results_dir"].split("/")[-2]
    info_txt_path = info["results_dir"].split("Subject")[0]
    info_txt_name = behaviour_name + " - Broken MoVi Tracking.txt"

    # initialise clean_cycles and loop over SCs
    clean_cycles = None
    for r, run_cycles in enumerate(all_cycles):
        for c, cycle in enumerate(run_cycles):
            exclude_cycle = False
            # check if we have any zeros in the data
            this_data = data.loc[cycle[0] : cycle[1], :]
            zero_idxs = np.argwhere(this_data == 0)
            # zero idxs is a list of lists with each list being the row/col idxs of the
            # zero
            # => can be accessed with iloc
            for zero_idx in zero_idxs:
                # tracking failure: the zero-col's previous or next index is also zero
                try:
                    previous_rows_value = this_data.iloc[zero_idx[0] - 1, zero_idx[1]]
                except:
                    # i.e., no previous row - some number so code doesn't break
                    previous_rows_value = 999
                try:
                    next_rows_value = this_data.iloc[zero_idx[0] + 1, zero_idx[1]]
                except:
                    next_rows_value = 999  # i.e., no next row
                if previous_rows_value == 0 or next_rows_value == 0:
                    exclude_cycle = True
            if exclude_cycle:
                message = f"\nID {name} - Run #{r + 1} - SC #{c + 1}"
                with open(os.path.join(info_txt_path, info_txt_name), "a") as f:
                    f.write(message)
            else:
                if clean_cycles is None:  # if first valid cycle: list of empty lists
                    clean_cycles = [[] for s in range(len(all_cycles))]
                clean_cycles[r].append(cycle)
    return clean_cycles


def check_different_angle_joint_coords(all_cycles, data, info, cfg):
    """Check if none of the joints used for angle computations later have equal values (since this would lead to math.domain errors due to floating point precision)"""

    # Note 1
    # ------
    # In theory, I could fix this programatically in the add_angle function, but I feel
    # like joint-coords should not often be exactly equal like this in a meaningful way
    # We can still change it in the future.

    # Note 2
    # ------
    # It is important that I loop over legs, because I have to ensure that angle-joints
    # are different for each leg separately - even though the SC is just w.r.t. one leg,
    # both legs' angles are computed later (and would lead to an error if equal)

    # unpack
    angles = cfg["angles"]

    clean_cycles = None
    for r, run_cycles in enumerate(all_cycles):
        for c, cycle in enumerate(run_cycles):
            cycle = check_a_single_cycle_for_joint_coords(
                cycle, angles, data, r, c, info
            )
            if cycle:  # if cycle was not valid (equal-joint-coords) this returns None
                if clean_cycles is None:  # if first valid cycle: list of empty lists
                    clean_cycles = [[] for s in range(len(all_cycles))]
                clean_cycles[r].append(cycle)
    return clean_cycles


def check_a_single_cycle_for_joint_coords(cycle, angles, data, r, c, info):
    """This checks a single cycle: across both legs and all angle configs. Removing the cycle if we had equal joint-coords anywhere!"""
    for legname in LEGS:  # loop over legs
        for a in range(len(angles["name"])):  # loop over different angle configs
            # first, prepare a dict that has only the data of this leg/angle combo
            this_angle_data = {"name": [], "lower_joint": [], "upper_joint": []}
            for key in this_angle_data.keys():
                this_joint = angles[key][a]
                if this_joint + "Y" in data.columns:
                    this_angle_data[key] = np.array(
                        [data[this_joint + "Y"], data[this_joint + "Z"]]
                    )
                else:  # we know that this joint is in data (because of a check in prep)
                    this_angle_data[key] = np.array(
                        [
                            data[this_joint + ", " + legname + " Y"],
                            data[this_joint + ", " + legname + " Z"],
                        ]
                    )
            # now check if any of the joints have the same coord at any idx
            for idx in range(cycle[0], cycle[1] + 1):  # within this SC only
                if (
                    np.array_equal(
                        this_angle_data["name"][:, idx],
                        this_angle_data["lower_joint"][:, idx],
                    )
                    or np.array_equal(
                        this_angle_data["name"][:, idx],
                        this_angle_data["upper_joint"][:, idx],
                    )
                    or np.array_equal(
                        this_angle_data["lower_joint"][:, idx],
                        this_angle_data["upper_joint"][:, idx],
                    )
                ):
                    this_message = (
                        "\n***********\n! WARNING !\n***********\n"
                        + f"Run #{r + 1} - SC #{c + 1} has equal {legname.upper()} "
                        + "joint coordinates at "
                        + f"{round(data[TIME_COL][idx],4)}s:"
                        + "\n\nAngle - [Y Z]:\n"
                        + angles["name"][a]
                        + " - "
                        + str(this_angle_data["name"][:, idx])
                        + "\nLower joint: "
                        + angles["lower_joint"][a]
                        + " - "
                        + str(this_angle_data["lower_joint"][:, idx])
                        + "\nUpper joint: "
                        + angles["upper_joint"][a]
                        + " - "
                        + str(this_angle_data["upper_joint"][:, idx])
                        + "\nRemoving the SC from "
                        + f"{round(data[TIME_COL][cycle[0]], 4)}-"
                        + f"{round(data[TIME_COL][cycle[1]], 4)}s"
                    )
                    print(this_message)
                    write_issues_to_textfile(this_message, info)
                    return None  # removes this SC
    return cycle  # if we never returned None, this SC is valid


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
    if isinstance(all_cycles["left"], list) and isinstance(all_cycles["right"], list):
        return all_cycles
    # case 2 - no valid SCs for left leg
    elif (all_cycles["left"] is None) and isinstance(all_cycles["right"], list):
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
    elif isinstance(all_cycles["left"], list) and (all_cycles["right"] is None):
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
    elif (all_cycles["left"] is None) & (all_cycles["right"] is None):
        this_message = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "\nID: "
            + name
            + "\nSkipped because no valid SCs found for any leg!"
        )
        print(this_message)
        write_issues_to_textfile(this_message, info)
        return  # in this case, abort everything (returns None to main)

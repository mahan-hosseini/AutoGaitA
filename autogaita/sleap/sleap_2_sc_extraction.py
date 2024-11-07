# %% imports
from autogaita.gaita_res.utils import write_issues_to_textfile
from autogaita.core2D.core2D_sc_extraction_utils import (
    check_cycle_out_of_bounds,
    check_cycle_duplicates,
    check_cycle_order,
    check_tracking,
    handle_issues,
)
import os
import pandas as pd
import numpy as np

# %% constants
from autogaita.core2D.core2D_constants import (
    SCXLS_MOUSECOLS,
    SCXLS_SCCOLS,
    SWINGSTART_COL,
    STANCEEND_COL,
)

# %% workflow step #2 - SC extraction (reading user-provided SC Table)


def extract_stepcycles(data, info, folderinfo, cfg):
    """Read XLS file with SC annotations, find correct row & return all_cycles"""

    # ...............................  preparation  ....................................
    # unpack
    name = info["name"]
    root_dir = folderinfo["root_dir"]
    sctable_filename = folderinfo["sctable_filename"]
    sampling_rate = cfg["sampling_rate"]

    # check if excel file is .xlsx or .xls, if none found try to fix it
    if (".xls" in sctable_filename) | (".xlsx" in sctable_filename):
        if os.path.exists(os.path.join(root_dir, sctable_filename)):
            SCdf = pd.read_excel(os.path.join(root_dir, sctable_filename))
        else:
            raise FileNotFoundError(
                "No Annotation Table found! sctable_filename has to be @ root_dir"
            )
    else:
        # in cases below use string-concat (+) - otherwise xls added as path
        if os.path.exists(os.path.join(root_dir, sctable_filename + ".xls")):
            SCdf = pd.read_excel(os.path.join(root_dir, sctable_filename + ".xls"))
        elif os.path.exists(os.path.join(root_dir, sctable_filename + ".xlsx")):
            SCdf = pd.read_excel(os.path.join(root_dir, sctable_filename + ".xlsx"))
        else:
            raise FileNotFoundError(
                "No Annotation Table found! sctable_filename has to be @ root_dir"
            )
    # see if table columns are labelled correctly (try a couple to allow user typos)
    valid_col_flags = [False, False]
    header_columns = ["", ""]
    for h, header in enumerate([SCXLS_MOUSECOLS, SCXLS_SCCOLS]):
        for header_col in header:
            if header_col in SCdf.columns:
                valid_col_flags[h] = True
                header_columns[h] = header_col
                break
    if not all(valid_col_flags):
        handle_issues("wrong_scxls_colnames", info)
        return
    # find our info columns & rows
    mouse_col = SCdf.columns.get_loc(header_columns[0])  # INDEXING! (see list above)
    sc_col = SCdf.columns.get_loc(header_columns[1])
    SCdf[header_columns[0]] = SCdf[header_columns[0]].astype(str)
    mouse_row = SCdf.index[SCdf[header_columns[0]] == name]  # find this mouse
    # this mouse was not included in sc xls
    if len(mouse_row) == 0:
        handle_issues("no_mouse", info)
        return
    # this mouse was included more than once
    if len(mouse_row) > 1:
        handle_issues("double_mouse", info)
        return

    # next_mouse_idx = mouse_row  # search idx of first row of next mouse

    # ..............................  main xls read  ...................................
    sc_num = 0
    for column in SCdf.columns:
        if STANCEEND_COL in column:
            if np.isnan(SCdf[column][mouse_row].values[0]) == False:
                sc_num += 1
    if sc_num == 0:
        handle_issues("no_scs", info)
        return
    user_scnum = SCdf.iloc[mouse_row, sc_col].values[0]  # sanity check input
    if user_scnum != sc_num:  # warn the user, take the values we found
        this_message = (
            "\n***********\n! WARNING !\n***********\n"
            + "Mismatch between stepcycle number of SC Number column & "
            + "entries in swing/stance latency columns!"
            + "\nUsing all valid swing/stance entries."
        )
        print(this_message)
        write_issues_to_textfile(this_message, info)

    # ...........................  idxs to all_cycles  .................................
    # use value we found, loop over all runs, throw all scs into all_cycles
    all_cycles = [[None, None] for s in range(sc_num)]  # fill :sc_num x 2 list
    for s in range(sc_num):
        if s == 0:
            start_col = SCdf.columns.get_loc(SWINGSTART_COL)
            end_col = SCdf.columns.get_loc(STANCEEND_COL)
        else:
            # str(s) because colnames match s for s>0!
            start_col = SCdf.columns.get_loc(SWINGSTART_COL + "." + str(s))
            end_col = SCdf.columns.get_loc(STANCEEND_COL + "." + str(s))
        user_scnum += 1
        # extract the SC times
        start_in_s = float(SCdf.iloc[mouse_row, start_col].values[0])
        end_in_s = float(SCdf.iloc[mouse_row, end_col].values[0])
        # see if we are rounding to fix inaccurate user input
        # => account for python's float precision leading to inaccuracies
        # => two important steps here (sanity_check_vals only used for these checks)
        # 1. round to 10th decimal to fix python making
        #    3211.999999999999999995 out of 3212
        sanity_check_start = round(start_in_s * sampling_rate, 10)
        sanity_check_end = round(end_in_s * sampling_rate, 10)
        # 2. comparing abs(sanity check vals) to 1e-7 just to be 1000% sure
        if (abs(sanity_check_start % 1) > 1e-7) | (abs(sanity_check_end % 1) > 1e-7):
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
        all_cycles[s][0] = int(start_in_s * sampling_rate)
        all_cycles[s][1] = int(end_in_s * sampling_rate)
        # check if we are in data-bounds
        if (all_cycles[s][0] in data.index) & (all_cycles[s][1] in data.index):
            pass
        else:
            all_cycles[s] = [None, None]  # so they can be cleaned later
            this_message = (
                "\n***********\n! WARNING !\n***********\n"
                + "SC latencies of: "
                + str(start_in_s)
                + "s to "
                + str(end_in_s)
                + "s not in data/video range!"
                + "\nSkipping!"
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
        all_cycles = check_cycle_order(all_cycles, info)
        # check if tracking broke for any SCs - if so remove them
        all_cycles = check_tracking(data, info, all_cycles, cfg)
    return all_cycles

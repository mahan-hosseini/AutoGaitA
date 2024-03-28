# ...................................  imports  ........................................
from autogaita import autogaita_dlc, autogaita_simi
import pandas as pd
import numpy as np
import os
import traceback


# ...............................  global constants  ...................................
ISSUES_TXT_FILENAME = "Issues.txt"


# ...............................  error handling  .....................................
def try_to_run_gaita(
    which_gaita, info, folderinfo, cfg, multirun_flag
):
    """Try to run AutoGaitA for a single dataset - print and log error if there was any
    error that prevented completion of the main code

    Note
    ----
    Needs to know "which gaita" (DLC or Simi) should be run and if "this run" is part
    of a call to one of our multiruns!
    """
    # print info
    message = (
        "\n\n\n*********************************************"
        + "\n*                  "
        + info["name"]
        + "                     *"
        + "\n*********************************************"
    )
    print(message)
    try:
        if which_gaita == "DLC":
            autogaita_dlc.dlc(info, folderinfo, cfg)
        elif which_gaita == "Simi":
            autogaita_simi.simi(info, folderinfo, cfg)
        else:
            print("which_gaita has to be DLC or Simi - try again.")
    # catch these errors (don't catch all possbile errors - bad practice!)
    except (
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        FileNotFoundError,
        IOError,
        OSError,
        PermissionError,
        MemoryError,
        OverflowError,
        FloatingPointError,
        pd.errors.ParserError,
        pd.errors.DtypeWarning,
        np.linalg.LinAlgError,
    ):
        error_traceback = traceback.format_exc()  # capture traceback of error
        # modify and print message
        skip_message = (
            "* ! ! ! ! ! ! ATTENTION  PLEASE ! ! ! ! ! ! *"
            + "\n* Whoopsie - Something unexpected is wrong! *"
            + "\n* See below & check Issues.txt for details. *"
        )
        if multirun_flag:
            skip_message += (
                "\n*   We'll continue with the next dataset!   *"
                + "\n\n*********************************************"
                + "\n*               Error Details               *"
                + "\n*********************************************"
                + f"\n{error_traceback}"
            )
        else:
            skip_message += (
                "\n\n*********************************************"
                + "\n*               Error Details               *"
                + "\n*********************************************\n"
                + f"\n{error_traceback}"
            )
        print(skip_message)
        # store message
        if not os.path.exists(info["results_dir"]):
            os.makedirs(info["results_dir"])
        textfile = os.path.join(info["results_dir"], ISSUES_TXT_FILENAME)
        with open(textfile, "a") as f:
            f.write(skip_message)
    return

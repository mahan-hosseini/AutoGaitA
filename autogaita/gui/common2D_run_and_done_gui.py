# %%..........  LOCAL FUNCTION(S) #3 - BUILD RUN AND DONE WINDOWS .............
from autogaita.gui.common2D_gui_utils import (
    get_results_and_cfg,
    runanalysis,
)
from autogaita.gui.first_level_gui_utils import (
    update_config_file,
    extract_results_from_json_file,
)
import autogaita.gui.gui_utils as gui_utils
import autogaita.gui.gaita_widgets as gaita_widgets
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from customtkinter import CTkImage
import os
from autogaita.gui.gui_utils import create_folder_icon


def build_run_and_done_windows(
    tracking_software,
    analysis,
    root,
    cfg,
    widget_cfg,
    gui_specific_vars,
    root_dimensions,
):
    """The run window, get information, pass information & run."""
    # unpack root window dimensions & widget cfg
    widget_cfg = widget_cfg
    FG_COLOR = widget_cfg["FG_COLOR"]
    HOVER_COLOR = widget_cfg["HOVER_COLOR"]
    HEADER_FONT_NAME = widget_cfg["HEADER_FONT_NAME"]
    MAIN_HEADER_FONT_SIZE = widget_cfg["MAIN_HEADER_FONT_SIZE"]
    TEXT_FONT_NAME = widget_cfg["TEXT_FONT_NAME"]
    ADV_CFG_TEXT_FONT_SIZE = widget_cfg["ADV_CFG_TEXT_FONT_SIZE"]

    w = root_dimensions[0]
    h = root_dimensions[1]

    # .............................  run window  ..............................
    # ghost_root = ctk.CTk()
    # ghost_root.withdraw()
    # root = ctk.CTkToplevel()
    runwindow = ctk.CTkToplevel(root)
    user_ready = tk.IntVar(runwindow, 0)  # used to know when user is ready 4 screen 3
    if analysis == "single":
        runwindow.title("Single GaitA")
    else:
        runwindow.title("Batch GaitA")
    runwindow.geometry(f"{int(w / 2)}x{h}+{int(w / 4)}+0")
    gui_utils.fix_window_after_its_creation(runwindow)
    # fill window with required info labels & entries - then get results
    results = populate_run_window(
        analysis,
        runwindow,
        cfg,
        widget_cfg,
        gui_specific_vars,
        user_ready,
    )

    # IMPORTANT NOTE
    # --------------
    # we have a wait_variable (user_ready) in populate_run_window waiting for user being
    # ready before results are returned and everything below this line will be executed
    # when calling populate_run_window
    # => the scope of that IntVar has to be runwindow (see initialisation line above)
    #    otherwise things won't work when we call _dlc_gui from autogaita.py
    runwindow.destroy()

    # .........................................................................
    # .............. IMPORTANT - GET VARS & CHECK USER-INPUT ..................
    # .........................................................................
    # ==> Extract "this" results & cfg info IMMEDIATELY BEFORE running analysis
    #     (i.e., before providing donewindow)
    # ==> get_results_and_cfg checks whether the numerical vars (see
    #     FLOAT_/INT_VARS) were numbers - if not it returns an error_msg, which
    #     we use to inform users about their wrong input
    #       -- Catch this here and don't even show donewindow if input is wrong
    # ==> NEVER, EVER change the global variable cfg!
    try:
        this_runs_results, this_runs_cfg = get_results_and_cfg(
            results, cfg, analysis, gui_specific_vars
        )
    except:
        error_msg = get_results_and_cfg(results, cfg, analysis, gui_specific_vars)
        tk.messagebox.showerror(title="Try again", message=error_msg)
        return

    # .............................  done window  .............................
    donewindow = ctk.CTkToplevel(root)
    donewindow.title("GaitA Ready :)")
    donewindow_w = w * (3 / 5)
    donewindow_h = h * (1 / 5)
    donewindow_x = (w - donewindow_w) // 2
    donewindow_y = h * (1 / 2.5)
    donewindow.geometry(
        "%dx%d+%d+%d" % (donewindow_w, donewindow_h, donewindow_x, donewindow_y)
    )
    gui_utils.fix_window_after_its_creation(donewindow)

    # labels
    done_label1_string = "Your results will be saved as your data is processed"
    done_label1 = ctk.CTkLabel(
        donewindow,
        text=done_label1_string,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    done_label1.grid(row=0, column=0, sticky="nsew")
    done_label2_string = (
        "Please see the Python command window for progress "
        + "and the figure panel for an overview of all plots."
    )
    done_label2 = ctk.CTkLabel(
        donewindow,
        text=done_label2_string,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    done_label2.grid(row=1, column=0, sticky="nsew")
    done_label3_string = (
        "You may start another analysis while we are "
        + "processing - however your PC might slow down a bit. "
    )
    done_label3 = ctk.CTkLabel(
        donewindow,
        text=done_label3_string,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    done_label3.grid(row=2, column=0, sticky="nsew")
    done_label4_string = (
        "Thank you for using AutoGaitA! Feel free to "
        + "contact me on Github or at autogaita@fz-juelich.de - MH."
    )
    done_label4 = ctk.CTkLabel(
        donewindow,
        text=done_label4_string,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    done_label4.grid(row=3, column=0, sticky="nsew")
    # run button
    done_button = ctk.CTkButton(
        donewindow,
        text="Run!",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        font=(HEADER_FONT_NAME, MAIN_HEADER_FONT_SIZE),
        command=lambda: (
            runanalysis(tracking_software, analysis, this_runs_results, this_runs_cfg),
            donewindow.destroy(),
        ),
    )
    done_button.grid(row=4, column=0, sticky="nsew", pady=10, padx=200)

    gui_utils.maximise_widgets(donewindow)


# %%..........  LOCAL FUNCTION(S) #4 - POPULATE RUN WINDOW ....................
def populate_run_window(
    analysis,
    runwindow,
    cfg,
    widget_cfg,
    gui_specific_vars,
    user_ready,
):
    """Populate the information window before running analysis"""

    # unpack widget cfg
    FG_COLOR = widget_cfg["FG_COLOR"]
    HOVER_COLOR = widget_cfg["HOVER_COLOR"]
    TEXT_FONT_NAME = widget_cfg["TEXT_FONT_NAME"]
    TEXT_FONT_SIZE = widget_cfg["TEXT_FONT_SIZE"]
    ADV_CFG_TEXT_FONT_SIZE = widget_cfg["ADV_CFG_TEXT_FONT_SIZE"]
    HEADER_FONT_NAME = widget_cfg["HEADER_FONT_NAME"]
    HEADER_FONT_SIZE = widget_cfg["MAIN_HEADER_FONT_SIZE"]
    AUTOGAITA_FOLDER_PATH = widget_cfg["AUTOGAITA_FOLDER_PATH"]
    # unpack variable dict
    CONFIG_FILE_NAME = gui_specific_vars["CONFIG_FILE_NAME"]
    LIST_VARS = gui_specific_vars["LIST_VARS"]
    DICT_VARS = gui_specific_vars["DICT_VARS"]
    TK_STR_VARS = gui_specific_vars["TK_STR_VARS"]
    TK_BOOL_VARS = gui_specific_vars["TK_BOOL_VARS"]

    # ..................... load results dict from config.....................
    # use the values in the config json file for the results dictionary
    results = extract_results_from_json_file(
        runwindow, AUTOGAITA_FOLDER_PATH, CONFIG_FILE_NAME, TK_STR_VARS, TK_BOOL_VARS
    )

    # ........................  build the frame  ...............................
    if analysis == "single":
        # mouse number
        mousenum_label, mousenum_entry = gaita_widgets.label_and_entry_pair(
            runwindow,
            "What is the number of the animal/subject?",
            results["mouse_num"],
            widget_cfg,
            adv_cfg_textsize=True,
        )
        mousenum_label.grid(row=0, column=0)
        mousenum_entry.grid(row=1, column=0)
        # run number
        runnum_label, runnum_entry = gaita_widgets.label_and_entry_pair(
            runwindow,
            "What is the number of the trial?",
            results["run_num"],
            widget_cfg,
            adv_cfg_textsize=True,
        )
        runnum_label.grid(row=2, column=0)
        runnum_entry.grid(row=3, column=0)
        # set row index accordingly
        r = 4
    else:
        r = 0

    # root directory
    root_dir_label = ctk.CTkLabel(
        runwindow,
        text="Directory containing the files to be analysed:",
        font=(widget_cfg["TEXT_FONT_NAME"], widget_cfg["ADV_CFG_TEXT_FONT_SIZE"]),
    )
    root_dir_label.grid(row=r, column=0)
    root_dir_browse = gaita_widgets.make_browse(
        parent_window=runwindow,
        row=r + 1,
        column=0,
        var_key="root_dir",
        var_dict=results,
        widget_cfg=widget_cfg,
        pady=5,
    )
    # stepcycle latency XLS
    SCXLS_label = ctk.CTkLabel(
        runwindow,
        text="Annotation Table Excel file:",
        font=(widget_cfg["TEXT_FONT_NAME"], widget_cfg["ADV_CFG_TEXT_FONT_SIZE"]),
    )
    SCXLS_label.grid(row=r + 2, column=0)
    SCXLS_browse = gaita_widgets.make_browse(
        parent_window=runwindow,
        row=r + 3,
        column=0,
        var_key="sctable_filename",
        var_dict=results,
        widget_cfg=widget_cfg,
        pady=5,
        is_file=True,
        initial_dir=root_dir_browse.get,
    )

    # empty label 1 (for spacing)
    empty_label_one = ctk.CTkLabel(runwindow, text="")
    empty_label_one.grid(row=r + 4, column=0)
    # .......................  file-identifier information  ............................
    # file naming convention label one
    name_convention_string_one = (
        "According to the [A]_[B]_[C]_[D]-[E][G] filename convention "
    )
    name_convention_label_one = ctk.CTkLabel(
        runwindow,
        text=name_convention_string_one,
        font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
    )
    name_convention_label_one.grid(row=r + 5, column=0)
    # file naming convention label two
    name_convention_string_two = "(e.g. C57B6_Mouse10_25mm_Run1-6DLC-JointTracking):"
    name_convention_label_two = ctk.CTkLabel(
        runwindow,
        text=name_convention_string_two,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    name_convention_label_two.grid(row=r + 6, column=0)
    # empty label 2 (for spacing)
    empty_label_two = ctk.CTkLabel(runwindow, text="")
    empty_label_two.grid(row=r + 7, column=0)
    # data string
    data_label, data_entry = gaita_widgets.label_and_entry_pair(
        runwindow,
        "[G] What is the identifier of the tracked coordinate file?",
        results["data_string"],
        widget_cfg,
        adv_cfg_textsize=True,
    )
    data_label.grid(row=r + 8, column=0)
    data_entry.grid(row=r + 9, column=0)
    # beam string
    beam_label, beam_entry = gaita_widgets.label_and_entry_pair(
        runwindow,
        "[G] What is the identifier of the tracked baseline file? (optional)",
        results["beam_string"],
        widget_cfg,
        adv_cfg_textsize=True,
    )
    beam_label.grid(row=r + 10, column=0)
    beam_entry.grid(row=r + 11, column=0)
    # premouse_num string
    premouse_label, premouse_entry = gaita_widgets.label_and_entry_pair(
        runwindow,
        "[B] Define the 'unique subject identifier' preceding the number",
        results["premouse_string"],
        widget_cfg,
        adv_cfg_textsize=True,
    )
    premouse_label.grid(row=r + 12, column=0)
    premouse_entry.grid(row=r + 13, column=0)
    # postmouse_num string
    postmouse_label, postmouse_entry = gaita_widgets.label_and_entry_pair(
        runwindow,
        "[C] Define the 'unique task identifier",
        results["postmouse_string"],
        widget_cfg,
        adv_cfg_textsize=True,
    )
    postmouse_label.grid(row=r + 14, column=0)
    postmouse_entry.grid(row=r + 15, column=0)
    # prerun string
    prerun_label, prerun_entry = gaita_widgets.label_and_entry_pair(
        runwindow,
        "[D] Define the 'unique trial identifier",
        results["prerun_string"],
        widget_cfg,
        adv_cfg_textsize=True,
    )
    prerun_label.grid(row=r + 16, column=0)
    prerun_entry.grid(row=r + 17, column=0)
    # postrun string
    postrun_label, postrun_entry = gaita_widgets.label_and_entry_pair(
        runwindow,
        "[E] Define the 'unique camera identifier",
        results["postrun_string"],
        widget_cfg,
        adv_cfg_textsize=True,
    )
    postrun_label.grid(row=r + 18, column=0)
    postrun_entry.grid(row=r + 19, column=0)
    # button confirming being done
    # => change value of user_ready in this call
    finishbutton = ctk.CTkButton(
        runwindow,
        text="I am done, pass the info!",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: (
            update_config_file(
                results,
                cfg,
                AUTOGAITA_FOLDER_PATH,
                CONFIG_FILE_NAME,
                LIST_VARS,
                DICT_VARS,
                TK_STR_VARS,
                TK_BOOL_VARS,
            ),
            user_ready.set(1),
        ),
    )
    finishbutton_row = r + 20
    finishbutton.grid(
        row=finishbutton_row, column=0, rowspan=2, sticky="nsew", pady=5, padx=70
    )
    # maximise widgets
    gui_utils.maximise_widgets(runwindow)
    # wait until user is ready before returning
    runwindow.wait_variable(user_ready)
    return results

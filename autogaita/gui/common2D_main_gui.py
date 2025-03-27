# %% imports
import autogaita.gui.gaita_widgets as gaita_widgets
import autogaita.gui.gui_utils as gui_utils
from autogaita.gui.common2D_columninfo_gui import build_column_info_window
from autogaita.gui.common2D_advanced_config_gui import build_cfg_window
from autogaita.gui.common2D_run_and_done_gui import build_run_and_done_windows
from autogaita.gui.first_level_gui_utils import (
    update_config_file,
    extract_cfg_from_json_file,
)

import tkinter as tk
import customtkinter as ctk
import os
import platform

# %% global constants
from autogaita.gui.gui_constants import (
    DLC_FG_COLOR,
    DLC_HOVER_COLOR,
    SLEAP_FG_COLOR,
    SLEAP_HOVER_COLOR,
    TEXT_FONT_NAME,
    TEXT_FONT_SIZE,
    WINDOWS_TASKBAR_MAXHEIGHT,
    AUTOGAITA_FOLDER_PATH,
    get_widget_cfg_dict,  # function!
)

# gaita's cfg-dict related constants
from autogaita.gui.common2D_gui_constants import (
    FLOAT_VARS,
    INT_VARS,
    LIST_VARS,
    DICT_VARS,
    TK_BOOL_VARS,
    TK_STR_VARS,
    GUI_SPECIFIC_VARS,
)

# %% An important Note
# I am using a global variable called cfg because I need its info to be shared
# between root and advanced_cfg windows. This is not the object-oriented way
# that one would do this typically. However, it works as expected since:
# 1) cfg's values are only ever modified except @ initialisation & by widgets
# 2) cfg's values are shared for analysis of a single and multiple video(s)
# 3) cfg's values are passed to all functions that need them
# 4) and (IMPORTANTLY!) just before running either (i.e. single/multi) analysis, cfg's
#    and result's values are unpacked and assigned to "this_" dicts that are passed
#    to the runanalysis local function. Hence, from that point onwards, only
#    "this_" dicts are used, never cfg or result dicts themselves.
#    ==> see donewindow for point 4)

# %%............................  MAIN PROGRAM ................................


def run_common2D_gui(tracking_software):

    # .................................  IMPORTANT  ...........................
    # => This part depends on tracking_software (and later in run and done
    #    window)
    WIDGET_CFG = get_widget_cfg_dict()
    if tracking_software == "DLC":
        WIDGET_CFG["FG_COLOR"] = DLC_FG_COLOR
        WIDGET_CFG["HOVER_COLOR"] = DLC_HOVER_COLOR
        CONFIG_FILE_NAME = "dlc_gui_config.json"
    elif tracking_software == "SLEAP":
        WIDGET_CFG["FG_COLOR"] = SLEAP_FG_COLOR
        WIDGET_CFG["HOVER_COLOR"] = SLEAP_HOVER_COLOR
        CONFIG_FILE_NAME = "sleap_gui_config.json"
    GUI_SPECIFIC_VARS["CONFIG_FILE_NAME"] = CONFIG_FILE_NAME

    # ..........................................................................
    # ......................  root window initialisation .......................
    # ..........................................................................
    # Check for config file
    config_file_path = os.path.join(AUTOGAITA_FOLDER_PATH, CONFIG_FILE_NAME)
    if not os.path.isfile(config_file_path):
        config_file_error_msg = (
            f"{CONFIG_FILE_NAME} file not found in autogaita folder.\n"
            "Confirm that the file exists and is named correctly.\n"
            "If not, download it again from the GitHub repository."
        )
        tk.messagebox.showerror(
            title="Config File Error", message=config_file_error_msg
        )
        exit()

    # CustomTkinter vars
    ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
    ctk.set_default_color_theme("green")  # Themes: blue , dark-blue, green
    # root
    root = ctk.CTk()
    # make window pretty
    screen_width = root.winfo_screenwidth()  # width of the screen
    screen_height = root.winfo_screenheight()  # height of the screen
    if platform.system() == "Windows":  # adjust for taskbar in windows only
        screen_height -= WINDOWS_TASKBAR_MAXHEIGHT
    # create root dimensions (based on fullscreen) to pass to other window-functions l8r
    w, h, x, y = screen_width, screen_height, 0, 0
    root_dimensions = (w, h, x, y)
    # set the dimensions of the screen and where it is placed
    # => have it half-wide starting at 1/4 of screen's width (dont change w & x!)
    root.geometry(f"{int(screen_width / 2)}x{screen_height}+{int(screen_width / 4)}+0")
    root.title(f"{tracking_software} GaitA")
    gui_utils.fix_window_after_its_creation(root)
    gui_utils.configure_the_icon(root)

    # .....................  load cfg dict from config .....................
    # use the values in the config json file for the results dictionary
    global cfg
    cfg = extract_cfg_from_json_file(
        root,
        AUTOGAITA_FOLDER_PATH,
        CONFIG_FILE_NAME,
        LIST_VARS,
        DICT_VARS,
        TK_STR_VARS,
        TK_BOOL_VARS,
    )

    # ...............................  header ..........................................
    # main configuration header
    main_cfg_header_label = gaita_widgets.header_label(
        root,
        "Main Configuration",
        WIDGET_CFG,
    )
    main_cfg_header_label.grid(row=0, column=0, columnspan=3, sticky="nsew")

    # ............................  main cfg section  ..................................
    # sampling rate
    samprate_label, samprate_entry = gaita_widgets.label_and_entry_pair(
        root,
        "Sampling rate of videos in Hertz (frames/second):",
        cfg["sampling_rate"],
        WIDGET_CFG,
    )
    samprate_label.grid(row=1, column=0, columnspan=2, sticky="w")
    samprate_entry.grid(row=1, column=2, sticky="w")

    # convert pixel to mm - checkbox
    convert_checkbox = gaita_widgets.checkbox(
        root,
        "Convert pixels to millimetres:",
        cfg["convert_to_mm"],
        WIDGET_CFG,
    )
    convert_checkbox.configure(
        command=lambda: gui_utils.change_widget_state_based_on_checkbox(
            cfg, "convert_to_mm", ratio_entry
        ),
    )
    convert_checkbox.grid(row=2, column=0, columnspan=2, sticky="w")

    # ratio label
    ratio_entry = ctk.CTkEntry(
        root,
        textvariable=cfg["pixel_to_mm_ratio"],
        font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
    )
    ratio_entry.grid(row=2, column=1, sticky="e")
    ratio_right_string = "pixels = 1 mm"
    ratio_right_label = ctk.CTkLabel(
        root, text=ratio_right_string, font=(TEXT_FONT_NAME, TEXT_FONT_SIZE)
    )
    ratio_right_label.grid(row=2, column=2, sticky="w")
    # to initialise the widget correctly, run this function once
    gui_utils.change_widget_state_based_on_checkbox(cfg, "convert_to_mm", ratio_entry)

    # subtract beam
    subtract_beam_checkbox = gaita_widgets.checkbox(
        root,
        "Standardise y-coordinates to baseline height (requires to be tracked)",
        cfg["subtract_beam"],
        WIDGET_CFG,
    )
    subtract_beam_checkbox.grid(row=3, column=0, columnspan=3, sticky="w")

    # flip gait direction
    flip_gait_direction_box = gaita_widgets.checkbox(
        root,
        "Adjust x-coordinates to follow direction of movement",
        cfg["flip_gait_direction"],
        WIDGET_CFG,
    )
    flip_gait_direction_box.grid(row=4, column=0, columnspan=3, sticky="w")

    # plot plots to python
    showplots_checkbox = gaita_widgets.checkbox(
        root,
        "Don't show plots in Figure GUI (save only)",
        cfg["dont_show_plots"],
        WIDGET_CFG,
    )
    showplots_checkbox.grid(row=5, column=0, columnspan=2, sticky="w")

    # bin number of SC normalisation
    bin_num_label, bin_num_entry = gaita_widgets.label_and_entry_pair(
        root,
        "Number of bins used to normalise the step cycle:",
        cfg["bin_num"],
        WIDGET_CFG,
    )
    bin_num_label.grid(row=6, column=0, columnspan=2, sticky="w")
    bin_num_entry.grid(row=6, column=2, sticky="w")

    # empty label 1 (for spacing)
    empty_label_one = ctk.CTkLabel(root, text="")
    empty_label_one.grid(row=7, column=0)

    # ..........................  advanced cfg section  ................................
    # advanced header string
    advanced_cfg_header_label = gaita_widgets.header_label(
        root,
        "Advanced Configuration",
        WIDGET_CFG,
    )
    advanced_cfg_header_label.grid(row=8, column=0, columnspan=3, sticky="nsew")

    # column name information window
    column_info_button = gaita_widgets.header_button(
        root, "Customise Joints & Angles", WIDGET_CFG
    )
    column_info_button.configure(
        command=lambda: build_column_info_window(root, cfg, WIDGET_CFG, root_dimensions)
    )
    column_info_button.grid(row=9, column=0, columnspan=3)

    # advanced cfg
    cfg_window_button = gaita_widgets.header_button(
        root, "Advanced Configuration", WIDGET_CFG
    )
    cfg_window_button.configure(
        command=lambda: build_cfg_window(root, cfg, WIDGET_CFG, root_dimensions)
    )
    cfg_window_button.grid(row=10, column=0, columnspan=3)

    # empty label 2 (for spacing)
    empty_label_two = ctk.CTkLabel(root, text="")
    empty_label_two.grid(row=11, column=0)

    # run analysis label
    runheader_label = gaita_widgets.header_label(root, "Run Analysis", WIDGET_CFG)
    runheader_label.grid(row=12, column=0, columnspan=3, sticky="nsew")

    # single gaita button
    onevid_button = gaita_widgets.header_button(root, "One Video", WIDGET_CFG)
    onevid_button.configure(
        command=lambda: build_run_and_done_windows(
            tracking_software,
            "single",
            root,
            cfg,
            WIDGET_CFG,
            GUI_SPECIFIC_VARS,
            root_dimensions,
        )
    )
    onevid_button.grid(row=13, column=1, sticky="ew")

    # multi gaita button
    multivid_button = gaita_widgets.header_button(root, "Batch Analysis", WIDGET_CFG)
    multivid_button.configure(
        command=lambda: build_run_and_done_windows(
            tracking_software,
            "multi",
            root,
            cfg,
            WIDGET_CFG,
            GUI_SPECIFIC_VARS,
            root_dimensions,
        )
    )
    multivid_button.grid(row=14, column=1, sticky="ew")

    # empty label 2 (for spacing)
    empty_label_two = ctk.CTkLabel(root, text="")
    empty_label_two.grid(row=15, column=0)

    # close & exit button
    exit_button = gaita_widgets.exit_button(root, WIDGET_CFG)
    exit_button.configure(
        command=lambda: (
            # results variable is only defined later in populate_run_window()
            # therefore only cfg settings will be updated
            update_config_file(
                "results dict not defined yet",
                cfg,
                AUTOGAITA_FOLDER_PATH,
                CONFIG_FILE_NAME,
                LIST_VARS,
                DICT_VARS,
                TK_STR_VARS,
                TK_BOOL_VARS,
            ),
            root.withdraw(),
            root.after(5000, root.destroy),
        ),
    )
    exit_button.grid(row=16, column=0, columnspan=3)

    # # .........................  widget configuration  ...............................

    # first maximise everything according to sticky
    # => Silent_Creme is some undocumented option that makes stuff uniform
    #   see: https://stackoverflow.com/questions/45847313/tkinter-grid-rowconfigure-weight-doesnt-work
    root.columnconfigure(list(range(3)), weight=1, uniform="Silent_Creme")
    root.rowconfigure(list(range(17)), weight=1, uniform="Silent_Creme")

    # then un-maximise main config rows to have them grouped together
    root.rowconfigure(list(range(1, 7)), weight=0)

    # main loop
    root.mainloop()

# %% imports
from autogaita import autogaita_utils
import tkinter as tk
import customtkinter as ctk
import os
from threading import Thread
from importlib import resources
import platform
import json
import pdb


# %% global constants
HEADER_FONT_NAME = "Calibri Bold"
HEADER_FONT_SIZE = 30
HEADER_TXT_COLOR = "#ffffff"  # white
MAIN_HEADER_FONT_SIZE = 35
TEXT_FONT_NAME = "Calibri"
TEXT_FONT_SIZE = 20
ADV_CFG_TEXT_FONT_SIZE = TEXT_FONT_SIZE - 4
FG_COLOR = "#789b73"  # grey green
HOVER_COLOR = "#287c37"  # darkish green
CLOSE_COLOR = "#840000"  # dark red
CLOSE_HOVER_COLOR = "#650021"  # maroon
CONFIG_FILE_NAME = "dlc_gui_config.json"
FLOAT_VARS = ["pixel_to_mm_ratio"]
INT_VARS = [
    "sampling_rate",
    "x_sc_broken_threshold",
    "y_sc_broken_threshold",
    "bin_num",
    "mouse_num",
    "run_num",
    "plot_joint_number",
]
LIST_VARS = [
    "hind_joints",
    "fore_joints",
    "x_standardisation_joint",
    "y_standardisation_joint",
    "beam_hind_jointadd",
    "beam_fore_jointadd",
    "beam_col_left",
    "beam_col_right",
]
DICT_VARS = ["angles"]
# TK_BOOL/STR_VARS are only used for initialising widgets based on cfg file
# (note that numbers are initialised as strings)
TK_BOOL_VARS = [
    "subtract_beam",
    "dont_show_plots",
    "convert_to_mm",
    "x_acceleration",
    "angular_acceleration",
    "save_to_xls",
    "plot_SE",
    "standardise_y_at_SC_level",
    "standardise_y_to_a_joint",
    "standardise_x_coordinates",
    "invert_y_axis",
    "flip_gait_direction",
    "analyse_average_x",
    "legend_outside",
]
TK_STR_VARS = [
    "sampling_rate",
    "pixel_to_mm_ratio",
    "x_sc_broken_threshold",
    "y_sc_broken_threshold",
    "bin_num",
    "plot_joint_number",
    "color_palette",
    "results_dir",
]
# For how the look like refer to https://r02b.github.io/seaborn_palettes/
COLOR_PALETTES_LIST = [
    "Set1",
    "Set2",
    "Set3",
    "Dark2",
    "Paired",
    "Accent",  # qualitative palettes
    "hls",
    "husl",  # circular palettes
    "rocket",
    "mako",
    "flare",
    "crest",
    "viridis",
    "plasma",
    "inferno",
    "magma",
    "cividis",  # Perceptually uniform palettes
    "rocket_r",
    "mako_r",
    "flare_r",
    "crest_r",
    "viridis_r",
    "plasma_r",
    "inferno_r",
    "magma_r",
    "cividis_r",  # uniform palettes in reversed order
]
WINDOWS_TASKBAR_MAXHEIGHT = 72

# To get the path of the autogaita folder I use __file__
# which returns the path of the autogaita_utils module imported above.
# Removing the 18 letter long "autogaita_utils.py" return the folder path
autogaita_utils_path = autogaita_utils.__file__
AUTOGAITA_FOLDER_PATH = autogaita_utils_path[:-18]

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


def dlc_gui():
    # ..........................................................................
    # ......................  root window initialisation .......................
    # ..........................................................................
    # Check for config file
    config_file_path = os.path.join(AUTOGAITA_FOLDER_PATH, CONFIG_FILE_NAME)
    if not os.path.isfile(config_file_path):
        config_file_error_msg = (
            "dlc_gui_config.json file not found in autogaita folder.\n"
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
    root.geometry(f"{int(screen_width/2)}x{screen_height}+{int(screen_width/4)}+0")
    root.title("DLC GaitA")
    fix_window_after_its_creation(root)
    configure_the_icon(root)

    # nested function: advanced configuration
    def advanced_cfg_window(cfg):
        """Advanced configuration window"""
        build_cfg_window(root, cfg, root_dimensions)

    # nested function: run windows
    def run_window(cfg, analysis):
        """Run and done windows"""
        build_run_and_done_windows(root, cfg, analysis, root_dimensions)

    # .....................  load cfg dict from config .....................
    # use the values in the config json file for the results dictionary
    global cfg
    cfg = extract_cfg_from_json_file(root)

    # ...............................  header ..........................................
    # main configuration header
    main_cfg_header_string = "Main Configuration"
    main_cfg_header_label = ctk.CTkLabel(
        root,
        text=main_cfg_header_string,
        width=w,
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=(HEADER_FONT_NAME, MAIN_HEADER_FONT_SIZE),
    )
    main_cfg_header_label.grid(row=0, column=0, columnspan=3, sticky="nsew")

    # ............................  main cfg section  ..................................
    # sampling rate
    samprate_label = ctk.CTkLabel(
        root,
        text="Sampling rate of videos in Hertz (frames/second):",
        font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
    )
    samprate_label.grid(row=1, column=0, columnspan=2, sticky="w")
    samprate_entry = ctk.CTkEntry(
        root,
        textvariable=cfg["sampling_rate"],
        font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
    )
    samprate_entry.grid(row=1, column=2, sticky="w")

    # convert pixel to mm - checkbox
    # Note: convert_checkbox also modifies the state of ratio_entry's state
    #       (which starts with being disabled), so users can only change
    #       pixel_to_mm ratio value when they want the conversion in the first
    #       place
    #       ==> AutoGaitA only uses pixel_to_mm when converting, so when we
    #           are not converting we can just leave the value at whatever
    #           value (e.g., the initialised 0))
    convert_string = "Convert pixels to millimetres:"
    convert_checkbox = ctk.CTkCheckBox(
        root,
        text=convert_string,
        variable=cfg["convert_to_mm"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        command=lambda: change_ratio_entry_state(ratio_entry),
        font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
    )
    convert_checkbox.grid(row=2, column=0, columnspan=2, sticky="w")

    # ratio  label
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
    change_ratio_entry_state(ratio_entry)

    # subtract beam
    subtract_beam_string = (
        "Standardise y-coordinates to baseline height (requires to be tracked)"
    )
    subtract_beam_checkbox = ctk.CTkCheckBox(
        root,
        text=subtract_beam_string,
        variable=cfg["subtract_beam"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
    )
    subtract_beam_checkbox.grid(row=3, column=0, columnspan=3, sticky="w")

    # flip gait direction
    flip_gait_direction_string = "Adjust x-coordinates to follow direction of movement"
    flip_gait_direction_box = ctk.CTkCheckBox(
        root,
        text=flip_gait_direction_string,
        variable=cfg["flip_gait_direction"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
    )
    flip_gait_direction_box.grid(row=4, column=0, columnspan=3, sticky="w")

    # plot plots to python
    showplots_string = "Don't show plots in Figure GUI (save only)"
    showplots_checkbox = ctk.CTkCheckBox(
        root,
        text=showplots_string,
        variable=cfg["dont_show_plots"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
    )
    showplots_checkbox.grid(row=5, column=0, columnspan=2, sticky="w")

    # bin number of SC normalisation
    bin_num_string = "Number of bins used to normalise the step cycle:"
    bin_num_label = ctk.CTkLabel(
        root, text=bin_num_string, font=(TEXT_FONT_NAME, TEXT_FONT_SIZE)
    )
    bin_num_label.grid(row=6, column=0, columnspan=2, sticky="w")
    bin_num_entry = ctk.CTkEntry(
        root, textvariable=cfg["bin_num"], font=(TEXT_FONT_NAME, TEXT_FONT_SIZE)
    )
    bin_num_entry.grid(row=6, column=2, sticky="w")

    # empty label 1 (for spacing)
    empty_label_one = ctk.CTkLabel(root, text="")
    empty_label_one.grid(row=7, column=0)

    # ..........................  advanced cfg section  ................................
    # advanced header string
    advanced_cfg_header_string = "Advanced Configuration"
    advanced_cfg_header_label = ctk.CTkLabel(
        root,
        text=advanced_cfg_header_string,
        width=w,
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=(HEADER_FONT_NAME, MAIN_HEADER_FONT_SIZE),
    )
    advanced_cfg_header_label.grid(row=8, column=0, columnspan=3, sticky="nsew")

    # column name information window
    column_info_string = "Customise Joints & Angles"
    column_info_button = ctk.CTkButton(
        root,
        text=column_info_string,
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: build_column_info_window(root, cfg, root_dimensions),
    )
    column_info_button.grid(row=9, column=0, columnspan=3)

    # advanced cfg
    cfg_window_button = ctk.CTkButton(
        root,
        text="Advanced Configuration",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: (advanced_cfg_window(cfg)),
    )
    cfg_window_button.grid(row=10, column=0, columnspan=3)

    # empty label 2 (for spacing)
    empty_label_two = ctk.CTkLabel(root, text="")
    empty_label_two.grid(row=11, column=0)

    # run analysis label
    runheader_label = ctk.CTkLabel(
        root,
        text="Run Analysis",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=(HEADER_FONT_NAME, MAIN_HEADER_FONT_SIZE),
    )
    runheader_label.grid(row=12, column=0, columnspan=3, sticky="nsew")

    # single gaita button
    onevid_button = ctk.CTkButton(
        root,
        text="One Video",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: run_window(cfg, "single"),
    )
    onevid_button.grid(row=13, column=1, sticky="ew")

    # multi gaita button
    multivid_button = ctk.CTkButton(
        root,
        text="Batch Analysis",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: run_window(cfg, "multi"),
    )
    multivid_button.grid(row=14, column=1, sticky="ew")

    # empty label 2 (for spacing)
    empty_label_two = ctk.CTkLabel(root, text="")
    empty_label_two.grid(row=15, column=0)

    # close & exit button
    close_button = ctk.CTkButton(
        root,
        text="Exit",
        fg_color=CLOSE_COLOR,
        hover_color=CLOSE_HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: (
            # results variable is only defined later in populate_run_window()
            # therefore only cfg settings will be updated
            update_config_file("results dict not defined yet", cfg),
            root.withdraw(),
            root.after(5000, root.destroy),
        ),
    )
    close_button.grid(row=16, column=0, columnspan=3)

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


# %%..........  LOCAL FUNCTION(S) #1 - BUILD ADVANCED CFG WINDOW  .............


def build_cfg_window(root, cfg, root_dimensions):
    """Build advanced configuration window"""
    # unpack root window dimensions
    w = root_dimensions[0]
    h = root_dimensions[1]
    # build window
    cfg_window = ctk.CTkToplevel(root)
    cfg_window.title("Advanced Configuration")
    cfg_window.geometry(f"{int(w/2)}x{h}+{int(w/4)}+0")
    fix_window_after_its_creation(cfg_window)

    #  ...........................  advanced analysis  .................................

    # advanced analysis header
    adv_cfg_analysis_header_label = ctk.CTkLabel(
        cfg_window,
        text="Analysis",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=(HEADER_FONT_NAME, MAIN_HEADER_FONT_SIZE),
    )
    adv_cfg_analysis_header_label.grid(
        row=0, column=0, rowspan=2, columnspan=2, sticky="nsew"
    )

    # x & y threshold for rejecting SCs
    threshold_string = "What criteria (in pixels) to use for rejecting step cycles?"
    thresh_label = ctk.CTkLabel(
        cfg_window, text=threshold_string, font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE)
    )
    thresh_label.grid(row=2, column=0, columnspan=2, sticky="ew")
    x_threshold_string = "Along x-dimension:"
    x_thresh_label = ctk.CTkLabel(
        cfg_window,
        text=x_threshold_string,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    x_thresh_label.grid(row=3, column=0, sticky="e")
    x_thresh_entry = ctk.CTkEntry(
        cfg_window,
        textvariable=cfg["x_sc_broken_threshold"],
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    x_thresh_entry.grid(row=3, column=1, sticky="w")
    # y threshold for rejecting SCs
    y_thresh_string = "Along y-dimension:"
    y_thresh_label = ctk.CTkLabel(
        cfg_window, text=y_thresh_string, font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE)
    )
    y_thresh_label.grid(row=4, column=0, sticky="e")
    y_thresh_entry = ctk.CTkEntry(
        cfg_window,
        textvariable=cfg["y_sc_broken_threshold"],
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    y_thresh_entry.grid(row=4, column=1, sticky="w")

    # acceleration label
    acceleration_string = "Analyse (i.e. plot & export) accelerations for:"
    acceleration_label = ctk.CTkLabel(
        cfg_window,
        text=acceleration_string,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    acceleration_label.grid(row=5, column=0, columnspan=2)
    # x acceleration
    x_accel_box = ctk.CTkCheckBox(
        cfg_window,
        text="x-coordinates",
        variable=cfg["x_acceleration"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    x_accel_box.grid(row=6, column=0, sticky="e")
    # angular acceleration
    angular_accel_box = ctk.CTkCheckBox(
        cfg_window,
        text="angles",
        variable=cfg["angular_acceleration"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    angular_accel_box.grid(row=6, column=1, sticky="w")

    # y standardisation at each step cycle separately
    standardise_y_at_SC_level_string = (
        "Standardise y-coordinates separately for all step cycles"
    )
    standardise_y_at_SC_level_box = ctk.CTkCheckBox(
        cfg_window,
        text=standardise_y_at_SC_level_string,
        variable=cfg["standardise_y_at_SC_level"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    standardise_y_at_SC_level_box.grid(row=7, column=0, columnspan=2)

    # y standardisation to a specific joint not global minimum
    standardise_y_to_joint_string = (
        "Standardise y to a joint instead of to global minimum"
    )
    standardise_y_to_joint_box = ctk.CTkCheckBox(
        cfg_window,
        text=standardise_y_to_joint_string,
        variable=cfg["standardise_y_to_a_joint"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
        command=lambda: change_y_standardisation_joint_entry_state(
            y_standardisation_joint_entry
        ),
    )
    standardise_y_to_joint_box.grid(row=8, column=0, columnspan=2)

    # y standardisation joint string label & entry
    y_standardisation_joint_string = "Y-standardisation joint:"
    y_standardisation_joint_label = ctk.CTkLabel(
        cfg_window,
        text=y_standardisation_joint_string,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    y_standardisation_joint_label.grid(row=9, column=0, sticky="e")
    y_standardisation_joint_entry = ctk.CTkEntry(
        cfg_window,
        textvariable=cfg["y_standardisation_joint"][0],
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    y_standardisation_joint_entry.grid(row=9, column=1, sticky="w")
    # to initialise the widget correctly, run this function once
    change_y_standardisation_joint_entry_state(y_standardisation_joint_entry)

    # analyse average x coordinates
    analyse_average_x_string = "Analyse x-coordinate averages"
    analyse_average_x_box = ctk.CTkCheckBox(
        cfg_window,
        text=analyse_average_x_string,
        variable=cfg["analyse_average_x"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
        command=lambda: change_x_standardisation_box_state(
            standardise_x_coordinates_box
        ),
    )
    analyse_average_x_box.grid(row=10, column=0)

    # standardise x coordinates
    standardise_x_coordinates_string = "Standardise x-coordinates"
    standardise_x_coordinates_box = ctk.CTkCheckBox(
        cfg_window,
        text=standardise_x_coordinates_string,
        variable=cfg["standardise_x_coordinates"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
        command=lambda: change_x_standardisation_joint_entry_state(
            x_standardisation_joint_entry
        ),
    )
    standardise_x_coordinates_box.grid(row=10, column=1)
    change_x_standardisation_box_state(standardise_x_coordinates_box)

    # x standardisation joint string label & entry
    x_standardisation_joint_string = "X-standardisation joint:"
    x_standardisation_joint_label = ctk.CTkLabel(
        cfg_window,
        text=x_standardisation_joint_string,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    x_standardisation_joint_label.grid(row=11, column=0, sticky="e")
    x_standardisation_joint_entry = ctk.CTkEntry(
        cfg_window,
        textvariable=cfg["x_standardisation_joint"][0],
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    x_standardisation_joint_entry.grid(row=11, column=1, sticky="w")
    change_x_standardisation_joint_entry_state(x_standardisation_joint_entry)

    # invert y-axis
    invert_y_axis_string = "Invert y-axis"
    invert_y_axis_box = ctk.CTkCheckBox(
        cfg_window,
        text=invert_y_axis_string,
        variable=cfg["invert_y_axis"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    invert_y_axis_box.grid(row=12, column=0, columnspan=2)

    #  .............................  advanced output  .................................
    # advanced analysis header
    adv_cfg_output_header_label = ctk.CTkLabel(
        cfg_window,
        text="Output",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=(HEADER_FONT_NAME, MAIN_HEADER_FONT_SIZE),
    )
    adv_cfg_output_header_label.grid(
        row=13, column=0, rowspan=2, columnspan=2, sticky="nsew"
    )

    # number of hindlimb (primary) joints to plot
    plot_joint_num_string = "Number of primary joints to plot in detail"
    plot_joint_num__label = ctk.CTkLabel(
        cfg_window,
        text=plot_joint_num_string,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    plot_joint_num__label.grid(row=15, column=0, columnspan=2)
    plot_joint_num_entry = ctk.CTkEntry(
        cfg_window,
        textvariable=cfg["plot_joint_number"],
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    plot_joint_num_entry.grid(row=16, column=0, columnspan=2)

    # save to xls
    save_to_xls_string = "Save results as .xlsx instead of .csv files"
    save_to_xls_box = ctk.CTkCheckBox(
        cfg_window,
        text=save_to_xls_string,
        variable=cfg["save_to_xls"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    save_to_xls_box.grid(row=17, column=0, columnspan=2)

    # plot SE
    plot_SE_string = "Use standard error instead of standard deviation for plots"
    plot_SE_box = ctk.CTkCheckBox(
        cfg_window,
        text=plot_SE_string,
        variable=cfg["plot_SE"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    plot_SE_box.grid(row=18, column=0, columnspan=2)

    # color palette
    color_palette_string = "Choose figures' color palette"
    color_palette_label = ctk.CTkLabel(
        cfg_window,
        text=color_palette_string,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    color_palette_label.grid(row=19, column=0, columnspan=2)
    color_palette_entry = ctk.CTkOptionMenu(
        cfg_window,
        values=COLOR_PALETTES_LIST,
        variable=cfg["color_palette"],
        fg_color=FG_COLOR,
        button_color=FG_COLOR,
        button_hover_color=HOVER_COLOR,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    color_palette_entry.grid(row=20, column=0, columnspan=2)

    # legend outside
    legend_outside_string = "Plot legends outside of figures' panels"
    legend_outside_checkbox = ctk.CTkCheckBox(
        cfg_window,
        text=legend_outside_string,
        variable=cfg["legend_outside"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    legend_outside_checkbox.grid(row=21, column=0, columnspan=2)

    # results dir
    results_dir_string = (
        "Save Results subfolders to directory below instead of to data's"
    )
    results_dir_label = ctk.CTkLabel(
        cfg_window,
        text=results_dir_string,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    results_dir_label.grid(row=22, column=0, columnspan=2)
    results_dir_entry = ctk.CTkEntry(
        cfg_window,
        textvariable=cfg["results_dir"],
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    results_dir_entry.grid(row=23, column=0, columnspan=2)

    # done button
    adv_cfg_done_button = ctk.CTkButton(
        cfg_window,
        text="I am done, update cfg.",
        fg_color=CLOSE_COLOR,
        hover_color=CLOSE_HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: cfg_window.destroy(),
    )
    adv_cfg_done_button.grid(
        row=24, column=0, columnspan=2, rowspan=2, sticky="nsew", padx=10, pady=(10, 5)
    )
    # maximise widgets
    cfg_window.columnconfigure(list(range(2)), weight=1, uniform="Silent_Creme")
    cfg_window.rowconfigure(list(range(25)), weight=1, uniform="Silent_Creme")


# %%..............  LOCAL FUNCTION(S) #2 - BUILD COLUMN INFO WINDOW  ...................
# Note
# ----
# Hindlimb and forelimb joints were re-named to primary and secondary joints @ v0.4.0.
# I kept the old variable/key-names for compatibility with autogaita_dlc.
# => Except for input to build_beam_jointadd_window since that is used for a string


def build_column_info_window(root, cfg, root_dimensions):
    """Build a window allowing users to configure custom column names if required"""
    columnwindow = ctk.CTkToplevel(root)
    columnwindow.geometry("%dx%d+%d+%d" % root_dimensions)
    columnwindow.title("Custom column names & features")
    fix_window_after_its_creation(columnwindow)

    # .............  Nested Function: Add joint label & entry  .........................
    def add_joint(window, key):
        """Add a joint if needed or a angle name/lower_joint/upper_joint if angle widget"""
        # append StringVar to cfg appropriately
        if key == "angles":
            for angle_key in cfg[key]:
                cfg[key][angle_key].append(tk.StringVar(root, ""))
        else:
            cfg[key].append(tk.StringVar(root, ""))
        # find out the number of rows to append to it
        nrows = window.grid_size()[1]
        # add stuff based on to which case we are adding
        if key in [
            "hind_joints",
            "fore_joints",
            "beam_hind_jointadd",
            "beam_fore_jointadd",
        ]:
            if key == "hind_joints":
                label_string = "Primary Joint #" + str(len(cfg[key]))
            elif key == "fore_joints":
                label_string = "Secondary Joint #" + str(len(cfg[key]))
            elif key == "beam_hind_jointadd":
                label_string = "Left beam-subtraction joint #" + str(len(cfg[key]))
            elif key == "beam_fore_jointadd":
                label_string = "Right beam-subtraction joint #" + str(len(cfg[key]))
            label = ctk.CTkLabel(
                window, text=label_string, font=(TEXT_FONT_NAME, TEXT_FONT_SIZE)
            )
            label.grid(row=nrows + 1, column=0, sticky="ew")
            entry = ctk.CTkEntry(
                window, textvariable=cfg[key][-1], font=(TEXT_FONT_NAME, TEXT_FONT_SIZE)
            )
            entry.grid(row=nrows + 2, column=0)
        elif key == "angles":
            for a, angle_key in enumerate(cfg[key]):
                if angle_key == "name":
                    this_case = "Angle"
                elif angle_key == "lower_joint":
                    this_case = "Lower Joint"
                elif angle_key == "upper_joint":
                    this_case = "Upper Joint"
                label = ctk.CTkLabel(
                    window,
                    text=this_case + " #" + str(len(cfg[key][angle_key])),
                    font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
                )
                label.grid(row=nrows + 1, column=angle_column + a, sticky="ew")
                entry = ctk.CTkEntry(
                    window,
                    textvariable=cfg[key][angle_key][-1],
                    font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
                )
                entry.grid(row=nrows + 2, column=angle_column + a)
        # maximise columns
        for c in range(window.grid_size()[0]):
            window.grid_columnconfigure(c, weight=1)

    # ...............  Nested Function: Beam jointadd window  ..........................
    def build_beam_window():
        """Build a window for configuring the beam, i.e.:
        1. beam_col_left and right
        ==> what were the col names of your beam in the beam file
        2. beam_hind_jointadd and beam_fore_jointadd
        ==> what additional joints (not included in hind/fore) do you want to include in beam standardisation?
        """
        # build window and fullscreen
        beamwindow = ctk.CTkToplevel(columnwindow)
        beamwindow.geometry("%dx%d+%d+%d" % (root_dimensions))
        beamwindow.title("Beam Configuration")
        fix_window_after_its_creation(beamwindow)
        beam_scrollable_rows = 1
        total_padx = 20
        left_padx = (total_padx, total_padx / 2)
        right_padx = (total_padx / 2, total_padx)
        # ................... left section - left beam / hind joints ...................
        # left beam label
        beam_left_label = ctk.CTkLabel(
            beamwindow,
            text="Left beam column (primary joints')",
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        )
        beam_left_label.grid(row=0, column=0, sticky="nsew")
        # left beam entry
        beam_left_entry = ctk.CTkEntry(
            beamwindow,
            textvariable=cfg["beam_col_left"][0],
            font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
        )
        beam_left_entry.grid(row=1, column=0)
        # empty label one (for spacing)
        empty_label_one = ctk.CTkLabel(beamwindow, text="")
        empty_label_one.grid(row=2, column=0)
        # important: cfg key for forelimb joint add
        hindlimb_key = "beam_hind_jointadd"
        # hindlimb jointadd label
        hind_jointsubtract_label = ctk.CTkLabel(
            beamwindow,
            text="Left beam: additional joints subtracted",
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        )
        hind_jointsubtract_label.grid(row=3, column=0, sticky="nsew")
        # initialise scrollable frame for beamsubtract windows
        hind_jointsubtract_frame = ctk.CTkScrollableFrame(beamwindow)
        hind_jointsubtract_frame.grid(
            row=4,
            column=0,
            rowspan=beam_scrollable_rows,
            sticky="nsew",
        )
        # initialise labels & entries
        initialise_labels_and_entries(
            hind_jointsubtract_frame,
            hindlimb_key,
            "Left beam-subtraction joint",
        )
        # add button
        add_hindjoint_button = ctk.CTkButton(
            beamwindow,
            text="Add left beam-subtraction joint",
            fg_color=FG_COLOR,
            hover_color=HOVER_COLOR,
            font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
            command=lambda: add_joint(
                hind_jointsubtract_frame, hindlimb_key
            ),  # input = cfg's key
        )
        add_hindjoint_button.grid(
            row=4 + beam_scrollable_rows,
            column=0,
            sticky="nsew",
            padx=left_padx,
            pady=20,
        )
        # .................. right section - right beam / fore joints ..................
        # right beam label
        beam_right_label = ctk.CTkLabel(
            beamwindow,
            text="Right beam column (secondary joints')",
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        )
        beam_right_label.grid(row=0, column=1, sticky="nsew")
        # right beam entry
        beam_right_entry = ctk.CTkEntry(
            beamwindow,
            textvariable=cfg["beam_col_right"][0],
            font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
        )
        beam_right_entry.grid(row=1, column=1)
        # empty label two (for spacing)
        empty_label_two = ctk.CTkLabel(beamwindow, text="")
        empty_label_two.grid(row=2, column=1)
        # important: cfg key for forelimb joint add
        forelimb_key = "beam_fore_jointadd"
        # hindlimb jointadd label
        fore_jointsubtract_label = ctk.CTkLabel(
            beamwindow,
            text="Right beam: additional joints subtracted",
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        )
        fore_jointsubtract_label.grid(row=3, column=1, sticky="nsew")
        # initialise scrollable frame for beamsubtract windows
        fore_jointsubtract_frame = ctk.CTkScrollableFrame(beamwindow)
        fore_jointsubtract_frame.grid(
            row=4,
            column=1,
            rowspan=beam_scrollable_rows,
            sticky="nsew",
        )
        # initialise labels & entries
        initialise_labels_and_entries(
            fore_jointsubtract_frame,
            forelimb_key,
            "Right beam-subtraction joint",
        )
        # add button
        add_forejoint_button = ctk.CTkButton(
            beamwindow,
            text="Add right beam-subtraction joint",
            fg_color=FG_COLOR,
            hover_color=HOVER_COLOR,
            font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
            command=lambda: add_joint(
                fore_jointsubtract_frame, forelimb_key
            ),  # input = cfg's key
        )
        add_forejoint_button.grid(
            row=4 + beam_scrollable_rows,
            column=1,
            sticky="nsew",
            padx=right_padx,
            pady=20,
        )
        # .................... bottom section - update & close  ........................
        # empty label three (for spacing)
        empty_label_three = ctk.CTkLabel(beamwindow, text="")
        empty_label_three.grid(row=5 + beam_scrollable_rows, column=0, columnspan=2)
        # done button
        beam_done_button = ctk.CTkButton(
            beamwindow,
            text="I am done, update cfg!",
            fg_color=CLOSE_COLOR,
            hover_color=CLOSE_HOVER_COLOR,
            font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
            command=lambda: beamwindow.destroy(),
        )
        beam_done_button.grid(
            row=6 + beam_scrollable_rows,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=20,
            pady=20,
        )
        # maximise widgets
        maximise_widgets(beamwindow)

    # ...................  Scrollable Window Configuration  ............................
    scrollable_rows = 7

    # ...................  Column 0: hind limb joint names  ............................
    hind_column = 0
    # header label
    hind_joint_label = ctk.CTkLabel(
        columnwindow,
        text="Primary Joints",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
    )
    hind_joint_label.grid(row=0, column=hind_column, sticky="nsew", pady=(0, 5))
    # initialise scrollable frame for hindlimb
    hindlimb_frame = ctk.CTkScrollableFrame(columnwindow)
    hindlimb_frame.grid(
        row=1,
        column=hind_column,
        rowspan=scrollable_rows,
        sticky="nsew",
    )
    # initialise labels & entries with hind limb defaults
    initialise_labels_and_entries(hindlimb_frame, "hind_joints", "Primary Joint ")
    # add joint button
    add_hind_joint_button = ctk.CTkButton(
        columnwindow,
        text="Add Primary Joint",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: add_joint(
            hindlimb_frame, "hind_joints"
        ),  # 2nd input = cfg's key
    )
    add_hind_joint_button.grid(
        row=2 + scrollable_rows, column=hind_column, sticky="nsew", padx=5, pady=(10, 5)
    )
    # beam config window label
    beam_window_label = ctk.CTkLabel(columnwindow, text="")  # empty for spacing only
    beam_window_label.grid(
        row=4 + scrollable_rows,
        column=hind_column,
        columnspan=2,
        sticky="nsew",
        padx=1,
        pady=(0, 5),
    )
    # beam config window button
    beam_window_button = ctk.CTkButton(
        columnwindow,
        text="Baseline (Beam) Configuration",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: build_beam_window(),
    )
    beam_window_button.grid(
        row=5 + scrollable_rows,
        column=hind_column,
        columnspan=2,
        sticky="nsew",
        padx=40,
        pady=(10, 5),
    )

    # ...................  Column 1: fore limb joint names  ............................
    fore_column = 1
    # header label
    fore_joint_label = ctk.CTkLabel(
        columnwindow,
        text="Secondary Joints",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
    )
    fore_joint_label.grid(row=0, column=fore_column, sticky="nsew", pady=(0, 5))
    # initialise scrollable frame for forelimb
    forelimb_frame = ctk.CTkScrollableFrame(columnwindow)
    forelimb_frame.grid(
        row=1, column=fore_column, rowspan=scrollable_rows, sticky="nsew"
    )
    # initialise labels & entries with fore limb defaults
    initialise_labels_and_entries(
        forelimb_frame,
        "fore_joints",
        "Secondary Joint ",
    )
    # add joint button
    add_fore_joint_button = ctk.CTkButton(
        columnwindow,
        text="Add Secondary Joint",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: add_joint(
            forelimb_frame, "fore_joints"
        ),  # 2nd input = cfg's key
    )
    add_fore_joint_button.grid(
        row=2 + scrollable_rows, column=fore_column, sticky="nsew", padx=5, pady=(10, 5)
    )

    # .........  Column 2: angle names/joint-definitions & done button  ................
    angle_column = 2
    # header label
    angle_label = ctk.CTkLabel(
        columnwindow,
        text="Angle Configuration",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
    )
    angle_label.grid(
        row=0, column=angle_column, columnspan=3, sticky="nsew", pady=(0, 5)
    )
    # initialise scrollable frame for angles
    angle_frame = ctk.CTkScrollableFrame(columnwindow)
    angle_frame.grid(
        row=1, column=angle_column, rowspan=scrollable_rows, columnspan=3, sticky="nsew"
    )
    # initial entries & labels
    for a, angle_key in enumerate(cfg["angles"]):
        if angle_key == "name":
            this_case = "Angle"
        elif angle_key == "lower_joint":
            this_case = "Lower Joint"
        elif angle_key == "upper_joint":
            this_case = "Upper Joint"
        initialise_labels_and_entries(
            angle_frame, ["angles", angle_key], this_case, angle_column + a
        )
    # add angle trio button
    add_angle_button = ctk.CTkButton(
        columnwindow,
        text="Add Angle",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: add_joint(angle_frame, "angles"),  # 2nd input = cfg's key
    )
    add_angle_button.grid(
        row=2 + scrollable_rows,
        column=angle_column,
        columnspan=3,
        sticky="nsew",
        padx=5,
        pady=(10, 5),
    )
    # done label
    done_label = ctk.CTkLabel(columnwindow, text="")  # empty for spacing only
    done_label.grid(
        row=4 + scrollable_rows,
        column=angle_column,
        columnspan=3,
        sticky="nsew",
        padx=1,
        pady=(0, 5),
    )
    # done button
    columncfg_done_button = ctk.CTkButton(
        columnwindow,
        text="I am done, update cfg!",
        fg_color=CLOSE_COLOR,
        hover_color=CLOSE_HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: columnwindow.destroy(),
    )
    columncfg_done_button.grid(
        row=5 + scrollable_rows,
        column=angle_column,
        columnspan=3,
        sticky="nsew",
        padx=40,
        pady=(10, 5),
    )
    # maximise everything in columnwindow
    maximise_widgets(columnwindow)


def initialise_labels_and_entries(window, key, which_case_string, *args):
    """Add labels & entries for joint column information areas"""
    # we input a list of strings if we use this function to initialise angles (since
    # cfg["angle"] itself is a dict) => handle this particularly at textvariable
    # parameter of CTkEntry
    if type(key) is str:
        this_var = cfg[key]
    elif type(key) is list:
        this_var = cfg[key[0]][key[1]]
    joint_labels = [[] for _ in this_var]
    joint_entries = [[] for _ in this_var]
    row_counter = 0  # because we always call this in a scrollable frame
    if args:
        column_number = args
    else:
        column_number = 0
    for j, joint in enumerate(this_var):
        joint_labels[j] = ctk.CTkLabel(
            window,
            text=which_case_string + " #" + str(j + 1),
            font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
        )
        joint_labels[j].grid(row=row_counter, column=column_number, sticky="ew")
        row_counter += 1
        if type(key) is str:
            joint_entries[j] = ctk.CTkEntry(
                window, textvariable=cfg[key][j], font=(TEXT_FONT_NAME, TEXT_FONT_SIZE)
            )
        elif type(key) is list:
            joint_entries[j] = ctk.CTkEntry(
                window,
                textvariable=cfg[key[0]][key[1]][j],
                font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
            )
        # span only in width
        joint_entries[j].grid(row=row_counter, column=column_number)
        row_counter += 1
    # maximise columns
    for c in range(window.grid_size()[0]):
        window.grid_columnconfigure(c, weight=1)


# %%..........  LOCAL FUNCTION(S) #3 - BUILD RUN AND DONE WINDOWS .............
def build_run_and_done_windows(root, cfg, analysis, root_dimensions):
    """The run window, get information, pass information & run."""
    # unpack root window dimensions
    w = root_dimensions[0]
    h = root_dimensions[1]

    # .............................  run window  ..............................
    runwindow = ctk.CTkToplevel(root)
    user_ready = tk.IntVar(runwindow, 0)  # used to know when user is ready 4 screen 3
    if analysis == "single":
        runwindow.title("Single GaitA")
    else:
        runwindow.title("Batch GaitA")
    # runwindow.geometry("%dx%d+%d+%d" % root_dimensions)
    runwindow.geometry(f"{int(w/2)}x{h}+{int(w/4)}+0")
    fix_window_after_its_creation(runwindow)
    # fill window with required info labels & entries - then get results
    results = populate_run_window(runwindow, w, analysis, user_ready)

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
        this_runs_results, this_runs_cfg = get_results_and_cfg(results, cfg, analysis)
    except:
        error_msg = get_results_and_cfg(results, cfg, analysis)
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
    fix_window_after_its_creation(donewindow)

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
            runanalysis(this_runs_results, this_runs_cfg, analysis),
            donewindow.destroy(),
        ),
    )
    done_button.grid(row=4, column=0, sticky="nsew", pady=10, padx=200)

    maximise_widgets(donewindow)


# %%..........  LOCAL FUNCTION(S) #4 - POPULATE RUN WINDOW ....................
def populate_run_window(runwindow, runwindow_w, analysis, user_ready):
    """Populate the information window before running analysis"""

    # ..................... load results dict from config.....................
    # use the values in the config json file for the results dictionary
    results = extract_results_from_json_file(runwindow)

    # ........................  build the frame  ...............................
    if analysis == "single":
        # mouse number
        mousenum_string = "What is the number of the animal/subject?"
        mousenum_label = ctk.CTkLabel(
            runwindow,
            text=mousenum_string,
            font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
        )
        mousenum_label.grid(row=0, column=0)
        mousenum_entry = ctk.CTkEntry(
            runwindow,
            textvariable=results["mouse_num"],
            font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
        )
        mousenum_entry.grid(row=1, column=0)
        # run number
        runnum_string = "What is the number of the trial?"
        runnum_label = ctk.CTkLabel(
            runwindow, text=runnum_string, font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE)
        )
        runnum_label.grid(row=2, column=0)
        runnum_entry = ctk.CTkEntry(
            runwindow,
            textvariable=results["run_num"],
            font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
        )
        runnum_entry.grid(row=3, column=0)
    # how we index rows from here upon depends on current analysis
    if analysis == "single":
        r = 4
    else:
        r = 0
    # root directory
    rootdir_string = "Directory containing the files to be analysed"
    rootdir_label = ctk.CTkLabel(
        runwindow, text=rootdir_string, font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE)
    )
    rootdir_label.grid(row=r + 0, column=0)
    rootdir_entry = ctk.CTkEntry(
        runwindow,
        textvariable=results["root_dir"],
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    rootdir_entry.grid(row=r + 1, column=0)
    # stepcycle latency XLS
    SCXLS_string = "Filename of the Annotation Table Excel file"
    SCXLS_label = ctk.CTkLabel(
        runwindow, text=SCXLS_string, font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE)
    )
    SCXLS_label.grid(row=r + 2, column=0)
    SCXLS_entry = ctk.CTkEntry(
        runwindow,
        textvariable=results["sctable_filename"],
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    SCXLS_entry.grid(row=r + 3, column=0)
    # empty label 1 (for spacing)
    empty_label_one = ctk.CTkLabel(runwindow, text="")
    empty_label_one.grid(row=r + 4, column=0)
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
    data_string = "[G] What is the identifier of the DLC-tracked coordinate file?"
    data_label = ctk.CTkLabel(
        runwindow, text=data_string, font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE)
    )
    data_label.grid(row=r + 8, column=0)
    data_entry = ctk.CTkEntry(
        runwindow,
        textvariable=results["data_string"],
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    data_entry.grid(row=r + 9, column=0)
    # beam string
    beam_string = (
        "[G] What is the identifier of the DLC-tracked baseline file? (optional)"
    )
    beam_label = ctk.CTkLabel(
        runwindow, text=beam_string, font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE)
    )
    beam_label.grid(row=r + 10, column=0)
    beam_entry = ctk.CTkEntry(
        runwindow,
        textvariable=results["beam_string"],
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    beam_entry.grid(row=r + 11, column=0)
    # premouse_num string
    premouse_string = "[B] Define the 'unique subject identifier' preceding the number"
    premouse_label = ctk.CTkLabel(
        runwindow, text=premouse_string, font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE)
    )
    premouse_label.grid(row=r + 12, column=0)
    premouse_entry = ctk.CTkEntry(
        runwindow,
        textvariable=results["premouse_string"],
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    premouse_entry.grid(row=r + 13, column=0)
    # postmouse_num string
    postmouse_string = "[C] Define the 'unique task identifier"
    postmouse_label = ctk.CTkLabel(
        runwindow, text=postmouse_string, font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE)
    )
    postmouse_label.grid(row=r + 14, column=0)
    postmouse_entry = ctk.CTkEntry(
        runwindow,
        textvariable=results["postmouse_string"],
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    postmouse_entry.grid(row=r + 15, column=0)
    # prerun string
    prerun_string = "[D] Define the 'unique trial identifier"
    prerun_label = ctk.CTkLabel(
        runwindow, text=prerun_string, font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE)
    )
    prerun_label.grid(row=r + 16, column=0)
    prerun_entry = ctk.CTkEntry(
        runwindow,
        textvariable=results["prerun_string"],
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    prerun_entry.grid(row=r + 17, column=0)
    # postrun string
    postrun_string = "[E] Define the 'unique camera identifier"
    postrun_label = ctk.CTkLabel(
        runwindow, text=postrun_string, font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE)
    )
    postrun_label.grid(row=r + 18, column=0)
    postrun_entry = ctk.CTkEntry(
        runwindow,
        textvariable=results["postrun_string"],
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
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
            update_config_file(results, cfg),
            user_ready.set(1),
        ),
    )
    finishbutton.grid(row=r + 20, column=0, rowspan=2, sticky="nsew", pady=5, padx=70)
    # maximise widgets
    maximise_widgets(runwindow)
    # wait until user is ready before returning
    runwindow.wait_variable(user_ready)
    return results


# %%..........  LOCAL FUNCTION(S) #5 - PREPARE & CALL AUTOGAITA ............


def runanalysis(this_runs_results, this_runs_cfg, analysis):
    """Run the main program"""
    if analysis == "single":
        run_thread = Thread(
            target=analyse_single_run, args=(this_runs_results, this_runs_cfg)
        )
        # analyse_single_run(this_runs_results, this_runs_cfg)
    elif analysis == "multi":
        run_thread = Thread(
            target=analyse_multi_run, args=(this_runs_results, this_runs_cfg)
        )
        # analyse_multi_run(this_runs_results, this_runs_cfg)
    run_thread.start()


def analyse_single_run(this_runs_results, this_runs_cfg):
    """Prepare for one execution of autogaita_dlc & execute"""
    # prepare (folderinfo first to handle root_dir "/" issue if needed)
    folderinfo = prepare_folderinfo(this_runs_results)
    if folderinfo is None:
        error_msg = (
            "No directory found at: " + this_runs_results["root_dir"] + " - try again!"
        )
        tk.messagebox.showerror(title="Try again", message=error_msg)
        print(error_msg)
        return
    info = {}  # info dict: run-specific info
    info["mouse_num"] = this_runs_results["mouse_num"]
    info["run_num"] = this_runs_results["run_num"]
    info["name"] = "ID " + str(info["mouse_num"]) + " - Run " + str(info["run_num"])
    if this_runs_cfg["results_dir"]:
        info["results_dir"] = os.path.join(this_runs_cfg["results_dir"], info["name"])
    else:
        info["results_dir"] = os.path.join(
            folderinfo["root_dir"], "Results", info["name"]
        )
    # execute
    autogaita_utils.try_to_run_gaita("DLC", info, folderinfo, this_runs_cfg, False)


def analyse_multi_run(this_runs_results, this_runs_cfg):
    """Prepare for multi-execution of autogaita_dlc & loop-execute"""
    # prepare (folderinfo first to handle root_dir "/" issue if needed)
    folderinfo = prepare_folderinfo(this_runs_results)
    if folderinfo is None:
        error_msg = (
            "No directory found at: " + this_runs_results["root_dir"] + " - try again!"
        )
        tk.messagebox.showerror(title="Try again", message=error_msg)
        print(error_msg)
        return
    info = extract_info(folderinfo)  # folderinfo has info of individual runs - extract
    for idx in range(len(info["name"])):
        multirun_run_a_single_dataset(idx, info, folderinfo, this_runs_cfg)


def multirun_run_a_single_dataset(idx, info, folderinfo, this_runs_cfg):
    """Run the main code of individual run-analyses based on current this_runs_cfg"""
    # extract and pass info of this mouse/run (also update resdir)
    this_info = {}
    for keyname in info.keys():
        this_info[keyname] = info[keyname][idx]
    if this_runs_cfg["results_dir"]:
        this_info["results_dir"] = os.path.join(
            this_runs_cfg["results_dir"], this_info["name"]
        )
    else:
        this_info["results_dir"] = os.path.join(
            folderinfo["root_dir"], "Results", this_info["name"]
        )
    # important to only pass this_info to main script here (1 run at a time!)
    autogaita_utils.try_to_run_gaita("DLC", this_info, folderinfo, this_runs_cfg, True)


# %%...............  LOCAL FUNCTION(S) #6 - VARIOUS HELPER FUNCTIONS  ..................


def change_ratio_entry_state(ratio_entry):
    """Change the state of ratio entry widget based on whether user wants
    to convert pixels to mm or not.
    """
    if cfg["convert_to_mm"].get() == True:
        ratio_entry.configure(state="normal")
    elif cfg["convert_to_mm"].get() == False:
        ratio_entry.configure(state="disabled")


def change_y_standardisation_joint_entry_state(y_standardisation_joint_entry):
    if cfg["standardise_y_to_a_joint"].get() == True:
        y_standardisation_joint_entry.configure(state="normal")
    elif cfg["standardise_y_to_a_joint"].get() == False:
        y_standardisation_joint_entry.configure(state="disabled")


def change_x_standardisation_box_state(standardise_x_coordinates_box):
    if cfg["analyse_average_x"].get() == True:
        standardise_x_coordinates_box.configure(state="normal")
    elif cfg["analyse_average_x"].get() == False:
        standardise_x_coordinates_box.configure(state="disabled")


def change_x_standardisation_joint_entry_state(x_standardisation_joint_entry):
    if cfg["standardise_x_coordinates"].get() == True:
        x_standardisation_joint_entry.configure(state="normal")
    elif cfg["standardise_x_coordinates"].get() == False:
        x_standardisation_joint_entry.configure(state="disabled")


def maximise_widgets(window):
    """Maximises all widgets to look good in fullscreen"""
    # fix the grid to fill the window
    num_rows = window.grid_size()[1]  # maximise rows
    for r in range(num_rows):
        window.grid_rowconfigure(r, weight=1)
    num_cols = window.grid_size()[0]  # maximise cols
    for c in range(num_cols):
        window.grid_columnconfigure(c, weight=1)


def fix_window_after_its_creation(window):
    """Perform some quality of life things after creating a window (root or Toplevel)"""
    window.attributes("-topmost", True)
    window.focus_set()
    window.after(100, lambda: window.attributes("-topmost", False))  # 100 ms


def configure_the_icon(root):
    """Configure the icon - in macos it changes the dock icon, in windows it changes
    all windows titlebar icons (taskbar cannot be changed without converting to exe)
    """
    if platform.system().startswith("Darwin"):
        try:
            from Cocoa import NSApplication, NSImage
        except ImportError:
            print("Unable to import pyobjc modules")
        else:
            with resources.path("autogaita", "autogaita_icon.icns") as icon_path:
                ns_application = NSApplication.sharedApplication()
                logo_ns_image = NSImage.alloc().initByReferencingFile_(str(icon_path))
                ns_application.setApplicationIconImage_(logo_ns_image)
    elif platform.system().startswith("win"):
        with resources.path("autogaita", "autogaita_icon.ico") as icon_path:
            root.iconbitmap(str(icon_path))


def get_results_and_cfg(results, cfg, analysis):
    """Before calling analysis, use .get() to extract values from tk-vars"""
    # 1) We make sure to return and use for all "run"-purposes (i.e. everything
    #    that follows this local function) "this_" dicts (stuff is dangerous
    #    otherwise!)
    # 2) I implemented the usage & transformation of FLOAT_&INT_VARS the way I
    #    do here (instead of initialising as (e.g.) tk.IntVar because otherwise
    #    tkinter complains whenever an Entry is empty @ any time, just because
    #    the user is inputting their values.
    output_dicts = [{}, {}]
    for i in range(len(output_dicts)):
        if i == 0:
            input_dict = results
        elif i == 1:
            input_dict = cfg
        for key in input_dict.keys():
            # exclude mouse_num and run_num from int conversion
            # in case analysis is multi
            if analysis == "multi" and (key == "mouse_num" or key == "run_num"):
                output_dicts[i][key] = input_dict[key].get()
            elif key in FLOAT_VARS:
                # make sure that if user doesn't want to convert then we just use 0 so
                # the float() statement doesn't throw an error
                # => set the outer dict directly instead of modulating the input_dict,
                #    since that would also modify cfg which might be dangerous for
                #    future runs
                if (key == "pixel_to_mm_ratio") & (cfg["convert_to_mm"].get() is False):
                    output_dicts[i][key] = 0
                else:
                    try:
                        output_dicts[i][key] = float(input_dict[key].get())
                    except ValueError:
                        return (
                            key
                            + " value was not a decimal number, but "
                            + input_dict[key].get()
                        )
            elif key in INT_VARS:
                try:
                    output_dicts[i][key] = int(input_dict[key].get())
                except ValueError:
                    return (
                        key
                        + " value was not an integer number, but "
                        + input_dict[key].get()
                    )
            elif key in LIST_VARS:
                # if list of strings, initialise output empty list and get & append vals
                output_dicts[i][key] = []
                for list_idx in range(len(input_dict[key])):
                    output_dicts[i][key].append(input_dict[key][list_idx].get())
            elif key in DICT_VARS:
                # if dict of list of strings, initialise as empty dict and assign stuff
                # key = "angles" or other DICT_VAR
                # inner_key = "name" & "lower_ / upper_joint"
                # list_idx = idx of list of strings of inner_key
                output_dicts[i][key] = {}
                for inner_key in input_dict[key]:
                    output_dicts[i][key][inner_key] = []
                    for list_idx in range(len(input_dict[key][inner_key])):
                        output_dicts[i][key][inner_key].append(
                            input_dict[key][inner_key][list_idx].get()
                        )
            else:
                output_dicts[i][key] = input_dict[key].get()
    this_runs_results = output_dicts[0]
    this_runs_cfg = output_dicts[1]
    return this_runs_results, this_runs_cfg


def prepare_folderinfo(this_runs_results):
    # IMPORTANT NOTE
    # This function should only return None if there are issues with root_dir
    # since we handle the error in outside functions because of this (i.e. the meaning
    # behind the None should NOT change in the future!)
    if len(this_runs_results["root_dir"]) == 0:
        return
    folderinfo = {}
    folderinfo["root_dir"] = this_runs_results["root_dir"]
    # to make sure root_dir works under windows
    # (windows is okay with all dir-separators being "/", so make sure it is!)
    folderinfo["root_dir"] = folderinfo["root_dir"].replace(os.sep, "/")
    if folderinfo["root_dir"][-1] != "/":
        folderinfo["root_dir"] = folderinfo["root_dir"] + "/"
    if not os.path.exists(folderinfo["root_dir"]):
        return
    folderinfo["sctable_filename"] = this_runs_results["sctable_filename"]
    folderinfo["data_string"] = this_runs_results["data_string"]
    folderinfo["beam_string"] = this_runs_results["beam_string"]
    folderinfo["premouse_string"] = this_runs_results["premouse_string"]
    folderinfo["postmouse_string"] = this_runs_results["postmouse_string"]
    folderinfo["prerun_string"] = this_runs_results["prerun_string"]
    folderinfo["postrun_string"] = this_runs_results["postrun_string"]
    return folderinfo


def extract_info(folderinfo):
    """Prepare a dict of lists that include unique name/mouse/run infos"""
    info = {"name": [], "mouse_num": [], "run_num": []}
    postrun_string = folderinfo["postrun_string"]
    for filename in os.listdir(folderinfo["root_dir"]):
        # make sure we don't get wrong files
        if (
            (folderinfo["premouse_string"] in filename)
            & (folderinfo["prerun_string"] in filename)
            & (filename.endswith(".csv"))
        ):
            # ID number - fill in "_" for user if needed & throw error & stop if issues
            this_mouse_num = False
            for candidate_postmouse_string in [
                folderinfo["postmouse_string"],
                "_" + folderinfo["postmouse_string"],
            ]:
                try:
                    this_mouse_num = find_number(
                        filename,
                        folderinfo["premouse_string"],
                        candidate_postmouse_string,
                    )
                except:
                    pass
            if this_mouse_num is False:
                no_ID_num_found_msg = (
                    "Unable to extract ID numbers from file identifiers! "
                    + "Check unique subject [B] and unique task [C] identifiers"
                )
                tk.messagebox.showerror(
                    title="No ID number found!", message=no_ID_num_found_msg
                )
                return
            # Do the same for run number
            this_run_num = False
            for candidate_postrun_string in [
                folderinfo["postrun_string"],
                "-" + folderinfo["postrun_string"],
            ]:
                try:
                    this_run_num = find_number(
                        filename, folderinfo["prerun_string"], candidate_postrun_string
                    )
                except:
                    pass
            if this_run_num is False:
                no_run_num_found_msg = (
                    "Unable to extract trial numbers from file identifiers! "
                    + "Check unique trial [D] and unique camera [E] identifiers"
                )
                tk.messagebox.showerror(
                    title="No Trial number found!", message=no_ID_num_found_msg
                )
                return
            # if we found both an ID and a run number, create this_name & add to dict
            this_name = "ID " + str(this_mouse_num) + " - Run " + str(this_run_num)
            if this_name not in info["name"]:  # no data/beam duplicates here
                info["name"].append(this_name)
                info["mouse_num"].append(this_mouse_num)
                info["run_num"].append(this_run_num)
    return info


def find_number(fullstring, prestring, poststring):
    """Find (mouse/run) number based on user-defined strings in filenames"""
    start_idx = fullstring.find(prestring) + len(prestring)
    end_idx = fullstring.find(poststring)
    return int(fullstring[start_idx:end_idx])


def update_config_file(results, cfg):
    """updates the dlc_gui_config file with this runs parameters"""
    # transform tkVars into normal strings and bools
    output_dicts = [{}, {}]
    for i in range(len(output_dicts)):
        if i == 0:
            # in case update_config_file is called before results is defined
            # as in the creation of the close_button in the dlc_gui() function
            # the results dict of the last run is used and only cfg is updated
            if results == "results dict not defined yet":
                # runwindow = None as we dont need the tk.Vars to refer to a specific window
                input_dict = extract_results_from_json_file(runwindow=None)
            else:
                input_dict = results
        elif i == 1:
            input_dict = cfg
        for key in input_dict.keys():
            if key in LIST_VARS:
                # if list of strings, initialise output empty list and get & append vals
                output_dicts[i][key] = []
                for list_idx in range(len(input_dict[key])):
                    output_dicts[i][key].append(input_dict[key][list_idx].get())
            elif key in DICT_VARS:
                # if dict of list of strings, initialise as empty dict and assign stuff
                # key = "angles" or other DICT_VAR
                # inner_key = "name" & "lower_ / upper_joint"
                # list_idx = idx of list of strings of inner_key
                output_dicts[i][key] = {}
                for inner_key in input_dict[key]:
                    output_dicts[i][key][inner_key] = []
                    for list_idx in range(len(input_dict[key][inner_key])):
                        output_dicts[i][key][inner_key].append(
                            input_dict[key][inner_key][list_idx].get()
                        )
            else:
                output_dicts[i][key] = input_dict[key].get()

    # merge the two configuration dictionaries
    configs_list = [output_dicts[0], output_dicts[1]]  # 0 = results, 1 = cfg, see above
    # write the configuration file
    with open(
        os.path.join(AUTOGAITA_FOLDER_PATH, CONFIG_FILE_NAME), "w"
    ) as config_json_file:
        json.dump(configs_list, config_json_file, indent=4)


def extract_cfg_from_json_file(root):
    """loads the cfg dictionary from the config file"""
    # load the configuration file
    with open(
        os.path.join(AUTOGAITA_FOLDER_PATH, CONFIG_FILE_NAME), "r"
    ) as config_json_file:
        # config_json contains list with 0 -> result and 1 -> cfg data
        last_runs_cfg = json.load(config_json_file)[1]

    cfg = {}
    # assign values to the cfg dict
    for key in last_runs_cfg.keys():
        if key in TK_BOOL_VARS:
            cfg[key] = tk.BooleanVar(root, last_runs_cfg[key])
        elif key in LIST_VARS:
            cfg[key] = []
            for entry in last_runs_cfg[key]:
                cfg[key].append(tk.StringVar(root, entry))
        elif key in DICT_VARS:
            cfg[key] = {}
            for subkey in last_runs_cfg[key]:
                cfg[key][subkey] = []
                for entry in last_runs_cfg[key][subkey]:
                    cfg[key][subkey].append(tk.StringVar(root, entry))
        elif key in TK_STR_VARS:  # Integers are also saved as strings
            cfg[key] = tk.StringVar(root, last_runs_cfg[key])
    return cfg


def extract_results_from_json_file(runwindow):
    """loads the results dictionary from the config file"""

    # load the configuration file
    with open(
        os.path.join(AUTOGAITA_FOLDER_PATH, CONFIG_FILE_NAME), "r"
    ) as config_json_file:
        # config_json contains list with 0 -> result and 1 -> cfg data
        last_runs_results = json.load(config_json_file)[0]

    results = {}
    for key in last_runs_results.keys():
        results[key] = tk.StringVar(runwindow, last_runs_results[key])

    return results


# %% what happens if we hit run
if __name__ == "__main__":
    dlc_gui()

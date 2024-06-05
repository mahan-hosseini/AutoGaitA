# %% imports
from autogaita import autogaita_utils
import tkinter as tk
import customtkinter as ctk
import os
from threading import Thread
from importlib import resources
import platform
import json


# %% global constants
FG_COLOR = "#789b73"  # grey green
HEADER_TXT_COLOR = "#ffffff"  # white
HEADER_FONT_SIZE = 20
HOVER_COLOR = "#287c37"  # darkish green
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
    "normalise_height_at_SC_level",
    "invert_y_axis",
    "flip_gait_direction",
    "export_average_x",
]
TK_STR_VARS = [
    "sampling_rate",
    "pixel_to_mm_ratio",
    "x_sc_broken_threshold",
    "y_sc_broken_threshold",
    "bin_num",
    "plot_joint_number",
    "results_dir",
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
    root.geometry(f"{screen_width}x{screen_height}+0+0")
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

    # ..........................................................................
    # ........................  root window population .........................
    # ..........................................................................
    # initialise default cfg vars
    # ==> see a note @ get_results_and_cfg helper function about why I
    #     initialise all vars that are not Boolean as Strings!
    # if you are looking for the initialisation of the results dict, that is at the top
    # of POPULATE_RUN_WINDOW local function

    global cfg
    # .....................  load cfg dict from config .....................
    # use the values in the config json file for the results dictionary
    cfg = extract_cfg_from_json_file(root)

    # .........................  top section  ..................................
    # welcome message
    welcomestring = "Welcome to AutoGaitA DLC! Please read info below " + "carefully."
    welcomeheader_label = ctk.CTkLabel(
        root,
        text=welcomestring,
        width=w,
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
    welcomeheader_label.grid(row=0, column=0, columnspan=2, sticky="nsew")
    # info message
    introstring = (
        "This program analyses kinematics after tracking with DeepLabCut."
        + "\n\nFor this, it requires: "
        + "\n1) DLC-generated CSV file of joint (i.e., key point) coordinates "
        + "(optional: corresponding video files)."
        + "\n2) A (group-level) Annotation Table Excel file (see documentation)"
        + "\n3) Optional: corresponding CSV file & video of tracked height baseline."
        + "\nPlease place all these files into a single folder "
        + "(filenames between CSVs and videos have to match)."
        + "\n\nTo use program: \n1) Enter main configuration info below."
        + "\n2) Use bottom left button for advanced configuration (including custom "
        + "joint/key point names & angle definitions) if desired."
        + "\n3) Use bottom right buttons to analyse one video or multiple videos at "
        + "once."
    )
    textbox_label = ctk.CTkLabel(
        root, text=introstring, width=w, fg_color="transparent"
    )
    textbox_label.grid(row=1, column=0, rowspan=2, columnspan=2, sticky="nsew", pady=10)
    # config header
    cfgheader_label = ctk.CTkLabel(
        root,
        text="Main Configuration",
        width=w,
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
    cfgheader_label.grid(row=3, column=0, columnspan=2, rowspan=1, sticky="nsew")

    # .........................  left section  .................................
    # sampling rate
    samprate_label = ctk.CTkLabel(
        root, text="Insert sampling rate of videos (frames/second)"
    )
    samprate_label.grid(row=4, column=0)
    samprate_entry = ctk.CTkEntry(root, textvariable=cfg["sampling_rate"])
    samprate_entry.grid(row=5, column=0)
    # subtract beam
    subtract_beam_string = "Normalise y-coordinates to baseline height"
    subtract_beam_checkbox = ctk.CTkCheckBox(
        root,
        text=subtract_beam_string,
        variable=cfg["subtract_beam"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
    )
    subtract_beam_checkbox.grid(row=6, column=0)
    # plot plots to python
    showplots_string = "Don't show plots in Python (save only)"
    showplots_checkbox = ctk.CTkCheckBox(
        root,
        text=showplots_string,
        variable=cfg["dont_show_plots"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
    )
    showplots_checkbox.grid(row=7, column=0)
    # advanced cfg
    cfg_window_label = ctk.CTkLabel(
        root,
        text="Advanced Configuration & Exit",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
    cfg_window_label.grid(row=8, column=0, sticky="nsew")
    cfg_window_button = ctk.CTkButton(
        root,
        text="Advanced cfg",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: (advanced_cfg_window(cfg)),
    )
    cfg_window_button.grid(row=9, column=0, pady=(15, 5), padx=30, sticky="nsew")
    close_button = ctk.CTkButton(
        root,
        text="I am done - close program",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: (
            # results variable is only defined later in populate_run_window()
            # therefore only cfg settings will be updated
            update_config_file("results dict not defined yet", cfg),
            root.after(1, root.destroy()),
        ),
    )
    close_button.grid(row=10, column=0, pady=(10, 15), padx=30, sticky="nsew")

    # .........................  right section  ................................
    # Note: convert_checkbox also modifies the state of ratio_entry's state
    #       (which starts with being disabled), so users can only change
    #       pixel_to_mm ratio value when they want the conversion in the first
    #       place
    #       ==> AutoGaitA only uses pixel_to_mm when converting, so when we
    #           are not converting we can just leave the value at whatever
    #           value (e.g., the initialised 0))
    # convert pixel to mm
    convert_string = "Convert x & y values to millimeters"
    convert_checkbox = ctk.CTkCheckBox(
        root,
        text=convert_string,
        variable=cfg["convert_to_mm"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        command=lambda: change_ratio_entry_state(ratio_entry, cfg),
    )
    convert_checkbox.grid(row=4, column=1, rowspan=2)
    ratio_string = "Only needed if converting: How many pixels equal a millimeter?"
    ratio_label = ctk.CTkLabel(root, text=ratio_string)
    ratio_label.grid(row=5, column=1)
    ratio_entry = ctk.CTkEntry(
        root, textvariable=cfg["pixel_to_mm_ratio"], state="disabled"
    )
    ratio_entry.grid(row=6, column=1, pady=4)
    # run analysis buttons
    runheader_label = ctk.CTkLabel(
        root,
        text="Run Analysis",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
    runheader_label.grid(row=8, column=1, sticky="nsew")
    onevid_button = ctk.CTkButton(
        root,
        text="One Video",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: run_window(cfg, "single"),
    )
    onevid_button.grid(row=9, column=1, pady=(15, 5), padx=30, sticky="nsew")
    multivid_button = ctk.CTkButton(
        root,
        text="Multiple Videos",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: run_window(cfg, "multi"),
    )
    multivid_button.grid(row=10, column=1, pady=(10, 15), padx=30, sticky="nsew")

    # maximise widgets
    maximise_widgets(root)

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
    cfg_w = w * (1 / 3)
    cfg_h = h * (1 / 1.5)
    cfg_x = ((1 / 2) * w) - (1 / 2 * cfg_w)
    cfg_y = ((1 / 2) * h) - (1 / 2 * cfg_h)
    cfg_window.geometry("%dx%d+%d+%d" % (cfg_w, cfg_h, cfg_x, cfg_y))
    fix_window_after_its_creation(cfg_window)

    # enter info - cfg vars are global!
    x_threshold_string = (
        "What x-criterion (in pixels) to use for rejecting step cycles?"
    )
    x_thresh_label = ctk.CTkLabel(cfg_window, text=x_threshold_string, width=cfg_w)
    x_thresh_label.grid(row=0, column=0)
    x_thresh_entry = ctk.CTkEntry(cfg_window, textvariable=cfg["x_sc_broken_threshold"])
    x_thresh_entry.grid(row=1, column=0)
    # y threshold for rejecting SCs
    y_threshold_string = (
        "What y-criterion (in pixels) to use for rejecting step cycles?"
    )
    y_thresh_label = ctk.CTkLabel(cfg_window, text=y_threshold_string, width=cfg_w)
    y_thresh_label.grid(row=2, column=0)
    y_thresh_entry = ctk.CTkEntry(cfg_window, textvariable=cfg["y_sc_broken_threshold"])
    y_thresh_entry.grid(row=3, column=0)
    # x acceleration
    x_accel_string = "Compute, plot & export joints' x-accelerations"
    x_accel_box = ctk.CTkCheckBox(
        cfg_window,
        text=x_accel_string,
        variable=cfg["x_acceleration"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
    )
    x_accel_box.grid(row=4, column=0)
    # angular acceleration
    angular_accel_string = "Compute, plot & export angular accelerations"
    angular_accel_box = ctk.CTkCheckBox(
        cfg_window,
        text=angular_accel_string,
        variable=cfg["angular_acceleration"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
    )
    angular_accel_box.grid(row=5, column=0)
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
    )
    save_to_xls_box.grid(row=6, column=0)
    # bin number of SC normalisation
    bin_num_string = "Number of bins to use for normalising the step cycle"
    bin_num_label = ctk.CTkLabel(cfg_window, text=bin_num_string, width=cfg_w)
    bin_num_label.grid(row=7, column=0)
    bin_num_entry = ctk.CTkEntry(cfg_window, textvariable=cfg["bin_num"])
    bin_num_entry.grid(row=8, column=0)
    # number of hindlimb joints to plot
    plot_joint_num_string = "Number of hindlimb joints to plot in detail"
    plot_joint_num__label = ctk.CTkLabel(
        cfg_window, text=plot_joint_num_string, width=cfg_w
    )
    plot_joint_num__label.grid(row=9, column=0)
    plot_joint_num_entry = ctk.CTkEntry(
        cfg_window, textvariable=cfg["plot_joint_number"]
    )
    plot_joint_num_entry.grid(row=10, column=0)
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
    )
    plot_SE_box.grid(row=11, column=0)
    # height normalisation at each step cycle separately
    height_normalisation_string = "Normalise height of all step cycles separately"
    height_normalisation_box = ctk.CTkCheckBox(
        cfg_window,
        text=height_normalisation_string,
        variable=cfg["normalise_height_at_SC_level"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
    )
    height_normalisation_box.grid(row=12, column=0)
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
    )
    invert_y_axis_box.grid(row=13, column=0)
    # flip gait direction
    flip_gait_direction_string = "Adjust x-coordinates to follow direction of movement"
    flip_gait_direction_box = ctk.CTkCheckBox(
        cfg_window,
        text=flip_gait_direction_string,
        variable=cfg["flip_gait_direction"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
    )
    flip_gait_direction_box.grid(row=14, column=0)
    # export average x coordinates
    export_average_x_string = (
        "Export x-coordinate averages (include in Average Stepcycles.xlsx)"
    )
    export_average_x_box = ctk.CTkCheckBox(
        cfg_window,
        text=export_average_x_string,
        variable=cfg["export_average_x"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
    )
    export_average_x_box.grid(row=15, column=0)
    # results dir
    results_dir_string = (
        "Save Results subfolders to directory location below instead of to data's"
    )
    results_dir_label = ctk.CTkLabel(cfg_window, text=results_dir_string, width=cfg_w)
    results_dir_label.grid(row=16, column=0)
    results_dir_entry = ctk.CTkEntry(cfg_window, textvariable=cfg["results_dir"])
    results_dir_entry.grid(row=17, column=0)
    # column name information window
    column_info_string = "Customise joints and angles"
    column_info_button = ctk.CTkButton(
        cfg_window,
        text=column_info_string,
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: build_column_info_window(root, cfg, root_dimensions),
    )
    column_info_button.grid(
        row=18, column=0, rowspan=2, sticky="nsew", padx=10, pady=(10, 5)
    )
    # done button
    adv_cfg_done_button = ctk.CTkButton(
        cfg_window,
        text="I am done, update cfg.",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: cfg_window.destroy(),
    )
    adv_cfg_done_button.grid(
        row=20, column=0, rowspan=2, sticky="nsew", padx=10, pady=(10, 5)
    )
    # maximise widgets
    maximise_widgets(cfg_window)


# %%..............  LOCAL FUNCTION(S) #2 - BUILD COLUMN INFO WINDOW  ...................
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
                label_string = "Hindlimb Joint #" + str(len(cfg[key]))
            elif key == "fore_joints":
                label_string = "Forelimb Joint #" + str(len(cfg[key]))
            elif key == "beam_hind_jointadd":
                label_string = "Hindlimb Beamsubtraction Joint #" + str(len(cfg[key]))
            elif key == "beam_fore_jointadd":
                label_string = "Forelimb Beamsubtraction Joint #" + str(len(cfg[key]))
            label = ctk.CTkLabel(window, text=label_string)
            label.grid(row=nrows + 1, column=0, sticky="ew")
            entry = ctk.CTkEntry(window, textvariable=cfg[key][-1])
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
                    window, text=this_case + " #" + str(len(cfg[key][angle_key]))
                )
                label.grid(row=nrows + 1, column=angle_column + a, sticky="ew")
                entry = ctk.CTkEntry(window, textvariable=cfg[key][angle_key][-1])
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
            text="Left Beam Column",
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=("Britannic Bold", HEADER_FONT_SIZE),
        )
        beam_left_label.grid(row=0, column=0, sticky="nsew")
        # left beam entry
        beam_left_entry = ctk.CTkEntry(beamwindow, textvariable=cfg["beam_col_left"][0])
        beam_left_entry.grid(row=1, column=0)
        # important: cfg key for forelimb joint add
        hindlimb_key = "beam_hind_jointadd"
        # hindlimb jointadd label
        hind_jointsubtract_label = ctk.CTkLabel(
            beamwindow,
            text="Hindlimb Joints subtracted from Left Beam",
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=("Britannic Bold", HEADER_FONT_SIZE),
        )
        hind_jointsubtract_label.grid(row=2, column=0, sticky="nsew")
        # initialise scrollable frame for beamsubtract windows
        hind_jointsubtract_frame = ctk.CTkScrollableFrame(beamwindow)
        hind_jointsubtract_frame.grid(
            row=3,
            column=0,
            rowspan=beam_scrollable_rows,
            sticky="nsew",
        )
        # initialise labels & entries
        initialise_labels_and_entries(
            hind_jointsubtract_frame,
            hindlimb_key,
            "Hindlimb Beamsubtraction Joint",
        )
        # add button
        add_hindjoint_button = ctk.CTkButton(
            beamwindow,
            text="Add Hindlimb Beamsubtraction Joint",
            fg_color=FG_COLOR,
            hover_color=HOVER_COLOR,
            command=lambda: add_joint(
                hind_jointsubtract_frame, hindlimb_key
            ),  # input = cfg's key
        )
        add_hindjoint_button.grid(
            row=3 + beam_scrollable_rows,
            column=0,
            sticky="nsew",
            padx=left_padx,
            pady=20,
        )
        # .................. right section - right beam / fore joints ..................
        # right beam label
        beam_right_label = ctk.CTkLabel(
            beamwindow,
            text="Right Beam Column",
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=("Britannic Bold", HEADER_FONT_SIZE),
        )
        beam_right_label.grid(row=0, column=1, sticky="nsew")
        # right beam entry
        beam_right_entry = ctk.CTkEntry(
            beamwindow, textvariable=cfg["beam_col_right"][0]
        )
        beam_right_entry.grid(row=1, column=1)
        # important: cfg key for forelimb joint add
        forelimb_key = "beam_fore_jointadd"
        # hindlimb jointadd label
        fore_jointsubtract_label = ctk.CTkLabel(
            beamwindow,
            text="Forelimb Joints subtracted from Right Beam",
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=("Britannic Bold", HEADER_FONT_SIZE),
        )
        fore_jointsubtract_label.grid(row=2, column=1, sticky="nsew")
        # initialise scrollable frame for beamsubtract windows
        fore_jointsubtract_frame = ctk.CTkScrollableFrame(beamwindow)
        fore_jointsubtract_frame.grid(
            row=3,
            column=1,
            rowspan=beam_scrollable_rows,
            sticky="nsew",
        )
        # initialise labels & entries
        initialise_labels_and_entries(
            fore_jointsubtract_frame,
            forelimb_key,
            "Forelimb Beamsubtraction Joint",
        )
        # add button
        add_forejoint_button = ctk.CTkButton(
            beamwindow,
            text="Add Forelimb Beamsubtraction Joint",
            fg_color=FG_COLOR,
            hover_color=HOVER_COLOR,
            command=lambda: add_joint(
                fore_jointsubtract_frame, forelimb_key
            ),  # input = cfg's key
        )
        add_forejoint_button.grid(
            row=3 + beam_scrollable_rows,
            column=1,
            sticky="nsew",
            padx=right_padx,
            pady=20,
        )
        # .................... bottom section - update & close  ........................
        # done button
        beam_done_button = ctk.CTkButton(
            beamwindow,
            text="I am done, update cfg!",
            fg_color=FG_COLOR,
            hover_color=HOVER_COLOR,
            command=lambda: beamwindow.destroy(),
        )
        beam_done_button.grid(
            row=4 + beam_scrollable_rows,
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
        text="Hindlimb Joints",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
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
    initialise_labels_and_entries(hindlimb_frame, "hind_joints", "Hindlimb Joint ")
    # add joint button
    add_hind_joint_button = ctk.CTkButton(
        columnwindow,
        text="Add hindlimb joint",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: add_joint(
            hindlimb_frame, "hind_joints"
        ),  # 2nd input = cfg's key
    )
    add_hind_joint_button.grid(
        row=2 + scrollable_rows, column=hind_column, sticky="nsew", padx=5, pady=(10, 5)
    )
    # beam config window label
    beam_window_label = ctk.CTkLabel(
        columnwindow,
        text="Baseline (Beam) Configuration",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
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
        text="Configure Beam Columns and Beamsubtraction Joints",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
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
        text="Forelimb Joints",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
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
        "Forelimb Joint ",
    )
    # add joint button
    add_fore_joint_button = ctk.CTkButton(
        columnwindow,
        text="Add forelimb joint",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
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
        font=("Britannic Bold", HEADER_FONT_SIZE),
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
        text="Add angle",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
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
    done_label = ctk.CTkLabel(
        columnwindow,
        text="Update Configuration",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
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
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
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
            window, text=which_case_string + " #" + str(j + 1)
        )
        joint_labels[j].grid(row=row_counter, column=column_number, sticky="ew")
        row_counter += 1
        if type(key) is str:
            joint_entries[j] = ctk.CTkEntry(window, textvariable=cfg[key][j])
        elif type(key) is list:
            joint_entries[j] = ctk.CTkEntry(window, textvariable=cfg[key[0]][key[1]][j])
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
        runwindow.title("Multi GaitA")
    runwindow.geometry("%dx%d+%d+%d" % root_dimensions)
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
    donewindow_w = w * (1 / 2)
    donewindow_h = h * (1 / 5)
    donewindow_x = w * (1 / 4)
    donewindow_y = h * (1 / 2.5)
    donewindow.geometry(
        "%dx%d+%d+%d" % (donewindow_w, donewindow_h, donewindow_x, donewindow_y)
    )
    fix_window_after_its_creation(donewindow)

    # labels
    done_label1_string = "Your results will be saved in a subfolder of your directory"
    done_label1 = ctk.CTkLabel(donewindow, text=done_label1_string, width=donewindow_w)
    done_label1.grid(row=0, column=0)
    done_label2_string = (
        "Please see the Python command window for progress "
        + "and the plots panel for an overview of all plots."
    )
    done_label2 = ctk.CTkLabel(donewindow, text=done_label2_string, width=donewindow_w)
    done_label2.grid(row=1, column=0)
    done_label3_string = (
        "You may start another analysis while we are "
        + "processing - however your PC might slow down a bit. "
    )
    done_label3 = ctk.CTkLabel(donewindow, text=done_label3_string, width=donewindow_w)
    done_label3.grid(row=2, column=0)
    done_label4_string = (
        "Thank you for using AutoGaitA! Feel free to "
        + "email me about bugs/feedback at autogaita@fz-juelich.de - MH."
    )
    done_label4 = ctk.CTkLabel(donewindow, text=done_label4_string, width=donewindow_w)
    done_label4.grid(row=3, column=0)
    # run button
    done_button = ctk.CTkButton(
        donewindow,
        text="Run!",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: (
            runanalysis(this_runs_results, this_runs_cfg, analysis),
            donewindow.destroy(),
        ),
    )
    done_button.grid(row=4, column=0, sticky="nsew", pady=10, padx=20)
    # maximise button only
    donewindow.grid_rowconfigure(4, weight=1)


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
        mousenum_label = ctk.CTkLabel(runwindow, text=mousenum_string)
        mousenum_label.grid(row=0, column=0)
        mousenum_entry = ctk.CTkEntry(runwindow, textvariable=results["mouse_num"])
        mousenum_entry.grid(row=1, column=0)
        # run number
        runnum_string = "What is the number of the trial?"
        runnum_label = ctk.CTkLabel(runwindow, text=runnum_string)
        runnum_label.grid(row=2, column=0)
        runnum_entry = ctk.CTkEntry(runwindow, textvariable=results["run_num"])
        runnum_entry.grid(row=3, column=0)
    # how we index rows from here upon depends on current analysis
    if analysis == "single":
        r = 4
    else:
        r = 0
    # root directory
    rootdir_string = "Directory location of the folder containing the files to analyse"
    rootdir_label = ctk.CTkLabel(runwindow, text=rootdir_string, width=runwindow_w)
    rootdir_label.grid(row=r + 0, column=0)
    rootdir_entry = ctk.CTkEntry(runwindow, textvariable=results["root_dir"])
    rootdir_entry.grid(row=r + 1, column=0)
    # stepcycle latency XLS
    SCXLS_string = "Name of the Annotation Table Excel file"
    SCXLS_label = ctk.CTkLabel(runwindow, text=SCXLS_string, width=runwindow_w)
    SCXLS_label.grid(row=r + 2, column=0)
    SCXLS_entry = ctk.CTkEntry(runwindow, textvariable=results["sctable_filename"])
    SCXLS_entry.grid(row=r + 3, column=0)
    # file naming convention label
    name_convention_string = (
        "According to [A]_[B]_[C]_[D]-[E][G] filename convention "
        + "(e.g. C57B6_Mouse10_25mm_Run1-6DLC-JointTracking):"
    )
    name_convention_label = ctk.CTkLabel(
        runwindow, text=name_convention_string, width=runwindow_w
    )
    name_convention_label.grid(row=r + 4, column=0)
    # data string
    data_string = "[G] What is the identifier of the DLC-tracked coordinate file?"
    data_label = ctk.CTkLabel(runwindow, text=data_string, width=runwindow_w)
    data_label.grid(row=r + 5, column=0)
    data_entry = ctk.CTkEntry(runwindow, textvariable=results["data_string"])
    data_entry.grid(row=r + 6, column=0)
    # beam string
    beam_string = (
        "[G] What is the identifier of the DLC-tracked baseline file? (optional)"
    )
    beam_label = ctk.CTkLabel(runwindow, text=beam_string, width=runwindow_w)
    beam_label.grid(row=r + 7, column=0)
    beam_entry = ctk.CTkEntry(runwindow, textvariable=results["beam_string"])
    beam_entry.grid(row=r + 8, column=0)
    # premouse_num string
    premouse_string = "[B] Define the 'unique subject identifier' preceding the number"
    premouse_label = ctk.CTkLabel(runwindow, text=premouse_string, width=runwindow_w)
    premouse_label.grid(row=r + 9, column=0)
    premouse_entry = ctk.CTkEntry(runwindow, textvariable=results["premouse_string"])
    premouse_entry.grid(row=r + 10, column=0)
    # postmouse_num string
    postmouse_string = "[C] Define the 'unique task identifier"
    postmouse_label = ctk.CTkLabel(runwindow, text=postmouse_string, width=runwindow_w)
    postmouse_label.grid(row=r + 11, column=0)
    postmouse_entry = ctk.CTkEntry(runwindow, textvariable=results["postmouse_string"])
    postmouse_entry.grid(row=r + 12, column=0)
    # prerun string
    prerun_string = "[D] Define the 'unique trial identifier"
    prerun_label = ctk.CTkLabel(runwindow, text=prerun_string, width=runwindow_w)
    prerun_label.grid(row=r + 13, column=0)
    prerun_entry = ctk.CTkEntry(runwindow, textvariable=results["prerun_string"])
    prerun_entry.grid(row=r + 14, column=0)
    # postrun string
    postrun_string = "[E] Define the 'unique camera identifier"
    postrun_label = ctk.CTkLabel(runwindow, text=postrun_string, width=runwindow_w)
    postrun_label.grid(row=r + 15, column=0)
    postrun_entry = ctk.CTkEntry(runwindow, textvariable=results["postrun_string"])
    postrun_entry.grid(row=r + 16, column=0)
    # button confirming being done
    # => change value of user_ready in this call
    finishbutton = ctk.CTkButton(
        runwindow,
        text="I am done, pass the info!",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: (
            update_config_file(results, cfg),
            user_ready.set(1),
        ),
    )
    finishbutton.grid(row=r + 17, column=0, rowspan=2, sticky="nsew", pady=5, padx=70)
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
            folderinfo["root_dir"], this_info["name"]
        )
    # important to only pass this_info to main script here (1 run at a time!)
    autogaita_utils.try_to_run_gaita("DLC", this_info, folderinfo, this_runs_cfg, True)


# %%...............  LOCAL FUNCTION(S) #6 - VARIOUS HELPER FUNCTIONS  ..................


def change_ratio_entry_state(ratio_entry, cfg):
    """Change the state of ratio entry widget based on whether user wants
    to convert pixels to mm or not.
    """
    if cfg["convert_to_mm"].get() == True:
        ratio_entry.configure(state="normal")
    elif cfg["convert_to_mm"].get() == False:
        ratio_entry.configure(state="disabled")


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
    for filename in os.listdir(folderinfo["root_dir"]):
        # make sure we don't get wrong files
        if (
            (folderinfo["premouse_string"] in filename)
            & (folderinfo["prerun_string"] in filename)
            & (filename.endswith(".csv"))
        ):
            # we can use COUNT vars as we do here, since we start @ 0 and do
            # not include the last index (so if counts=2, idx=[0:2]=include
            # 0&1 only!)
            this_mouse_num = find_number(
                filename, folderinfo["premouse_string"], folderinfo["postmouse_string"]
            )
            this_run_num = find_number(
                filename, folderinfo["prerun_string"], folderinfo["postrun_string"]
            )
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

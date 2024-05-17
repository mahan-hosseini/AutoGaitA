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
FG_COLOR = "#c0737a"  # dusty rose
HOVER_COLOR = "#b5485d"  # dark rose
HEADER_TXT_COLOR = "#ffffff"  # white
HEADER_FONT_SIZE = 20
CONFIG_FILE_NAME = "simi_gui_config.json"
INT_VARS = ["sampling_rate", "bin_num", "plot_joint_number"]
LIST_VARS = ["joints"]
DICT_VARS = ["angles"]
# TK_BOOL/STR_VARS are only used for initialising widgets based on cfg file
# (note that numbers are initialised as strings)
TK_BOOL_VARS = [
    "analyse_singlerun",
    "dont_show_plots",
    "y_acceleration",
    "angular_acceleration",
    "plot_SE",
    "normalise_height_at_SC_level",
    "postname_flag",
]
TK_STR_VARS = [
    "sampling_rate",
    "bin_num",
    "plot_joint_number",
    "results_dir",
    "name",
    "root_dir",
    "sctable_filename",
    "postname_string",
]
WINDOWS_TASKBAR_MAXHEIGHT = 72

# To get the path of the autogaita folder I use __file__
# which returns the path of the autogaita_utils module imported above.
# Removing the 18 letter long "autogaita_utils.py" return the folder path
autogaita_utils_path = autogaita_utils.__file__
AUTOGAITA_FOLDER_PATH = autogaita_utils_path[:-18]


# %% An important Note
# I am using a global variable called cfg because I need its info to be shared
# between root and columnconfiguration window. This is not the object-oriented way
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


def simi_gui():
    # ..........................................................................
    # ......................  root window initialisation .......................
    # ..........................................................................
    # Check for config file
    config_file_path = os.path.join(AUTOGAITA_FOLDER_PATH, CONFIG_FILE_NAME)
    if not os.path.isfile(config_file_path):
        config_file_error_msg = (
            "simi_gui_config.json file not found in autogaita folder.\n"
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
    root.title("Simi GaitA")
    fix_window_after_its_creation(root)
    configure_the_icon(root)

    # nested function: run windows
    def donewindow(results, root, root_dimensions):
        """Run and done windows"""
        build_donewindow(results, root, root_dimensions)

    # ..........................................................................
    # ........................  root window population .........................
    # ..........................................................................
    # initialise default cfg vars
    # ==> see a note @ get_results_and_cfg helper function about why I
    #     initialise all vars that are not Boolean as Strings!
    # ==> note that cfg is global because we need to change some of its variables
    #     column configure window
    # ==> the results dict is not global and will be passed from function to function
    #     like proper programmers do it (nice)
    global cfg  # global cfg variable
    global results
    cfg = extract_cfg_from_json_file(root)
    results = extract_results_from_json_file(root)

    # .............................  top section  .......................................
    # welcome message
    welcomestring = "Welcome to AutoGaitA Simi! Please read info below " + "carefully."
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
        "This program analyses kinematics after tracking with Simi Motion."
        + "\n\nFor this, it requires:"
        + "\n1) A data XLS-file of joint (i.e., key point) coordinates per "
        + "animal/subject. \n2) A (group-level) Annotation Table Excel file (see "
        + "documentation)"
        + "\n\nPlease place all these files into a single folder, enter configuration "
        + "(customise joint names & angle definitions if desired) & hit run."
    )
    introheader_label = ctk.CTkLabel(root, text=introstring, width=w)
    introheader_label.grid(row=1, column=0, columnspan=2)

    # ..................................................................................
    # ..........................  main configuration  ...................................
    # ..................................................................................
    # config header
    cfgheader_label = ctk.CTkLabel(
        root,
        text="Main Configuration",
        width=w,
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
    cfgheader_label.grid(row=2, column=0, columnspan=2, sticky="nsew")

    # .............................  left section  ......................................
    # root directory
    rootdir_string = "Directory location of the folder containing the files to analyse"
    rootdir_label = ctk.CTkLabel(root, text=rootdir_string)
    rootdir_label.grid(row=3, column=0)
    rootdir_entry = ctk.CTkEntry(root, textvariable=results["root_dir"])
    rootdir_entry.grid(row=4, column=0)

    # postname info label 1 & 2
    postname_info_label_string_1 = (
        "Files may either be named: 1) ID.xls(x) or 2) ID+STRING.xls(x)"
    )
    postname_info_label_label_1 = ctk.CTkLabel(root, text=postname_info_label_string_1)
    postname_info_label_label_1.grid(row=5, column=0)
    postname_info_label_string_2 = (
        "If 2), the STRING has to be constant across datasets!"
    )
    postname_info_label_label_2 = ctk.CTkLabel(root, text=postname_info_label_string_2)
    postname_info_label_label_2.grid(row=6, column=0)

    # postname present checkbox
    postname_flag_string = "I have a constant string that follows IDs in data files"
    postname_flag_checkbox = ctk.CTkCheckBox(
        root,
        text=postname_flag_string,
        variable=results["postname_flag"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        command=lambda: change_postname_entry_state(postname_entry, results),
    )
    postname_flag_checkbox.grid(row=7, column=0)
    # data string
    postname_string = "The constant string is:"
    postname_label = ctk.CTkLabel(root, text=postname_string)
    postname_label.grid(row=8, column=0)
    postname_entry = ctk.CTkEntry(
        root, textvariable=results["postname_string"], state="disabled"
    )
    postname_entry.grid(row=9, column=0)

    # .............................  right section  .....................................
    # stepcycle latency XLS
    SCXLS_string = "Name of the Annotation Table Excel file"
    SCXLS_label = ctk.CTkLabel(root, text=SCXLS_string)
    SCXLS_label.grid(row=3, column=1)
    SCXLS_entry = ctk.CTkEntry(root, textvariable=results["sctable_filename"])
    SCXLS_entry.grid(row=4, column=1)
    # sampling rate
    samprate_label = ctk.CTkLabel(
        root, text="Insert sampling rate of videos (frames/second)"
    )
    samprate_label.grid(row=5, column=1)
    samprate_entry = ctk.CTkEntry(root, textvariable=cfg["sampling_rate"])
    samprate_entry.grid(row=6, column=1)
    # single video checkbox
    singlevideo_string = "Do you want to only analyse one dataset?"
    singlevideo_checkbox = ctk.CTkCheckBox(
        root,
        text=singlevideo_string,
        variable=cfg["analyse_singlerun"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
        command=lambda: change_ID_entry_state(ID_entry, results),
    )
    singlevideo_checkbox.grid(row=7, column=1)
    # ID string info
    ID_label = ctk.CTkLabel(root, text="If so, what is the animal/subject's ID?")
    ID_label.grid(row=8, column=1)
    ID_entry = ctk.CTkEntry(root, textvariable=results["name"], state="disabled")
    ID_entry.grid(row=9, column=1)

    # ..................................................................................
    # ........................  advanced configuration  ................................
    # ..................................................................................
    # advanced config header
    advanced_cfgheader_label = ctk.CTkLabel(
        root,
        text="Advanced Configuration",
        width=w,
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
    advanced_cfgheader_label.grid(row=10, column=0, columnspan=2, sticky="nsew")

    # .............................  left section  .....................................
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
    showplots_checkbox.grid(row=11, column=0)
    # bin_num
    bin_num_string = "Number of bins to use for normalising the step cycle"
    bin_num_label = ctk.CTkLabel(root, text=bin_num_string)
    bin_num_label.grid(row=12, column=0)
    bin_num_entry = ctk.CTkEntry(root, textvariable=cfg["bin_num"])
    bin_num_entry.grid(row=13, column=0)
    # number of joints to plot
    plot_joint_num_string = "Number of joints to plot in detail"
    plot_joint_num_label = ctk.CTkLabel(root, text=plot_joint_num_string)
    plot_joint_num_label.grid(row=14, column=0)
    plot_joint_num_entry = ctk.CTkEntry(root, textvariable=cfg["plot_joint_number"])
    plot_joint_num_entry.grid(row=15, column=0)
    # results dir
    results_dir_string = (
        "Save Results subfolders to directory location below instead of to data's"
    )
    results_dir_label = ctk.CTkLabel(root, text=results_dir_string)
    results_dir_label.grid(row=16, column=0)
    results_dir_entry = ctk.CTkEntry(root, textvariable=cfg["results_dir"])
    results_dir_entry.grid(row=17, column=0)

    # .............................  right section  ....................................
    # x acceleration
    x_accel_string = "Compute, plot & export joints' y-accelerations"
    x_accel_box = ctk.CTkCheckBox(
        root,
        text=x_accel_string,
        variable=cfg["y_acceleration"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
    )
    x_accel_box.grid(row=11, column=1)
    # angular acceleration
    angular_accel_string = "Compute, plot & export angular accelerations"
    angular_accel_box = ctk.CTkCheckBox(
        root,
        text=angular_accel_string,
        variable=cfg["angular_acceleration"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
    )
    angular_accel_box.grid(row=12, column=1)
    # plot SE
    plot_SE_string = "Use standard error instead of standard deviation for plots"
    plot_SE_box = ctk.CTkCheckBox(
        root,
        text=plot_SE_string,
        variable=cfg["plot_SE"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
    )
    plot_SE_box.grid(row=13, column=1)
    # height normalisation at each step cycle separately
    height_normalisation_string = "Normalise heights of all step cycles separately"
    height_normalisation_box = ctk.CTkCheckBox(
        root,
        text=height_normalisation_string,
        variable=cfg["normalise_height_at_SC_level"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
    )
    height_normalisation_box.grid(row=14, column=1)
    # column name information window
    column_info_string = "Customise joints and angles"
    column_info_button = ctk.CTkButton(
        root,
        text=column_info_string,
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: build_column_info_window(root, cfg, root_dimensions),
    )
    column_info_button.grid(
        row=16, column=1, sticky="nsew", rowspan=2, padx=10, pady=10
    )
    # .........................  run and done section  .................................
    # run button
    runheader_label = ctk.CTkLabel(
        root,
        text="Run Analysis",
        width=w,
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
    runheader_label.grid(row=18, column=0, columnspan=2, sticky="nsew")
    run_button = ctk.CTkButton(
        root,
        text="I am ready - run analysis!",
        command=lambda: (
            update_config_file(results, cfg),
            donewindow(results, root, root_dimensions),
        ),
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
    )
    run_button.grid(row=19, column=0, sticky="nsew", padx=10, pady=(10, 5))
    # close program button
    close_button = ctk.CTkButton(
        root,
        text="I am done - close program",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: (
            update_config_file(results, cfg),
            root.after(1, root.destroy()),
        ),
    )
    close_button.grid(row=19, column=1, sticky="nsew", padx=10, pady=(10, 5))

    # maximise widgets
    maximise_widgets(root)

    # main loop
    root.mainloop()


# %%..............  LOCAL FUNCTION(S) #1 - BUILD COLUMN INFO WINDOW  ...................
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
        if key == "joints":
            label = ctk.CTkLabel(window, text="Joint #" + str(len(cfg[key])))
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

    # ...................  Scrollable Window Configuration  ............................
    scrollable_rows = 8

    # ...................  Column 0: hind limb joint names  ............................
    joint_column = 0
    # header label
    joint_label = ctk.CTkLabel(
        columnwindow,
        text="Joints",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
    joint_label.grid(row=0, column=joint_column, sticky="nsew", pady=(0, 5))
    # initialise scrollable frame for hindlimb
    joint_frame = ctk.CTkScrollableFrame(columnwindow)
    joint_frame.grid(row=1, column=joint_column, rowspan=scrollable_rows, sticky="nsew")
    # initialise labels & entries with hind limb defaults
    initialise_labels_and_entries(joint_frame, "joints", "Joint ")
    # add joint button
    add_joint_button = ctk.CTkButton(
        columnwindow,
        text="Add joint",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: (add_joint(joint_frame, "joints")),  # 2nd input = cfg's key
    )
    add_joint_button.grid(
        row=2 + scrollable_rows,
        column=joint_column,
        sticky="nsew",
        padx=5,
        pady=(10, 5),
    )

    # .........  Column 1: angle names/joint-definitions & done button  ................
    angle_column = 1
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
    # done button
    columncfg_done_button = ctk.CTkButton(
        columnwindow,
        text="I am done, update cfg!",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: (columnwindow.destroy()),
    )
    columncfg_done_button.grid(
        row=3 + scrollable_rows,
        column=joint_column,
        columnspan=4,
        sticky="nsew",
        padx=5,
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


# %%..................  LOCAL FUNCTION(S) #2 - BUILD DONE WINDOW  ......................
def build_donewindow(results, root, root_dimensions):
    """Build done window informing people"""

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
        this_runs_results, this_runs_cfg = get_results_and_cfg(results, cfg)
    except:
        error_msg = get_results_and_cfg(results, cfg)
        tk.messagebox.showerror(title="Try again", message=error_msg)
        return

    # create the window & make it pretty and nice
    w = root_dimensions[0]
    h = root_dimensions[1]
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
            run_analysis(this_runs_results, this_runs_cfg),
            donewindow.destroy(),
        ),
    )
    done_button.grid(row=4, column=0, sticky="nsew", pady=10, padx=20)

    # maximise button only
    donewindow.grid_rowconfigure(4, weight=1)


# %%..........  LOCAL FUNCTION(S) #3 - PREPARE & CALL AUTOGAITA  ....................


def run_analysis(this_runs_results, this_runs_cfg):
    """Run the main program"""
    if this_runs_cfg["analyse_singlerun"]:
        run_thread = Thread(
            target=analyse_single_run, args=(this_runs_results, this_runs_cfg)
        )
    else:
        run_thread = Thread(
            target=analyse_multi_run, args=(this_runs_results, this_runs_cfg)
        )
    run_thread.start()


def analyse_single_run(this_runs_results, this_runs_cfg):
    """Prepare for one execution of autogaita_simi & execute"""
    # prepare
    this_info = {}  # info dict: run-specific info
    this_info["name"] = this_runs_results["name"]
    this_folderinfo = prepare_folderinfo(this_runs_results)
    if this_folderinfo is None:
        error_msg = (
            "No directory found at: " + this_runs_results["root_dir"] + " - try again!"
        )
        tk.messagebox.showerror(title="Try again", message=error_msg)
        print(error_msg)
        return
    if this_runs_cfg["results_dir"]:
        this_info["results_dir"] = os.path.join(
            this_runs_cfg["results_dir"], this_info["name"]
        )
    else:
        this_info["results_dir"] = os.path.join(
            this_runs_results["root_dir"], "Results", this_info["name"]
        )
    # execute
    autogaita_utils.try_to_run_gaita(
        "Simi", this_info, this_folderinfo, this_runs_cfg, False
    )


def analyse_multi_run(this_runs_results, this_runs_cfg):
    """Analyse multiple runs at once - extracts folderinfo and then loops over all names
    of multirun_info
    """
    this_folderinfo = prepare_folderinfo(this_runs_results)
    if this_folderinfo is None:
        error_msg = (
            "No directory found at: " + this_runs_results["root_dir"] + " - try again!"
        )
        tk.messagebox.showerror(title="Try again", message=error_msg)
        print(error_msg)
        return
    multirun_info = multirun_extract_info(this_folderinfo)
    for idx, name in enumerate(multirun_info["name"]):
        multirun_run_a_single_dataset(
            idx, multirun_info, this_folderinfo, this_runs_cfg
        )


def multirun_run_a_single_dataset(idx, multirun_info, this_folderinfo, this_runs_cfg):
    """If we are doing a multi-run analysis, run the main code of individual analyses
    based on current cfg"""
    # extract and pass info of this ID
    this_info = {}
    keynames = multirun_info.keys()
    for keyname in keynames:
        this_info[keyname] = multirun_info[keyname][idx]
    # important to only pass this_info here (1 run at a time - prints error if needed)
    autogaita_utils.try_to_run_gaita(
        "Simi", this_info, this_folderinfo, this_runs_cfg, True
    )


# %%..............  LOCAL FUNCTION(S) #4 - VARIOUS HELPER FUNCTIONS  ...................


def change_ID_entry_state(ID_entry, results):
    """Change the state of ID entry widget based on whether user wants to only analyse
    a single dataset.
    """
    if cfg["analyse_singlerun"].get() == True:
        ID_entry.configure(state="normal")
    elif cfg["analyse_singlerun"].get() == False:
        ID_entry.configure(state="disabled")


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


def change_postname_entry_state(postname_entry, results):
    """Change the state of ID entry widget based on whether user wants to only analyse
    a single dataset.
    """
    if results["postname_flag"].get() == True:
        postname_entry.configure(state="normal")
    elif results["postname_flag"].get() == False:
        postname_entry.configure(state="disabled")


def maximise_widgets(window):
    """Maximises all widgets to look good in fullscreen"""
    # fix the grid to fill the window
    num_rows = window.grid_size()[1]  # maximise rows
    for r in range(num_rows):
        window.grid_rowconfigure(r, weight=1)
    num_cols = window.grid_size()[0]  # maximise cols
    for c in range(num_cols):
        window.grid_columnconfigure(c, weight=1)


def get_results_and_cfg(results, cfg):
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
            if key in INT_VARS:
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
    """Dump all infos about constants in this given folder into a dict"""
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
    if this_runs_results["postname_flag"] is False:
        folderinfo["postname_string"] = ""
    else:
        folderinfo["postname_string"] = this_runs_results["postname_string"]
    return folderinfo


def multirun_extract_info(folderinfo):
    """If we are running multi-run analysis, prepare a dict of lists that include
    unique name & results_dir infos

    A Note
    ------
    There are 3 "results_dirs" here:
    1) cfg["results_dir"] is the user-provided entry
    2) results_dir var is the value extracted from 1)
    3) info["results_dir"] is the dir we save this ID's (!) Results to!
    """

    results_dir = cfg["results_dir"].get()
    info = {"name": [], "results_dir": []}
    for filename in os.listdir(folderinfo["root_dir"]):
        # dont try to combine the two "join" if blocks into one - we want to append
        # results dir WHENEVER we append name!
        if not folderinfo["postname_string"]:
            # dont use endswith below to catch .xlsx too
            if (".xls" in filename) & (folderinfo["sctable_filename"] not in filename):
                info["name"].append(filename.split(".xls")[0])
                if results_dir:
                    info["results_dir"].append(
                        os.path.join(results_dir, info["name"][-1])
                    )
                else:
                    info["results_dir"].append(
                        os.path.join(
                            folderinfo["root_dir"], "Results", info["name"][-1]
                        )
                    )
        else:
            if folderinfo["postname_string"] in filename:
                info["name"].append(filename.split(folderinfo["postname_string"])[0])
                if results_dir:
                    info["results_dir"].append(
                        os.path.join(results_dir, info["name"][-1])
                    )
                else:
                    info["results_dir"].append(
                        os.path.join(
                            folderinfo["root_dir"], "Results", info["name"][-1]
                        )
                    )
    return info


def update_config_file(results, cfg):
    """updates the simi_gui_config file with this runs parameters"""
    # transform tkVars into normal strings and bools
    output_dicts = [{}, {}]
    for i in range(len(output_dicts)):
        if i == 0:
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
        elif key in TK_STR_VARS:
            cfg[key] = tk.StringVar(root, last_runs_cfg[key])
    return cfg


def extract_results_from_json_file(root):
    """loads the results dictionary from the config file"""

    # load the configuration file
    with open(
        os.path.join(AUTOGAITA_FOLDER_PATH, CONFIG_FILE_NAME), "r"
    ) as config_json_file:
        # config_json contains list with 0 -> result and 1 -> cfg data
        last_runs_results = json.load(config_json_file)[0]

    results = {}
    for key in last_runs_results.keys():
        results[key] = tk.StringVar(root, last_runs_results[key])

    return results


# %% what happens if we hit run
if __name__ == "__main__":
    simi_gui()

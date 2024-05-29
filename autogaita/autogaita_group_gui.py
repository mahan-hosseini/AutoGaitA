# %% imports
from autogaita import autogaita_group
import tkinter as tk
import customtkinter as ctk
import pandas as pd
import os
import math
from threading import Thread
from importlib import resources
import platform
import json
import copy


# %% global constants
FG_COLOR = "#5a7d9a"  # steel blue
HOVER_COLOR = "#8ab8fe"  # carolina blue
HEADER_TXT_COLOR = "#ffffff"  # white
HEADER_FONT_SIZE = 20
MIN_GROUP_NUM = 2
MAX_GROUP_NUM = 6
CONFIG_FILE_NAME = "group_gui_config.json"
STRING_VARS = ["group_names", "group_dirs", "results_dir"]
FLOAT_VARS = ["stats_threshold"]
LIST_VARS = [
    "stats_variables",  # stats/PCA variables are also TK_BOOL_VARS but this will be
    "PCA_variables",  #  handled within the ---PCA / STATS FEATURE FRAMES--- part
]
INT_VARS = ["permutation_number", "number_of_PCs", "number_of_PCs"]
# TK_BOOL/STR_VARS are only used for initialising widgets based on cfg file
# (note that numbers are initialised as strings)
TK_BOOL_VARS = ["do_permtest", "do_anova", "save_3D_PCA_video", "plot_SE"]
TK_STR_VARS = [
    "anova_design",
    "permutation_number",
    "stats_threshold",
    "which_leg",
    "results_dir",
]
EXCLUDED_VARS_FROM_CFG_FILE = ["last_runs_stats_variables", "last_runs_PCA_variables"]
NORM_SHEET_NAME = "Normalised Stepcycles"
WINDOWS_TASKBAR_MAXHEIGHT = 72

# To get the path of the autogaita folder I use __file__
# which returns the path of the autogaita_group module imported above.
# Removing the 18 letter long "autogaita_group.py" return the folder path
autogaita_group_path = autogaita_group.__file__
AUTOGAITA_FOLDER_PATH = autogaita_group_path[:-18]


# %%...............................  MAIN PROGRAM ......................................


def group_gui():
    # ..................................................................................
    # .....................  root (intro) window initialisation  .......................
    # ..................................................................................
    # Check for config file
    config_file_path = os.path.join(AUTOGAITA_FOLDER_PATH, CONFIG_FILE_NAME)
    if not os.path.isfile(config_file_path):
        config_file_error_msg = (
            "group_gui_config.json file not found in autogaita folder.\n"
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
    fix_window_after_its_creation(root)
    configure_the_icon(root)

    # prepare screen width / height for later windows
    global screen_width, screen_height
    screen_width = root.winfo_screenwidth()  # width of the screen
    screen_height = root.winfo_screenheight()  # height of the screen
    if platform.system() == "Windows":  # adjust for taskbar in windows only
        screen_height -= WINDOWS_TASKBAR_MAXHEIGHT
    root_w = screen_width / 2  # width for the Tk root
    root_h = screen_height / 4.5  # height for the Tk root
    # calculate x and y coordinates for the Tk root window
    root_x = (screen_width / 2) - (root_w / 2)
    root_y = (screen_height / 2) - (root_h / 1)
    root_dimensions = (root_w, root_h, root_x, root_y)
    # set the dimensions of the screen and where it is placed
    root.geometry("%dx%d+%d+%d" % root_dimensions)
    root.title("Group GaitA")

    # nested function: main window
    def mainwindow(root, group_number, root_dimensions):
        """Main window"""
        build_mainwindow(root, group_number, root_dimensions)

    # ..................................................................................
    # .......................  root (intro) window population  .........................
    # ..................................................................................
    # .......................  important - global cfg variable  ........................
    # we have cfg be global so it can be modified by all widgets and frames. just prior
    # to calling autogaita_group, we will copy its values to a temporary cfg var, so
    # the values of the global variable are never used for running anything
    # (see run_analysis)
    global cfg
    cfg = extract_cfg_from_json_file(root)

    # .................................  widgets  ......................................
    # welcome message
    welcomestring = "Welcome to AutoGaitA Group!"
    welcomeheader_label = ctk.CTkLabel(
        root,
        text=welcomestring,
        width=root_w,
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
    welcomeheader_label.grid(row=0, column=0, columnspan=MAX_GROUP_NUM - 1)
    # contrast number message
    numberstring = "How many groups would you like to compare with each other?"
    numberheader_label = ctk.CTkLabel(
        root,
        text=numberstring,
        width=root_w,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
    numberheader_label.grid(row=1, column=0, columnspan=MAX_GROUP_NUM - 1, pady=(20, 5))
    # number of groups to contrast radio buttons
    group_number = ctk.IntVar(value=0)
    group_buttons = []
    for i in range(MIN_GROUP_NUM, MAX_GROUP_NUM + 1):
        group_buttons.append(
            ctk.CTkRadioButton(
                root,
                text=str(i),
                variable=group_number,
                value=i,
                fg_color=FG_COLOR,
                hover_color=HOVER_COLOR,
                font=("Britannic Bold", HEADER_FONT_SIZE),
            )
        )
        group_buttons[-1].grid(row=2, column=i - MIN_GROUP_NUM)
    # continue button
    continue_button = ctk.CTkButton(
        root,
        text="Continue",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
        command=lambda: (
            mainwindow(root, group_number, root_dimensions),
            root.withdraw(),
        ),
    )
    continue_button.grid(
        row=3,
        column=0,
        columnspan=MAX_GROUP_NUM - 1,
        pady=23,
        padx=30,
        sticky="nsew",
    )
    root.grid_rowconfigure(3, weight=1)
    num_cols = root.grid_size()[0]  # maximise cols
    for c in range(num_cols):
        root.grid_columnconfigure(c, weight=1)

    root.mainloop()


# %%..................  LOCAL FUNCTION(S) #1 - BUILD MAIN WINDOW  ......................
def build_mainwindow(root, group_number, root_dimensions):
    """Build the main window based on the number of groups to compare"""
    group_number = group_number.get()
    if group_number == 0:
        error_message = "You did not specify a number of groups for your contrast."
        tk.messagebox.showerror(title="No Input", message=error_message)
        root.deiconify()
    else:
        # ........................  geometry & intro section  ..........................
        # geometry
        mainwindow = ctk.CTkToplevel(root)
        mainwindow.title("Group GaitA")
        mainwindow.geometry(f"{screen_width}x{screen_height}+0+0")
        fix_window_after_its_creation(mainwindow)
        # welcome message
        welcomestring = "Please read info below carefully."
        welcomeheader_label = ctk.CTkLabel(
            mainwindow,
            text=welcomestring,
            width=screen_width,
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=("Britannic Bold", HEADER_FONT_SIZE),
        )
        welcomeheader_label.grid(row=0, column=0, columnspan=2, sticky="nsew")
        # info message
        introstring = (
            "This program performs group-level analyses on results obtained with "
            + "AutoGaitA DLC or AutoGaitA Simi. \n\nFor this, it requires:"
            + "\n1) Group names and paths to groups' /Results/ subfolders obtained our "
            + "first-level programs."
            + "\n2) A path to a folder where you would like group-results to be stored."
        )
        introheader_label = ctk.CTkLabel(
            mainwindow, text=introstring, width=screen_width
        )
        introheader_label.grid(row=1, column=0, columnspan=2, pady=10)

        # ..........................  main configuration  ..............................
        # config header
        cfgheader_label = ctk.CTkLabel(
            mainwindow,
            text="Main Configuration",
            width=screen_width,
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=("Britannic Bold", HEADER_FONT_SIZE),
        )
        cfgheader_label.grid(row=2, column=0, columnspan=2, pady=10, sticky="nsew")
        # load group names and dirs from the config file
        initial_names, initial_dirs = extract_group_names_and_dirs_from_json_file()
        # group names & dirs - variables
        group_names = [
            tk.StringVar(mainwindow, initial_names[g]) for g in range(group_number)
        ]
        group_dirs = [
            tk.StringVar(mainwindow, initial_dirs[g]) for g in range(group_number)
        ]
        group_names_labels = []
        group_names_entries = []
        group_dirs_labels = []
        group_dirs_entries = []
        row_counter = 3  # track row idxs for loop-widget-creation
        for g in range(group_number):
            this_groups_number = g + 1
            # group names - labels
            group_names_labels.append(
                ctk.CTkLabel(
                    mainwindow,
                    text="Group " + str(this_groups_number) + "'s Name",
                )
            )
            group_names_labels[-1].grid(row=row_counter, column=0)
            # group names - entries
            group_names_entries.append(
                ctk.CTkEntry(mainwindow, textvariable=group_names[g])
            )
            group_names_entries[-1].grid(row=row_counter + 1, column=0)
            # group dirs - labels
            group_dir_string = (
                "Path to Group " + str(this_groups_number) + "'s /Results/ subfolder"
            )
            group_dirs_labels.append(ctk.CTkLabel(mainwindow, text=group_dir_string))
            group_dirs_labels[-1].grid(row=row_counter, column=1)
            # group dirs - entries
            group_dirs_entries.append(
                ctk.CTkEntry(mainwindow, textvariable=group_dirs[g])
            )
            group_dirs_entries[-1].grid(row=row_counter + 1, column=1, sticky="ew")
            # update row counter
            row_counter += 2
        # call row_counter a better name
        last_group_row = row_counter
        # results dir
        results_dir = tk.StringVar(
            mainwindow,
            extract_results_dir_from_json_file(),
        )
        results_dir_string = "Where do you want group-results to be saved?"
        results_dir_label = ctk.CTkLabel(mainwindow, text=results_dir_string)
        results_dir_label.grid(row=last_group_row, column=0, columnspan=2, sticky="ew")
        results_dir_entry = ctk.CTkEntry(mainwindow, textvariable=results_dir)
        results_dir_entry.grid(
            row=last_group_row + 1, column=0, columnspan=2, sticky="ew"
        )
        # Perm Test
        perm_string = "Run cluster-extent permutation test"
        perm_checkbox = ctk.CTkCheckBox(
            mainwindow,
            text=perm_string,
            variable=cfg["do_permtest"],
            onvalue=True,
            offvalue=False,
            fg_color=FG_COLOR,
            hover_color=HOVER_COLOR,
        )
        perm_checkbox.grid(row=last_group_row + 2, column=0, columnspan=2, pady=10)
        # ANOVA info
        ANOVA_string = "Run ANOVA - if yes: choose design below"
        ANOVA_checkbox = ctk.CTkCheckBox(
            mainwindow,
            text=ANOVA_string,
            variable=cfg["do_anova"],
            onvalue=True,
            offvalue=False,
            fg_color=FG_COLOR,
            hover_color=HOVER_COLOR,
            command=lambda: change_ANOVA_buttons_state(ANOVA_buttons, cfg),
        )
        ANOVA_checkbox.grid(row=last_group_row + 3, column=0, columnspan=2, pady=10)
        # ANOVA design
        ANOVA_buttons_strings = ["Mixed ANOVA", "RM ANOVA"]
        ANOVA_buttons = []
        for i in range(len(ANOVA_buttons_strings)):
            ANOVA_buttons.append(
                ctk.CTkRadioButton(
                    mainwindow,
                    text=ANOVA_buttons_strings[i],
                    variable=cfg["anova_design"],
                    value=ANOVA_buttons_strings[i],
                    fg_color=FG_COLOR,
                    hover_color=HOVER_COLOR,
                    state="disabled",
                )
            )
            if cfg["do_anova"].get() == True:
                ANOVA_buttons[i].configure(state="normal")
            ANOVA_buttons[-1].grid(row=last_group_row + 4, column=i)
        # ....................  advanced cfg & define features  ........................
        # advanced cfg
        cfgwindow_label = ctk.CTkLabel(
            mainwindow,
            text="Advanced Configuration",
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=("Britannic Bold", HEADER_FONT_SIZE),
        )
        cfgwindow_label.grid(
            row=last_group_row + 5, column=0, pady=(15, 0), sticky="nsew"
        )
        cfgwindow_button = ctk.CTkButton(
            mainwindow,
            text="Advanced cfg",
            fg_color=FG_COLOR,
            hover_color=HOVER_COLOR,
            command=lambda: (advanced_cfgwindow(mainwindow, root_dimensions)),
        )
        cfgwindow_button.grid(
            row=last_group_row + 6, column=0, sticky="nsew", pady=15, padx=30
        )
        # define features
        definefeatures_label = ctk.CTkLabel(
            mainwindow,
            text="Define Features",
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=("Britannic Bold", HEADER_FONT_SIZE),
        )
        definefeatures_label.grid(
            row=last_group_row + 5, column=1, pady=(15, 0), sticky="nsew"
        )
        definefeatures_button = ctk.CTkButton(
            mainwindow,
            text="I am ready - define features!",
            fg_color=FG_COLOR,
            hover_color=HOVER_COLOR,
            command=lambda: (
                definefeatures_window(
                    mainwindow,
                    group_names,
                    group_dirs,
                    results_dir,
                    root,
                    root_dimensions,
                ),
            ),
        )
        definefeatures_button.grid(
            row=last_group_row + 6, column=1, sticky="nsew", pady=15, padx=30
        )

        # maximise widgets to fit fullscreen
        maximise_widgets(mainwindow)


# %%..............  LOCAL FUNCTION(S) #2 - BUILD ADVANCED CFG WINDOW  ..................


def advanced_cfgwindow(mainwindow, root_dimensions):
    """Build advanced configuration window"""

    # build window
    cfgwindow = ctk.CTkToplevel(mainwindow)
    cfgwindow.title("Advanced Configuration")
    cfgwindow.geometry(f"{screen_width}x{screen_height}+0+0")
    fix_window_after_its_creation(cfgwindow)

    # number of permutations
    permutation_number_string = "Number of permutations of the cluster-extent test"
    permutation_number_label = ctk.CTkLabel(cfgwindow, text=permutation_number_string)
    permutation_number_label.grid(row=0, column=0)
    permutation_number_entry = ctk.CTkEntry(
        cfgwindow, textvariable=cfg["permutation_number"]
    )
    permutation_number_entry.grid(row=1, column=0)

    # statistical threshold of significance
    stats_threshold_string = "Alpha level of statistical significance (as a decimal)"
    stats_threshold_label = ctk.CTkLabel(cfgwindow, text=stats_threshold_string)
    stats_threshold_label.grid(row=2, column=0)
    stats_threshold_entry = ctk.CTkEntry(cfgwindow, textvariable=cfg["stats_threshold"])
    stats_threshold_entry.grid(row=3, column=0)

    # number of PCs
    number_of_PCs_string = "How many principal components to compute?"
    number_of_PCs_label = ctk.CTkLabel(cfgwindow, text=number_of_PCs_string)
    number_of_PCs_label.grid(row=4, column=0)
    number_of_PCs_entry = ctk.CTkEntry(cfgwindow, textvariable=cfg["number_of_PCs"])
    number_of_PCs_entry.grid(row=5, column=0)

    # plot SE
    plot_SE_string = "Plot standard error instead of standard deviation as error bars"
    plot_SE_box = ctk.CTkCheckBox(
        cfgwindow,
        text=plot_SE_string,
        variable=cfg["plot_SE"],
        onvalue=True,
        offvalue=False,
        hover_color=HOVER_COLOR,
        fg_color=FG_COLOR,
    )
    plot_SE_box.grid(row=6, column=0)

    # save 3D PCA video
    save_PCA_video_string = "Save video of 3D PCA Scatterplot (requires ffmpeg!)"
    save_PCA_video_checkbox = ctk.CTkCheckBox(
        cfgwindow,
        text=save_PCA_video_string,
        variable=cfg["save_3D_PCA_video"],
        onvalue=True,
        offvalue=False,
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
    )
    save_PCA_video_checkbox.grid(row=7, column=0)

    # done button
    adv_cfg_done_button = ctk.CTkButton(
        cfgwindow,
        text="I am done, update cfg.",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: cfgwindow.destroy(),
    )
    adv_cfg_done_button.grid(row=8, column=0, sticky="nsew", pady=20, padx=80)

    # maximise widgets to fit fullscreen
    maximise_widgets(cfgwindow)


# %%..............  LOCAL FUNCTION(S) #3 - BUILD ADD FEATURES WINDOW  ..................


def definefeatures_window(
    mainwindow, group_names, group_dirs, results_dir, root, root_dimensions
):
    """Build define features window"""

    # nested function (called by run-button): extract boolean checkbox vars and store
    # in cfg dicts!
    def get_selected_variables():
        for key in LIST_VARS:
            # this list comprehension extracts all strings (keys) of checkbox_vars'
            # given sub-dict (either stats_variables or PCA_variables) and stores it to
            # the correct key of our cfg dict if it was checked (i.e., if var.get() is
            # True!)
            cfg[key] = [
                string for string, var in checkbox_vars[key].items() if var.get()
            ]

    # .................  EXTRACT FEATURES FROM A NORMALISED SC XLS  ....................
    # => First read the xls as df, extract columns that are meaningful after
    #    normalisation, or throw errors if we don't manage to do so
    df = None
    test_directories = []  # first see if all group dirs are valid paths
    for directory in group_dirs:
        test_directories.append(directory.get())
    for directory in test_directories:
        if not os.path.exists(directory):
            error_msg = "No directory found at: " + directory
            tk.messagebox.showerror(title="Folder not found!", message=error_msg)
            return
    if not results_dir.get():
        error_msg = "You did not specify a directory to save results to!"
        tk.messagebox.showerror(title="Folder not found!", message=error_msg)
        return
    if not os.path.exists(results_dir.get()):  # for results dir, create if not there
        os.makedirs(results_dir.get())
    some_groups_dir = group_dirs[0].get()
    all_ID_dirs = [
        f
        for f in os.listdir(some_groups_dir)
        if os.path.isdir(os.path.join(some_groups_dir, f))
    ]
    for ID_dir in all_ID_dirs:
        some_IDs_dir = os.path.join(some_groups_dir, ID_dir)
        IDs_files = os.listdir(some_IDs_dir)
        # next operator means we loop lazy - stop once we find it & return None if norm
        # sheet not in dir
        norm_sheet_path = next(
            (file for file in IDs_files if NORM_SHEET_NAME in file), None
        )
        if norm_sheet_path:  # won't be true if no NORMXLS found
            full_path = os.path.join(some_IDs_dir, norm_sheet_path)
            if norm_sheet_path.endswith(".xlsx"):
                df = pd.read_excel(full_path)
                break
            elif norm_sheet_path.endswith(".csv"):
                df = pd.read_csv(full_path)
                break
    # select columns we want to provide as feature options using regular expressions
    if df is not None:
        feature_strings = tuple(
            df.filter(regex="(y$|Z$|Angle$|Velocity$|Acceleration$)").columns
        )
    else:
        error_string = "Unable to find any Normalised SC sheet at " + some_groups_dir
        tk.messagebox.showerror(title="Group Directory Error!", message=error_string)
        print(error_string)
        print("Analysis did not run due to above errors. Fix them & re-try!")
        return

    # .......................  BUILD THE TOPLEVEL WINDOW  .............................
    # build window
    featureswindow = ctk.CTkToplevel(mainwindow)
    featureswindow.title("Add Features & Run!")
    featureswindow.geometry(f"{screen_width}x{screen_height}+0+0")
    fix_window_after_its_creation(featureswindow)
    # grid prep
    scrollbar_rows = 5  # scrollbar rowspan (in featureswindow)
    scrollbar_grid_ncols = 3
    # + 5 to be sure we have enough rows
    scrollbar_grid_nrows = math.ceil(len(feature_strings) / scrollbar_grid_ncols) + 5

    # stats label
    stats_label = ctk.CTkLabel(
        featureswindow,
        text="Statistics",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
    stats_label.grid(row=0, column=0, sticky="nsew")
    # PCA label
    PCA_label = ctk.CTkLabel(
        featureswindow,
        text="PCA",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
    PCA_label.grid(row=0, column=1, sticky="nsew")

    # .........................  PCA / STATS FEATURE FRAMES  ...........................
    # stats scrollable frame initialisation
    stats_frame = ctk.CTkScrollableFrame(featureswindow)
    stats_frame.grid(row=1, column=0, rowspan=scrollbar_rows, sticky="nsew")
    # PCA scrollable frame initialisation
    PCA_frame = ctk.CTkScrollableFrame(featureswindow)
    PCA_frame.grid(row=1, column=1, rowspan=scrollbar_rows, sticky="nsew")
    # populate scrollable frames with features
    # => note that checkbox_vars just store whether a given checkbox is checked
    #    (i.e., True) or not. we will store all true checkboxes for both PCA and stats
    #    later (but it's handy that the key names overlap)
    checkbox_vars = {key: {} for key in LIST_VARS}
    for f_idx, frame in enumerate([stats_frame, PCA_frame]):
        if frame == stats_frame:  # make sure to put stuff into the correct dict
            key = "stats_variables"
        elif frame == PCA_frame:
            key = "PCA_variables"
        row_counter = 1  # index rows at 1 for the top otherwise it breaks (dont ask)
        col_counter = 0
        for feature in feature_strings:
            # check whether features of this run (feature in feature_strings) where
            # also in the last run (cfg[key] = stats/PCA_variables list from config file)
            # if yes then set the checkbox to true
            if feature in cfg["last_runs_" + key]:
                checkbox_vars[key][feature] = var = tk.BooleanVar(value=True)
            # else set it to false as by default
            else:
                checkbox_vars[key][feature] = var = tk.BooleanVar()
            this_checkbox = ctk.CTkCheckBox(
                frame,
                text=feature,
                variable=var,
                fg_color=FG_COLOR,
                hover_color=HOVER_COLOR,
                font=("Britannic Bold", HEADER_FONT_SIZE - 5),
            )
            this_checkbox.grid(row=row_counter, column=col_counter, sticky="nsew")
            # if user doesn't want to do stats, dont have them choose features
            if frame == stats_frame:
                if (cfg["do_permtest"].get() is False) & (
                    cfg["do_anova"].get() is False
                ):
                    this_checkbox.configure(state="disabled")
            row_counter += 1
            # # CARE - the -1 is important here since indexing starts at 0 and grid_nrows
            # # is like len() kinda
            if row_counter == scrollbar_grid_nrows:  # not nrows-1 because we start @ 1
                row_counter = 1  # index rows at 1 for the top otherwise it breaks
                col_counter += 1
        # maximise widgets to fit frame (of scrollbar!)
        maximise_widgets(frame)

    # which leg label
    which_leg_label = ctk.CTkLabel(
        featureswindow,
        text="Choose Body Side",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
    which_leg_label.grid(row=2 + scrollbar_rows, column=0, sticky="nsew")
    # which leg of human data to analyse
    which_leg_string = (
        "If you ran AutoGaitA Simi first: which body side's behaviour "
        " (e.g. step-cycles) do you want to analyse?"
    )
    which_leg_label = ctk.CTkLabel(featureswindow, text=which_leg_string)
    which_leg_label.grid(row=3 + scrollbar_rows, column=0, sticky="ew")
    which_leg_options = ["left", "right"]  # !!! NU - "both" functionality
    which_leg_optionmenu = ctk.CTkOptionMenu(
        featureswindow,
        values=which_leg_options,
        variable=cfg["which_leg"],
        fg_color=FG_COLOR,
        button_color=FG_COLOR,
        button_hover_color=HOVER_COLOR,
    )
    which_leg_optionmenu.grid(row=4 + scrollbar_rows, column=0)
    # run
    runheader_label = ctk.CTkLabel(
        featureswindow,
        text="Run Analysis",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=("Britannic Bold", HEADER_FONT_SIZE),
    )
    runheader_label.grid(row=2 + scrollbar_rows, column=1, sticky="nsew")
    run_button = ctk.CTkButton(
        featureswindow,
        text="I am ready - run analysis!",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: (
            build_donewindow(
                group_names,
                group_dirs,
                results_dir,
                root,
                mainwindow,
                featureswindow,
            ),
            get_selected_variables(),
        ),
    )
    run_button.grid(row=4 + scrollbar_rows, column=1, sticky="nsew", pady=40, padx=40)

    # maximise widgets to fit fullscreen
    maximise_widgets(featureswindow)


# %%..................  LOCAL FUNCTION(S) #4 - BUILD DONE WINDOW  ......................
def build_donewindow(
    group_names, group_dirs, results_dir, root, mainwindow, featureswindow
):
    """Build done window"""
    # create done window & make it pretty and nice
    w = screen_width
    h = screen_height
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

    # ..................................................................................
    # ........................  IMPORTANT - prepare folderinfo .........................
    # ..................................................................................
    folderinfo = {"group_names": [], "group_dirs": [], "results_dir": ""}
    for g in range(len(group_names)):
        folderinfo["group_names"].append(group_names[g].get())
        folderinfo["group_dirs"].append(group_dirs[g].get())
    folderinfo["results_dir"] = results_dir.get()

    # run button
    done_button = ctk.CTkButton(
        donewindow,
        text="Run!",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        command=lambda: (
            update_config_file(folderinfo, cfg),
            run_analysis(folderinfo, cfg),
            featureswindow.destroy(),
            donewindow.destroy(),
            root.deiconify(),
        ),
    )
    done_button.grid(row=4, column=0, sticky="nsew", pady=10, padx=20)
    # maximise button only
    donewindow.grid_rowconfigure(4, weight=1)


# %%..................  LOCAL FUNCTION(S) #5 - RUN GROUP ANALYSIS  .....................
def run_analysis(folderinfo, cfg):
    """Run group results based on current info

    Note
    ----
    1) We previously used .get() on folderinfo string entries (names & dirs)
    => see IMPORTANT - prepare folderinfo above
    2) check_folderinfo_and_cfg just checks user inputs for validity
    => no .get() is called there, no variables are assigned to anything
    => tbh I think the check for dirs is redundant since we already do that at start
       of definefeatures_window - but whatever
    3) extract_this_runs_folderinfo_and_cfg extracts vars using .get() if necessary
    => we return this_ folderinfo/cfg dicts which are then used for running the analysis
    => ie. folderinfo & cfg entries can be changed by user, their values (eg. entries &
       checkboxes) are only collected once the user hits the run button in the features
       window (run_button collects stats/PCA checkboxes & done_button everything else)
    """

    # check if user-provided values were correct before extracting them for run function
    error_msg = check_folderinfo_and_cfg(folderinfo, cfg)
    if len(error_msg) > 0:
        error_string = "The following input variables are wrong! Fix them & re-run!\n"
        for i in range(len(error_msg)):
            error_string = error_string + "\n" + error_msg[i]
        tk.messagebox.showerror(title="Input variable errors!", message=error_string)
        print(error_string)
        print("Analysis did not run due to above errors. Fix them & re-try!")
        return

    # extract this runs variables correctly before running
    this_runs_folderinfo, this_runs_cfg = extract_this_runs_folderinfo_and_cfg(
        folderinfo, cfg
    )

    # run in a thread (see a note about thread running after helper functions)
    run_thread = Thread(
        target=autogaita_group.group, args=(this_runs_folderinfo, this_runs_cfg)
    )
    run_thread.start()


def check_folderinfo_and_cfg(folderinfo, cfg):
    """Check if the folderinfo and cfg values provided by the user are fine"""
    error_msg = []
    both_dicts = [folderinfo, cfg]
    for inner_dict in both_dicts:
        for key in inner_dict.keys():
            # check string vars: group dirs & names and results dir
            if key in STRING_VARS:
                if key == "group_dirs":
                    for g_idx, group_dir in enumerate(inner_dict[key]):
                        if not os.path.exists(group_dir):
                            this_msg = (
                                "Group #"
                                + str(g_idx + 1)
                                + "'s directory does not exist!"
                            )
                            print("\n" + this_msg)
                            error_msg.append(this_msg)
                elif key == "group_names":
                    for i in range(len(inner_dict[key])):
                        if len(inner_dict[key][i]) == 0:
                            this_msg = "Group #" + str(i + 1) + "'s name is empty!"
                            print("\n" + this_msg)
                            error_msg.append(this_msg)
                elif key == "results_dir":
                    if len(inner_dict[key]) == 0:
                        this_msg = key + " is empty!"
                        print("\n" + this_msg)
                        error_msg.append(this_msg)
            # check if numerical cfg variables were given correctly
            if key in FLOAT_VARS:
                try:
                    float(inner_dict[key].get())
                except ValueError:
                    this_msg = (
                        key
                        + " value was not a decimal number, but "
                        + inner_dict[key].get()
                    )
                    print(this_msg)
                    error_msg.append(this_msg)
            if key in INT_VARS:
                try:
                    int(inner_dict[key].get())
                except:
                    this_msg = (
                        key
                        + " value was not an integer number, but "
                        + inner_dict[key].get()
                    )
                    print(this_msg)
                    error_msg.append(this_msg)
    return error_msg


def extract_this_runs_folderinfo_and_cfg(folderinfo, cfg):
    """Extract folderinfo and cfg of current run - immediately before running!"""
    # prepare this runs folderinfo
    this_runs_folderinfo = {}
    # make sure that directories end with os.sep (since we want to be able to save files
    # using string concatenation). If not just add a forward slash. In the beginning
    # of autogaita_group, we will convert os.sep to forward slashes if they should be
    # backward slashes (windows works with both)
    # => Note this was changed and works with os.path.join() now...
    # => NU: have another look @ this matter in GUI functions
    for key in folderinfo.keys():
        if key == "group_names":
            this_runs_folderinfo[key] = folderinfo[key]
        if "dir" in key:
            if type(folderinfo[key]) == list:  # group_dirs
                this_runs_folderinfo[key] = [[] for _ in range(len(folderinfo[key]))]
                for i in range(len(folderinfo[key])):
                    if not folderinfo[key][i].endswith(os.sep):
                        this_runs_folderinfo[key][i] = folderinfo[key][i] + "/"
                    else:
                        this_runs_folderinfo[key][i] = folderinfo[key][i]
            else:  # results_dir
                if not folderinfo[key].endswith(os.sep):
                    this_runs_folderinfo[key] = folderinfo[key] + "/"
                else:
                    this_runs_folderinfo[key] = folderinfo[key]
    # prepare this runs cfg
    this_runs_cfg = {}
    for key in cfg.keys():
        if key in LIST_VARS:  # no get() needed - since these are lists already
            this_runs_cfg[key] = cfg[key]
            # elif is necessary as we want to exclude "last_runs_stats/PCA_variables"
        elif key not in EXCLUDED_VARS_FROM_CFG_FILE:
            this_runs_cfg[key] = cfg[key].get()
            # convert to numbers
            if key in FLOAT_VARS:
                this_runs_cfg[key] = float(this_runs_cfg[key])
            if key in INT_VARS:
                this_runs_cfg[key] = int(this_runs_cfg[key])
    return this_runs_folderinfo, this_runs_cfg

    # !!! NU - leave as is for now but if you want to add info messages for users about
    # how many active runs they have in their pipeline when adding a new one you can probably
    # have run_thread be a global variable and then use len(globals["run_thread"].is_active())
    # or something to print the number of active threads

    # # once we got this done, run the analysis in a separate thread
    # local_vars = locals()
    # if "run_thread" in local_vars:
    #     if local_vars["run_thread"].is_alive():
    #         still_busy_message = (
    #             "Your previous run is still being processed, we will let you know "
    #             + "once we are ready for another run :)"
    #             )
    #         tk.messagebox(title="Still busy :s", message=still_busy_message)
    #     else:
    #         run_thread = Thread(
    #             target=autogaita_group.main, args=(this_runs_folderinfo, this_runs_cfg)
    #             )
    #         check_thread = Thread(target=check_run_thread_completion, args=(run_thread))
    #         run_thread.start()
    #         check_thread.start()
    # else:
    #     run_thread = Thread(
    #         target=autogaita_group_dev.main, args=(this_runs_folderinfo, this_runs_cfg)
    #         )
    #     check_thread = Thread(target=check_run_thread_completion, args=(run_thread,))
    #     run_thread.start()
    #     check_thread.start()

    # def check_run_thread_completion(run_thread):
    #     """Keep checking if run thread is finished, if so display a tkinter messagebox"""
    #     dummy_number = 1
    #     while dummy_number != 0:
    #         if run_thread.is_alive():
    #             dummy_number += 1
    #     else:
    #         done_message = (
    #             "Your run has finished execution! You can find your results in the "
    #             + "group directory you provided and are able to run further runs if "
    #             + "desired.")
    #         tk.messagebox(title="Finished :)", message=done_message)
    #         dummy_number = 0  # so we exit the while loop


# %%...............  LOCAL FUNCTION(S) #6 - VARIOUS HELPER FUNCTIONS  ..................


def change_ANOVA_buttons_state(ANOVA_buttons, cfg):
    """Change the state of ANOVA radio button widgets based on whether user wants
    to perform an ANOVA or not.
    """
    if cfg["do_anova"].get() == True:
        for i in range(len(ANOVA_buttons)):
            ANOVA_buttons[i].configure(state="normal")
    elif cfg["do_anova"].get() == False:
        for i in range(len(ANOVA_buttons)):
            ANOVA_buttons[i].configure(state="disabled")


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


def update_config_file(folderinfo, cfg):
    """updates the group_gui_config file with this folderinfo and cfg parameters"""
    # transform tkVars into normal strings and bools
    output_dicts = [{"group_names": [], "group_dirs": [], "results_dir": ""}, {}]

    for i in range(len(output_dicts)):
        if i == 0:  # as the list index 0 refers to  folderinfo
            # to not alter the initial folderinfo variable a deepcopy is used
            input_dict = copy.deepcopy(folderinfo)
            output_dicts[0] = input_dict
            # the next if statement ensures that the names and dirs list always contains
            # the max group number of entries
            if len(output_dicts[0]["group_names"]) != MAX_GROUP_NUM:
                for i in range(MAX_GROUP_NUM - len(input_dict["group_names"])):
                    output_dicts[0]["group_names"].append("")
                    output_dicts[0]["group_dirs"].append("")

        elif i == 1:  # as the list index 1 refers to cfg
            input_dict = cfg
            for key in input_dict.keys():
                if key in LIST_VARS:  # PCA or Stats variables
                    # if list of strings, initialise output empty list and append vals
                    output_dicts[i][key] = []
                    for entry in input_dict[key]:
                        output_dicts[i][key].append(entry)
                # otherwise (if str, int or bool) get() and define
                elif (
                    key not in EXCLUDED_VARS_FROM_CFG_FILE
                ):  # not PCS or Stats variables
                    output_dicts[i][key] = input_dict[key].get()

    # merge the two configuration dictionaries
    # 0 = folderinfo, 1 = cfg, see above
    configs_list = [
        output_dicts[0],
        output_dicts[1],
    ]
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
        elif key in INT_VARS:
            cfg[key] = tk.IntVar(root, last_runs_cfg[key])
        elif key in TK_STR_VARS:
            cfg[key] = tk.StringVar(root, last_runs_cfg[key])
        # PCA/stats_variable are not needed as tkStringVars
        # see the ---PCA / STATS FEATURE FRAMES--- section for their usage
        elif key in LIST_VARS:
            # creates an empty list for this runs variables
            cfg[key] = []
            # and saves the stats/PCA_variables from the last run in a separate list
            # note, this list will not be save to the config file as "last_runs_..._variables"
            # in not in LIST_VARS
            cfg["last_runs_" + key] = []
            for entry in last_runs_cfg[key]:
                cfg["last_runs_" + key].append(entry)

    return cfg


def extract_group_names_and_dirs_from_json_file():
    """loads the group names and dirs from the config file"""
    # load the configuration file
    with open(
        os.path.join(AUTOGAITA_FOLDER_PATH, CONFIG_FILE_NAME), "r"
    ) as config_json_file:
        # config_json contains list with 0 -> folderinfo and 1 -> cfg data
        last_runs_folderinfo = json.load(config_json_file)[0]

    group_names = []
    group_dirs = []

    for key in last_runs_folderinfo.keys():
        if key == "group_names":
            for entry in last_runs_folderinfo[key]:
                group_names.append(entry)
        if key == "group_dirs":
            for entry in last_runs_folderinfo[key]:
                group_dirs.append(entry)

    return group_names, group_dirs


def extract_results_dir_from_json_file():
    """loads the results dir from the config file"""
    # load the configuration file
    with open(
        os.path.join(AUTOGAITA_FOLDER_PATH, CONFIG_FILE_NAME), "r"
    ) as config_json_file:
        # config_json contains list with 0 -> folderinfo and 1 -> cfg data
        last_runs_folderinfo = json.load(config_json_file)[0]

    results_dir = last_runs_folderinfo["results_dir"]

    return results_dir


# %% what happens if we hit run
if __name__ == "__main__":
    group_gui()

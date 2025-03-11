# %% imports
import autogaita
import autogaita.gui.gaita_widgets as gaita_widgets
import autogaita.gui.gui_utils as gui_utils
import tkinter as tk
import customtkinter as ctk
import pandas as pd
import os
import math
from threading import Thread
import platform
import json
import copy


# %% global constants
from autogaita.gui.gui_constants import (
    GROUP_FG_COLOR,
    GROUP_HOVER_COLOR,
    HEADER_FONT_NAME,
    HEADER_FONT_SIZE,
    HEADER_TXT_COLOR,
    MAIN_HEADER_FONT_SIZE,
    TEXT_FONT_NAME,
    TEXT_FONT_SIZE,
    ADV_CFG_TEXT_FONT_SIZE,
    COLOR_PALETTES_LIST,
    WINDOWS_TASKBAR_MAXHEIGHT,
    AUTOGAITA_FOLDER_PATH,
    get_widget_cfg_dict,  # function!
)
from autogaita.group.group_constants import NORM_SHEET_NAME, AVG_GROUP_SHEET_NAME

# these colors are GUI-specific - add to common widget cfg
FG_COLOR = GROUP_FG_COLOR
HOVER_COLOR = GROUP_HOVER_COLOR
WIDGET_CFG = get_widget_cfg_dict()
WIDGET_CFG["FG_COLOR"] = FG_COLOR
WIDGET_CFG["HOVER_COLOR"] = HOVER_COLOR

# group GUI specific constants
MIN_GROUP_NUM = 2
MAX_GROUP_NUM = 6
CONFIG_FILE_NAME = "group_gui_config.json"
STRING_VARS = ["group_names", "group_dirs", "results_dir", "load_dir"]
# note n_components can be float only for this input-check since we convert to int when
# fitting the PCA model if it is equal to or greater than 1
FLOAT_VARS = ["stats_threshold", "PCA_n_components"]
LIST_VARS = [
    "stats_variables",  #  stats/PCA variables are also TK_BOOL_VARS but this will be
    "PCA_variables",  #  handled within the ---PCA / STATS FEATURE FRAMES--- part
]
INT_VARS = ["permutation_number"]
# TK_BOOL/STR_VARS are only used for initialising widgets based on cfg file
# (note that numbers are initialised as strings)
TK_BOOL_VARS = [
    "do_permtest",
    "do_anova",
    "PCA_save_3D_video",
    "plot_SE",
    "legend_outside",
    "dont_show_plots",
]
TK_STR_VARS = [
    "anova_design",
    "permutation_number",
    "stats_threshold",
    "PCA_n_components",
    "PCA_custom_scatter_PCs",
    "PCA_bins",
    "which_leg",
    "results_dir",
    "load_dir",
    "color_palette",
]
EXCLUDED_VARS_FROM_CFG_FILE = ["last_runs_stats_variables", "last_runs_PCA_variables"]

# %%...............................  MAIN PROGRAM ......................................


def run_group_gui():
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
    gui_utils.configure_the_icon(root)

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

    # ..................................................................................
    # .......................  root (intro) window population  .........................
    # ..................................................................................

    # .................................  widgets  ......................................
    # welcome message
    welcomestring = "Welcome to AutoGaitA Group!"
    welcomeheader_label = ctk.CTkLabel(
        root,
        text=welcomestring,
        width=root_w,
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
    )
    welcomeheader_label.grid(row=0, column=0, columnspan=MAX_GROUP_NUM - 1)
    # contrast number message
    numberstring = "How many groups would you like to compare with each other?"
    numberheader_label = ctk.CTkLabel(
        root,
        text=numberstring,
        width=root_w,
        text_color=HEADER_TXT_COLOR,
        font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
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
                font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
            )
        )
        group_buttons[-1].grid(row=2, column=i - MIN_GROUP_NUM)
    # continue button
    continue_button = ctk.CTkButton(
        root,
        text="Continue",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: (
            build_mainwindow(root, group_number, root_dimensions),
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
        # .....................  important - global cfg variable  ......................
        # we have cfg be global so it can be modified by all widgets and frames.
        # just prior to calling autogaita.group, we will copy its values to a temporary # cfg var, so the values of the global variable are never used for running
        # anything (see run_analysis)
        global cfg
        cfg = extract_cfg_from_json_file(root)

        # ........................  geometry & intro section  ..........................
        # geometry
        mainwindow = ctk.CTkToplevel(root)
        mainwindow.title("Group GaitA")
        # set the dimensions of the screen and where it is placed
        # => have it half-wide starting at 1/4 of screen's width (dont change w & x!)
        mainwindow.geometry(
            f"{int(screen_width / 2)}x{screen_height}+{int(screen_width / 4)}+0"
        )
        fix_window_after_its_creation(mainwindow)

        # ..........................  main configuration  ..............................
        # config header
        cfgheader_label = ctk.CTkLabel(
            mainwindow,
            text="Main Configuration",
            width=screen_width,
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=(HEADER_FONT_NAME, MAIN_HEADER_FONT_SIZE),
        )
        cfgheader_label.grid(row=0, column=0, columnspan=3, sticky="nsew")
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
        group_dirs_entries = []
        # group number, name & dir labels
        group_number_label = ctk.CTkLabel(
            mainwindow,
            text="Group Number",
            font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
        )
        group_number_label.grid(row=1, column=0)
        group_name_label = ctk.CTkLabel(
            mainwindow,
            text="Name",
            font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
        )
        group_name_label.grid(row=1, column=1)
        group_dir_label = ctk.CTkLabel(
            mainwindow,
            text="Path to first-level Results",
            font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
        )
        group_dir_label.grid(row=1, column=2)
        row_counter = 2  # track row idxs for loop-widget-creation
        # ...........................  group-widgets-loop  .............................
        for g in range(group_number):
            this_groups_number = g + 1
            # group numbers - labels
            group_names_labels.append(
                ctk.CTkLabel(
                    mainwindow,
                    text=str(this_groups_number),
                    font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
                )
            )
            group_names_labels[-1].grid(row=row_counter, column=0)
            # group names - entries
            group_names_entries.append(
                ctk.CTkEntry(
                    mainwindow,
                    textvariable=group_names[g],
                    font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
                )
            )
            group_names_entries[-1].grid(row=row_counter, column=1)
            # group dirs - entries
            group_dirs_entries.append(
                ctk.CTkEntry(
                    mainwindow,
                    textvariable=group_dirs[g],
                    font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
                )
            )
            group_dirs_entries[-1].grid(row=row_counter, column=2, sticky="ew")
            # update row counter
            row_counter += 1
        # call row_counter a better name
        last_group_row = row_counter
        # empty label 1 for spacing
        empty_label_one = ctk.CTkLabel(mainwindow, text="")
        empty_label_one.grid(row=last_group_row, column=0, columnspan=3, sticky="nsew")

        # NOTE! load results and load dirs as strings from cfg json before converting
        #       to tk-vars
        results_dir_string, load_dir_string = (
            extract_results_and_load_dirs_from_json_files()
        )

        # results dir
        results_dir = tk.StringVar(mainwindow, results_dir_string)
        results_dir_label, results_dir_entry = gaita_widgets.label_and_entry_pair(
            mainwindow,
            "Path to save group-analysis results to",
            results_dir,
            WIDGET_CFG,
        )
        results_dir_label.grid(
            row=last_group_row + 1, column=0, columnspan=3, sticky="ew"
        )
        results_dir_entry.grid(
            row=last_group_row + 2, column=0, columnspan=3, sticky="ew"
        )
        # load dir
        load_dir = tk.StringVar(mainwindow, load_dir_string)
        load_dir_label, load_dir_entry = gaita_widgets.label_and_entry_pair(
            mainwindow,
            "Optional: path to load previous group-data from",
            load_dir,
            WIDGET_CFG,
        )
        load_dir_label.grid(row=last_group_row + 3, column=0, columnspan=3, sticky="ew")
        load_dir_entry.grid(row=last_group_row + 4, column=0, columnspan=3, sticky="ew")
        # empty label 2 for spacing
        empty_label_two = ctk.CTkLabel(mainwindow, text="")
        empty_label_two.grid(
            row=last_group_row + 5, column=0, columnspan=3, sticky="nsew"
        )
        # Perm Test
        perm_checkbox = gaita_widgets.checkbox(
            mainwindow,
            "Cluster-extent permutation test",
            cfg["do_permtest"],
            WIDGET_CFG,
        )
        perm_checkbox.grid(row=last_group_row + 6, column=0, columnspan=3, pady=10)
        # ANOVA info
        ANOVA_checkbox = gaita_widgets.checkbox(
            mainwindow,
            "ANOVA & Tukey's. If yes: choose factor-type below",
            cfg["do_anova"],
            WIDGET_CFG,
        )
        ANOVA_checkbox.configure(
            command=lambda: change_ANOVA_buttons_state(ANOVA_buttons),
        )  # dont use gui_utils here because its a bit special
        ANOVA_checkbox.grid(row=last_group_row + 7, column=0, columnspan=3, pady=10)
        # ANOVA design
        ANOVA_string_and_var_value = [
            ["Within-subjects (e.g. pre- & post-treatment)", "RM ANOVA"],
            ["Between-subjects (e.g. age)", "Mixed ANOVA"],
        ]
        ANOVA_buttons = []
        for i in range(len(ANOVA_string_and_var_value)):
            ANOVA_buttons.append(
                ctk.CTkRadioButton(
                    mainwindow,
                    text=ANOVA_string_and_var_value[i][0],
                    variable=cfg["anova_design"],
                    value=ANOVA_string_and_var_value[i][1],
                    fg_color=FG_COLOR,
                    hover_color=HOVER_COLOR,
                    font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
                )
            )
            if cfg["do_anova"].get() is True:
                ANOVA_buttons[i].configure(state="normal")
            ANOVA_buttons[-1].grid(row=last_group_row + 8 + i, column=0, columnspan=3)
        # initialise ANOVA buttons state by running this function once
        change_ANOVA_buttons_state(ANOVA_buttons)

        # ....................  advanced cfg & define features  ........................
        # empty label 3 for spacing
        empty_label_three = ctk.CTkLabel(mainwindow, text="")
        empty_label_three.grid(
            row=last_group_row + 10, column=0, columnspan=3, sticky="nsew"
        )

        # advanced cfg
        cfgwindow_button = gaita_widgets.header_button(
            mainwindow, "Advanced Configuration", WIDGET_CFG
        )
        cfgwindow_button.configure(
            command=lambda: (advanced_cfgwindow(mainwindow)),
        )
        cfgwindow_button.grid(
            row=last_group_row + 11,
            column=0,
            columnspan=3,
        )

        # define features button
        definefeatures_button = gaita_widgets.header_button(
            mainwindow, "I am ready - define features!", WIDGET_CFG
        )
        definefeatures_button.configure(
            command=lambda: (
                definefeatures_window(
                    mainwindow,
                    group_names,
                    group_dirs,
                    results_dir,
                    load_dir,  # tk var
                    cfg["which_leg"],  # tk var
                    root,
                ),
            ),
        )
        definefeatures_button.grid(row=last_group_row + 12, column=0, columnspan=3)

        # empty label four for spacing
        empty_label_four = ctk.CTkLabel(mainwindow, text="")
        empty_label_four.grid(
            row=last_group_row + 13, column=1, columnspan=3, sticky="ns"
        )

        # exit button
        exit_button = gaita_widgets.exit_button(mainwindow, WIDGET_CFG)
        exit_button.configure(
            command=lambda: (
                mainwindow.withdraw(),
                root.deiconify(),
                mainwindow.after(5000, mainwindow.destroy),
            ),
        )
        exit_button.grid(row=last_group_row + 14, column=0, columnspan=3)

        # maximise widgets to fit fullscreen
        maximise_widgets(mainwindow)


# %%..............  LOCAL FUNCTION(S) #2 - BUILD ADVANCED CFG WINDOW  ..................


def advanced_cfgwindow(mainwindow):
    """Build advanced configuration window"""

    # build window
    cfgwindow = ctk.CTkToplevel(mainwindow)
    cfgwindow.title("Advanced Configuration")
    cfgwindow.geometry(
        f"{int(screen_width / 2)}x{screen_height}+{int(screen_width / 4)}+0"
    )
    fix_window_after_its_creation(cfgwindow)

    # number of permutations
    permutation_number_label, permutation_number_entry = (
        gaita_widgets.label_and_entry_pair(
            cfgwindow,
            "Number of permutations of the cluster-extent test",
            cfg["permutation_number"],
            WIDGET_CFG,
        )
    )
    permutation_number_label.grid(row=0, column=0)
    permutation_number_entry.grid(row=1, column=0, sticky="n")

    # statistical threshold of significance
    stats_threshold_label, stats_threshold_entry = gaita_widgets.label_and_entry_pair(
        cfgwindow,
        "Alpha level of statistical significance (as a decimal)",
        cfg["stats_threshold"],
        WIDGET_CFG,
    )
    stats_threshold_label.grid(row=2, column=0)
    stats_threshold_entry.grid(row=3, column=0, sticky="n")

    # number of PCs
    PCA_n_components_string = (
        "Number of principal components (PCs). 0<PCs<1 for var-explained approach."
    )
    PCA_n_components_label, PCA_n_components_entry = gaita_widgets.label_and_entry_pair(
        cfgwindow,
        PCA_n_components_string,
        cfg["PCA_n_components"],
        WIDGET_CFG,
    )
    PCA_n_components_label.grid(row=4, column=0)
    PCA_n_components_entry.grid(row=5, column=0, sticky="n")

    # custom scatter info
    custom_scatter_label, custom_scatter_entry = gaita_widgets.label_and_entry_pair(
        cfgwindow,
        "Enter PCs for custom scatterplots (e.g. 2,3,5;4,6;3,4,5)",
        cfg["PCA_custom_scatter_PCs"],
        WIDGET_CFG,
    )
    custom_scatter_label.grid(row=6, column=0)
    custom_scatter_entry.grid(row=7, column=0, sticky="n")

    # PCA bins
    PCA_bins_label, PCA_bins_entry = gaita_widgets.label_and_entry_pair(
        cfgwindow,
        "Restrict PCA features to following cycle percentages (e.g. 0-10, 24, 50-75)",
        cfg["PCA_bins"],
        WIDGET_CFG,
    )
    PCA_bins_label.grid(row=8, column=0)
    PCA_bins_entry.grid(row=9, column=0, sticky="n")

    # save 3D PCA video
    save_PCA_video_checkbox = gaita_widgets.checkbox(
        cfgwindow,
        "Save video of 3D PCA Scatterplot (requires ffmpeg!)",
        cfg["PCA_save_3D_video"],
        WIDGET_CFG,
    )
    save_PCA_video_checkbox.grid(row=10, column=0)

    # color palette
    color_palette_string = "Choose figures' color palette"
    color_palette_label = ctk.CTkLabel(
        cfgwindow, text=color_palette_string, font=(TEXT_FONT_NAME, TEXT_FONT_SIZE)
    )
    color_palette_label.grid(row=11, column=0)
    color_palette_entry = ctk.CTkOptionMenu(
        cfgwindow,
        values=COLOR_PALETTES_LIST,
        variable=cfg["color_palette"],
        fg_color=FG_COLOR,
        button_color=FG_COLOR,
        button_hover_color=HOVER_COLOR,
        font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
    )
    color_palette_entry.grid(row=12, column=0, sticky="n")

    # plot SE
    plot_SE_box = gaita_widgets.checkbox(
        cfgwindow,
        "Plot standard error instead of standard deviation as error bars",
        cfg["plot_SE"],
        WIDGET_CFG,
    )
    plot_SE_box.grid(row=13, column=0)

    # legend outside
    legend_outside_checkbox = gaita_widgets.checkbox(
        cfgwindow,
        "Plot legends outside of figures' panels",
        cfg["legend_outside"],
        WIDGET_CFG,
    )
    legend_outside_checkbox.grid(row=14, column=0)

    # dont show plots
    dont_show_plots_checkbox = gaita_widgets.checkbox(
        cfgwindow,
        "Don't show plots in GUI (save only)",
        cfg["dont_show_plots"],
        WIDGET_CFG,
    )
    dont_show_plots_checkbox.grid(row=15, column=0)

    # which leg of human data to analyse
    which_leg_string = (
        "If first-level was AutoGaitA Universal 3D: which leg's step-cycles to analyse?"
    )
    which_leg_label = ctk.CTkLabel(
        cfgwindow, text=which_leg_string, font=(TEXT_FONT_NAME, TEXT_FONT_SIZE)
    )
    which_leg_label.grid(row=16, column=0)
    which_leg_options = ["left", "right"]  # !!! NU - "both" functionality
    which_leg_optionmenu = ctk.CTkOptionMenu(
        cfgwindow,
        values=which_leg_options,
        variable=cfg["which_leg"],
        fg_color=FG_COLOR,
        button_color=FG_COLOR,
        button_hover_color=HOVER_COLOR,
        font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
    )
    which_leg_optionmenu.grid(row=17, column=0, sticky="n")

    # done button
    adv_cfg_done_button = ctk.CTkButton(
        cfgwindow,
        text="I am done, update cfg.",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: cfgwindow.destroy(),
    )
    adv_cfg_done_button.grid(row=18, column=0, sticky="nsew", pady=20, padx=80)

    # maximise widgets to fit fullscreen
    maximise_widgets(cfgwindow)


# %%..............  LOCAL FUNCTION(S) #3 - BUILD ADD FEATURES WINDOW  ..................


def definefeatures_window(
    mainwindow, group_names, group_dirs, results_dir, load_dir, which_leg, root
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

    # ...................  EXTRACT FEATURES FROM AN AVERAGE SC XLS  ....................
    # => Only needed if not loading a previous run (note there is a check for features
    #    being present in all dfs in load_previous_runs_dataframes in group_main)
    # => First read the xls as df, extract columns that are meaningful after
    #    averaging, or throw errors if we don't manage to do so
    #    -- (note we extract from average xls since that automatically informs about
    #        export_average_x/y vars!)
    if len(load_dir.get()) > 0:
        group_one_string = group_names[0].get()
        load_dir_string = load_dir.get()
        df = pd.read_excel(
            os.path.join(
                load_dir_string, f"{group_one_string} - {AVG_GROUP_SHEET_NAME}.xlsx"
            )
        )
    else:
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
        if not os.path.exists(results_dir.get()):
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
            # next operator means we loop lazy - stop once we find it & return None if av
            # sheet not in dir
            av_sheet_path = next(
                (file for file in IDs_files if NORM_SHEET_NAME in file), None
            )
            if av_sheet_path:  # won't be true if no AVXLS found
                full_path = os.path.join(some_IDs_dir, av_sheet_path)
                if av_sheet_path.endswith(".xlsx"):
                    try:
                        # universal 3D (that has which_leg sheets) always exports xlsx
                        df = pd.read_excel(full_path, sheet_name=which_leg.get())
                    except:
                        df = pd.read_excel(full_path)
                    break
                elif av_sheet_path.endswith(".csv"):
                    df = pd.read_csv(full_path)
                    break
    # select columns we want to provide as feature options using regular expressions
    # => since it's on av sheet, x & Y will only be included if export_average_x/Y was
    #    True @ first-level
    if df is not None:
        feature_strings = tuple(
            df.filter(regex="(x$|y$|Y$|Z$|Angle$|Velocity$|Acceleration$)").columns
        )
    else:
        error_string = "Unable to find any Average SC sheet at " + some_groups_dir
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
    stats_label = gaita_widgets.header_label(featureswindow, "Statistics", WIDGET_CFG)
    stats_label.grid(row=0, column=0, sticky="nsew")
    # PCA label
    PCA_label = gaita_widgets.header_label(featureswindow, "PCA", WIDGET_CFG)
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
    for frame in [stats_frame, PCA_frame]:
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
            this_checkbox = gaita_widgets.checkbox(frame, feature, var, WIDGET_CFG)
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

    # run
    run_button = gaita_widgets.header_button(
        featureswindow, "I am ready - run analysis!", WIDGET_CFG
    )
    run_button.configure(
        command=lambda: (
            build_donewindow(
                group_names,
                group_dirs,
                results_dir,
                load_dir,
                root,
                mainwindow,
                featureswindow,
            ),
            get_selected_variables(),
        ),
    )
    run_button.grid(
        row=1 + scrollbar_rows, column=0, columnspan=2, sticky="nsew", pady=20, padx=200
    )

    # maximise widgets to fit fullscreen
    maximise_widgets(featureswindow)


# %%..................  LOCAL FUNCTION(S) #4 - BUILD DONE WINDOW  ......................
def build_donewindow(
    group_names, group_dirs, results_dir, load_dir, root, mainwindow, featureswindow
):
    """Build done window"""
    # create done window & make it pretty and nice
    w = screen_width
    h = screen_height
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

    # ..................................................................................
    # ........................  IMPORTANT - prepare folderinfo .........................
    # ..................................................................................
    folderinfo = {
        "group_names": [],
        "group_dirs": [],
        "results_dir": "",
        "load_dir": "",
    }
    for g in range(len(group_names)):
        folderinfo["group_names"].append(group_names[g].get())
        folderinfo["group_dirs"].append(group_dirs[g].get())
    folderinfo["results_dir"] = results_dir.get()
    folderinfo["load_dir"] = load_dir.get()

    # run button
    done_button = ctk.CTkButton(
        donewindow,
        text="Run!",
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR,
        font=(HEADER_FONT_NAME, MAIN_HEADER_FONT_SIZE),
        command=lambda: (
            update_config_file(folderinfo, cfg),
            run_analysis(folderinfo, cfg),
            mainwindow.destroy(),
            featureswindow.destroy(),
            donewindow.destroy(),
            root.deiconify(),
        ),
    )
    done_button.grid(row=4, column=0, sticky="nsew", pady=10, padx=200)

    maximise_widgets(donewindow)


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
        target=autogaita.group, args=(this_runs_folderinfo, this_runs_cfg)
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
                if key == "group_dirs" and len(folderinfo["load_dir"]) > 0:
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
    # of autogaita.group, we will convert os.sep to forward slashes if they should be
    # backward slashes (windows works with both)
    # => The part that does this in autogaita.group was updated and uses os.path.join
    # => Thought about changing strings to Paths here but will leave it for now it works
    for key in folderinfo.keys():
        if key == "group_names":
            this_runs_folderinfo[key] = folderinfo[key]
        if "dir" in key:
            if isinstance(folderinfo[key], list):  # group_dirs
                this_runs_folderinfo[key] = [[] for _ in range(len(folderinfo[key]))]
                for i in range(len(folderinfo[key])):
                    if not folderinfo[key][i].endswith(os.sep):
                        this_runs_folderinfo[key][i] = folderinfo[key][i] + "/"
                    else:
                        this_runs_folderinfo[key][i] = folderinfo[key][i]
            # results_dir and load_dir (check load_dir only if not empty)
            elif key in ["results_dir", "load_dir"]:
                if len(folderinfo[key]) > 0 and not folderinfo[key].endswith(os.sep):
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


def change_ANOVA_buttons_state(ANOVA_buttons):
    """Change the state of ANOVA radio button widgets based on whether user wants
    to perform an ANOVA or not.
    """
    if cfg["do_anova"].get() is True:
        for i in range(len(ANOVA_buttons)):
            ANOVA_buttons[i].configure(state="normal")
    elif cfg["do_anova"].get() is False:
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


def update_config_file(folderinfo, cfg):
    """updates the group_gui_config file with this folderinfo and cfg parameters"""
    # transform tkVars into normal strings and bools
    output_dicts = [
        {"group_names": [], "group_dirs": [], "results_dir": "", "load_dir": ""},
        {},
    ]

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
                ):  # not PCA or Stats variables
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


def extract_results_and_load_dirs_from_json_files():
    """loads the results dir from the config file"""
    # load the configuration file
    with open(
        os.path.join(AUTOGAITA_FOLDER_PATH, CONFIG_FILE_NAME), "r"
    ) as config_json_file:
        # config_json contains list with 0 -> folderinfo and 1 -> cfg data
        last_runs_folderinfo = json.load(config_json_file)[0]

    results_dir = last_runs_folderinfo["results_dir"]
    load_dir = last_runs_folderinfo["load_dir"]

    return results_dir, load_dir


# %% what happens if we hit run
if __name__ == "__main__":
    run_group_gui()

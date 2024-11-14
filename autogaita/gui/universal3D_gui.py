# %% imports
import autogaita.gui.gaita_widgets as gaita_widgets
import autogaita.gui.gui_utils as gui_utils
from autogaita.gui.first_level_gui_utils import (
    update_config_file,
    extract_cfg_from_json_file,
    extract_results_from_json_file,
)
from autogaita.gaita_res.utils import try_to_run_gaita
from autogaita.universal3D.universal3D_datafile_preparation import prepare_3D
import tkinter as tk
import customtkinter as ctk
import os
from threading import Thread
import platform


# %% global constants
from autogaita.gui.gui_constants import (
    UNIVERSAL3D_FG_COLOR,
    UNIVERSAL3D_HOVER_COLOR,
    HEADER_FONT_NAME,
    HEADER_FONT_SIZE,
    MAIN_HEADER_FONT_SIZE,
    TEXT_FONT_NAME,
    TEXT_FONT_SIZE,
    ADV_CFG_TEXT_FONT_SIZE,
    CLOSE_COLOR,
    CLOSE_HOVER_COLOR,
    COLOR_PALETTES_LIST,
    WINDOWS_TASKBAR_MAXHEIGHT,
    AUTOGAITA_FOLDER_PATH,
    get_widget_cfg_dict,  # function!
)

# these colors are GUI-specific - add to common widget cfg
FG_COLOR = UNIVERSAL3D_FG_COLOR
HOVER_COLOR = UNIVERSAL3D_HOVER_COLOR
WIDGET_CFG = get_widget_cfg_dict()
WIDGET_CFG["FG_COLOR"] = FG_COLOR
WIDGET_CFG["HOVER_COLOR"] = HOVER_COLOR

CONFIG_FILE_NAME = "universal3D_gui_config.json"
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
    "analyse_average_y",
    "legend_outside",
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
    "color_palette",
    "fileprep_root_dir",  # for datafile prep window only
    "fileprep_filetype",
    "fileprep_postname_string",
    "fileprep_results_dir",
    "fileprep_separator",
    "fileprep_string_to_remove",
]


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


def run_universal3D_gui():
    # ..........................................................................
    # ......................  root window initialisation .......................
    # ..........................................................................
    # Check for config file
    config_file_path = os.path.join(AUTOGAITA_FOLDER_PATH, CONFIG_FILE_NAME)
    if not os.path.isfile(config_file_path):
        config_file_error_msg = (
            "universal3D_gui_config.json file not found in autogaita folder.\n"
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
    root.title("Universal 3D GaitA")
    gui_utils.fix_window_after_its_creation(root)
    gui_utils.configure_the_icon(root)

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

    cfg = extract_cfg_from_json_file(
        root,
        AUTOGAITA_FOLDER_PATH,
        CONFIG_FILE_NAME,
        LIST_VARS,
        DICT_VARS,
        TK_STR_VARS,
        TK_BOOL_VARS,
    )
    results = extract_results_from_json_file(
        root, AUTOGAITA_FOLDER_PATH, CONFIG_FILE_NAME, TK_STR_VARS, TK_BOOL_VARS
    )

    # .........................  main configuration  ...................................
    # config header
    cfgheader_label = gaita_widgets.header_label(root, "Main Configuration", WIDGET_CFG)
    cfgheader_label.grid(row=0, column=0, columnspan=2, sticky="nsew")

    # root directory
    rootdir_label, rootdir_entry = gaita_widgets.label_and_entry_pair(
        root,
        "Directory containing the files to be analysed:",
        results["root_dir"],
        WIDGET_CFG,
    )
    rootdir_label.grid(row=1, column=0, columnspan=2, sticky="w")
    rootdir_entry.grid(row=1, column=1)

    # stepcycle latency XLS
    SCXLS_label, SCXLS_entry = gaita_widgets.label_and_entry_pair(
        root,
        "Name of the Annotation Table Excel file:",
        results["sctable_filename"],
        WIDGET_CFG,
    )
    SCXLS_label.grid(row=2, column=0, columnspan=2, sticky="w")
    SCXLS_entry.grid(row=2, column=1)

    # sampling rate
    samprate_label, samprate_entry = gaita_widgets.label_and_entry_pair(
        root,
        "Sampling rate of videos in Hertz (frames/second):",
        cfg["sampling_rate"],
        WIDGET_CFG,
    )
    samprate_label.grid(row=3, column=0, columnspan=2, sticky="w")
    samprate_entry.grid(row=3, column=1)

    # postname present checkbox
    postname_flag_checkbox = gaita_widgets.checkbox(
        root,
        "I have a constant string that follows IDs in filenames.",
        results["postname_flag"],
        WIDGET_CFG,
    )
    postname_flag_checkbox.configure(
        command=lambda: gui_utils.change_postname_entry_state(results, postname_entry),
    )
    postname_flag_checkbox.grid(row=4, column=0, columnspan=2)

    # postname string
    postname_label, postname_entry = gaita_widgets.label_and_entry_pair(
        root,
        "The constant string is:",
        results["postname_string"],
        WIDGET_CFG,
    )
    postname_label.grid(row=5, column=0, sticky="e")
    postname_entry.configure(state="disabled")
    postname_entry.grid(row=5, column=1, sticky="w")

    # empty label 1 (for spacing)
    empty_label_one = ctk.CTkLabel(root, text="")
    empty_label_one.grid(row=8, column=0)

    # ..........................  advanced cfg section  ................................

    # advanced header string
    advanced_cfg_header_label = gaita_widgets.header_label(
        root, "Advanced Configuration", WIDGET_CFG
    )
    advanced_cfg_header_label.grid(row=9, column=0, columnspan=2, sticky="nsew")

    # data file preparation window
    datafile_prep_button = gaita_widgets.header_button(
        root, "Data File Preparation", WIDGET_CFG
    )
    datafile_prep_button.configure(
        command=lambda: build_datafile_prep_window(root, results, cfg),
    )
    datafile_prep_button.grid(row=10, column=0, columnspan=2)

    # column name information window
    column_info_button = gaita_widgets.header_button(
        root, "Customise Joints & Angles", WIDGET_CFG
    )
    column_info_button.configure(
        command=lambda: build_column_info_window(root, cfg, root_dimensions),
    )
    column_info_button.grid(row=11, column=0, columnspan=2)

    # advanced cfg
    cfg_window_button = gaita_widgets.header_button(
        root, "Advanced Configuration", WIDGET_CFG
    )
    cfg_window_button.configure(
        command=lambda: (build_cfg_window(root, cfg)),
    )
    cfg_window_button.grid(row=12, column=0, columnspan=2)

    # empty label 2 (for spacing)
    empty_label_two = ctk.CTkLabel(root, text="")
    empty_label_two.grid(row=13, column=0)

    # ............................  run & exit section  ................................

    # run analysis label
    runheader_label = gaita_widgets.header_label(root, "Run Analysis", WIDGET_CFG)
    runheader_label.grid(row=14, column=0, columnspan=2, sticky="nsew")

    # single video checkbox
    singlevideo_checkbox = gaita_widgets.checkbox(
        root,
        "Only analyse a single dataset.",
        cfg["analyse_singlerun"],
        WIDGET_CFG,
    )
    singlevideo_checkbox.configure(
        command=lambda: gui_utils.change_ID_entry_state(cfg, ID_entry),
    )
    singlevideo_checkbox.grid(row=15, column=0, columnspan=2)

    # ID string info
    ID_label, ID_entry = gaita_widgets.label_and_entry_pair(
        root, "ID to be analysed:", results["name"], WIDGET_CFG
    )
    ID_label.grid(row=16, column=0, sticky="e")
    ID_entry.grid(row=16, column=1, sticky="w")
    gui_utils.change_ID_entry_state(cfg, ID_entry)

    # run analysis button
    run_button = gaita_widgets.header_button(root, "Run Analysis!", WIDGET_CFG)
    run_button.configure(
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
            build_donewindow(results, root, root_dimensions),
        )
    )
    run_button.grid(row=17, column=0, columnspan=2, padx=10, pady=(10, 5))

    # empty label 3 (for spacing)
    empty_label_three = ctk.CTkLabel(root, text="")
    empty_label_three.grid(row=18, column=0)

    # close program button
    exit_button = gaita_widgets.exit_button(
        root,
        WIDGET_CFG,
    )
    exit_button.configure(
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
            root.withdraw(),
            root.after(5000, root.destroy),
        ),
    )
    exit_button.grid(row=19, column=0, columnspan=2, padx=10, pady=(10, 5))

    # maximise widgets
    gui_utils.maximise_widgets(root)
    root.columnconfigure(list(range(2)), weight=1, uniform="Silent_Creme")

    # main loop
    root.mainloop()


# %%..............  LOCAL FUNCTION(S) #1 - BUILD DATAFILE PREP WINDOW  .................
def build_datafile_prep_window(root, results, cfg):
    """Build data file preparation window"""
    # unpack root window dimensions
    screen_width = root.winfo_screenwidth()  # width of the screen
    screen_height = root.winfo_screenheight()  # height of the screen
    # build window
    fileprep_window = ctk.CTkToplevel(root)
    fileprep_window.title("Datafile Preparation")
    fileprep_window.geometry(
        f"{int(screen_width / 2)}x{int(screen_height / 1.5)}+{int(screen_width / 4)}+{int(screen_height / 6)}"
    )
    gui_utils.fix_window_after_its_creation(fileprep_window)

    # fileprep header
    fileprep_header_label = gaita_widgets.header_label(
        fileprep_window, "Datafile Preparation", WIDGET_CFG
    )
    fileprep_header_label.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="nsew")
    # root dir
    fileprep_root_dir_label, fileprep_root_dir_entry = (
        gaita_widgets.label_and_entry_pair(
            fileprep_window,
            "Directory containing files:",
            cfg["fileprep_root_dir"],
            WIDGET_CFG,
        )
    )
    fileprep_root_dir_label.grid(row=2, column=0, sticky="e")
    fileprep_root_dir_entry.grid(row=2, column=1)
    # file type
    filetype_string = "File type:"
    filetype_label = ctk.CTkLabel(
        fileprep_window,
        text=filetype_string,
        font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
    )
    filetype_label.grid(row=3, column=0, columnspan=2)
    filetype_strings = ["csv", "xls", "xlsx"]
    filetype_buttons = []
    for i, string in enumerate(filetype_strings):
        filetype_buttons.append(
            ctk.CTkRadioButton(
                fileprep_window,
                text=string,
                variable=cfg["fileprep_filetype"],
                value=string,
                fg_color=FG_COLOR,
                hover_color=HOVER_COLOR,
                font=(TEXT_FONT_NAME, TEXT_FONT_SIZE),
            )
        )
        filetype_buttons[i].grid(row=4 + i, column=0, columnspan=2)
    row_num = 4 + len(filetype_strings)  # 7
    # postname string
    fileprep_postname_label, fileprep_postname_entry = (
        gaita_widgets.label_and_entry_pair(
            fileprep_window,
            "Constant string present in file names:",
            cfg["fileprep_postname_string"],
            WIDGET_CFG,
        )
    )
    fileprep_postname_label.grid(row=row_num, column=0, sticky="e")
    fileprep_postname_entry.grid(row=row_num, column=1)
    # results dir
    fileprep_results_dir_label, fileprep_results_dir_entry = (
        gaita_widgets.label_and_entry_pair(
            fileprep_window,
            "Directory to save results to:",
            cfg["fileprep_results_dir"],
            WIDGET_CFG,
        )
    )
    fileprep_results_dir_label.grid(row=row_num + 1, column=0, sticky="e")
    fileprep_results_dir_entry.grid(row=row_num + 1, column=1)
    # empty label for spacing
    empty_label_one = ctk.CTkLabel(fileprep_window, text="")
    empty_label_one.grid(row=row_num + 2, column=0)

    # ............................  left section: clean  ...............................
    # cleaning header
    clean_header_label = gaita_widgets.header_label(
        fileprep_window, "Clean Columns", WIDGET_CFG
    )
    clean_header_label.grid(row=row_num + 3, column=0, sticky="nsew")
    # string to remove
    string_to_remove_label, string_to_remove_entry = gaita_widgets.label_and_entry_pair(
        fileprep_window,
        "Substring to remove:",
        cfg["fileprep_string_to_remove"],
        WIDGET_CFG,
    )
    string_to_remove_label.grid(row=row_num + 4, column=0)
    string_to_remove_entry.grid(row=row_num + 5, column=0)
    # cleaning run button
    clean_button = gaita_widgets.header_button(fileprep_window, "Clean!", WIDGET_CFG)
    clean_button.configure(
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
            run_universal_3D_preparation("clean", cfg),
        )
    )
    clean_button.grid(row=row_num + 6, column=0, sticky="nsew", padx=10, pady=(10, 5))

    # ............................  right section: rename  .............................
    # renaming header
    rename_header_label = gaita_widgets.header_label(
        fileprep_window, "Rename Columns", WIDGET_CFG
    )
    rename_header_label.grid(row=row_num + 3, column=1, sticky="nsew")
    # separator
    separator_label, separator_entry = gaita_widgets.label_and_entry_pair(
        fileprep_window,
        "Separator substring (must be unique!):",
        cfg["fileprep_separator"],
        WIDGET_CFG,
    )
    separator_label.grid(row=row_num + 4, column=1)
    separator_entry.grid(row=row_num + 5, column=1)
    # renaming run button
    rename_button = gaita_widgets.header_button(fileprep_window, "Rename!", WIDGET_CFG)
    rename_button.configure(
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
            run_universal_3D_preparation("rename", cfg),
        )
    )
    rename_button.grid(row=row_num + 6, column=1, sticky="nsew", padx=10, pady=(10, 5))

    # ............................  bottom section: done  ..............................
    # empty label two
    empty_label_two = ctk.CTkLabel(fileprep_window, text="")
    empty_label_two.grid(row=row_num + 7, column=0)
    # done button
    done_button = ctk.CTkButton(
        fileprep_window,
        text="I am done!",
        fg_color=CLOSE_COLOR,
        hover_color=CLOSE_HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: fileprep_window.destroy(),
    )
    done_button.grid(
        row=row_num + 7, column=0, columnspan=2, padx=30, pady=(10, 5), sticky="ew"
    )
    # maximise widgets
    gui_utils.maximise_widgets(fileprep_window)


def run_universal_3D_preparation(task, cfg):
    """Call the autogaita_3D_preparation function with appropriate arguments"""
    # create separate cfg dict for fileprep function to avoid changing the main cfg
    fileprep_cfg = {}
    fileprep_cfg["root_dir"] = cfg["fileprep_root_dir"].get()
    fileprep_cfg["file_type"] = cfg["fileprep_filetype"].get()
    fileprep_cfg["postname_string"] = cfg["fileprep_postname_string"].get()
    fileprep_cfg["results_dir"] = cfg["fileprep_results_dir"].get()
    # set the appropriate kwargs based on the task
    if task == "clean":
        string_to_remove = cfg["fileprep_string_to_remove"].get()
        kwargs = {"string_to_remove": string_to_remove}
    elif task == "rename":
        separator = cfg["fileprep_separator"].get()
        kwargs = {"separator": separator}
    # run the function, with kwargs depending on task, & show info for users
    info_message = prepare_3D(task, fileprep_cfg, **kwargs)
    tk.messagebox.showinfo(title="Info", message=info_message)


# %%..........  LOCAL FUNCTION(S) #2 - BUILD ADVANCED CFG WINDOW  .............


def build_cfg_window(root, cfg):
    """Build advanced configuration window"""
    # unpack root window dimensions
    screen_width = root.winfo_screenwidth()  # width of the screen
    screen_height = root.winfo_screenheight()  # height of the screen
    # build window
    cfg_window = ctk.CTkToplevel(root)
    cfg_window.title("Advanced Configuration")
    cfg_window.geometry(
        f"{int(screen_width / 2)}x{screen_height}+{int(screen_width / 4)}+0"
    )
    gui_utils.fix_window_after_its_creation(cfg_window)

    #  ...........................  advanced analysis  .................................
    # advanced analysis header
    adv_cfg_analysis_header_label = gaita_widgets.header_label(
        cfg_window, "Analysis", WIDGET_CFG
    )
    adv_cfg_analysis_header_label.grid(row=0, column=0, rowspan=2, sticky="nsew")
    # bin_num
    bin_num_label, bin_num_entry = gaita_widgets.label_and_entry_pair(
        cfg_window,
        "Number of bins to use for normalising the step cycle:",
        cfg["bin_num"],
        WIDGET_CFG,
        adv_cfg_textsize=True,
    )
    bin_num_label.grid(row=2, column=0)
    bin_num_entry.grid(row=3, column=0)
    # y acceleration
    y_accel_box = gaita_widgets.checkbox(
        cfg_window,
        "Compute, plot & export joints' Y-accelerations",
        cfg["y_acceleration"],
        WIDGET_CFG,
        adv_cfg_textsize=True,
    )
    y_accel_box.grid(row=4, column=0)
    # angular acceleration
    angular_accel_box = gaita_widgets.checkbox(
        cfg_window,
        "Compute, plot & export angular accelerations",
        cfg["angular_acceleration"],
        WIDGET_CFG,
        adv_cfg_textsize=True,
    )
    angular_accel_box.grid(row=5, column=0)
    # height normalisation at each step cycle separately
    height_normalisation_box = gaita_widgets.checkbox(
        cfg_window,
        "Normalise heights of all step cycles separately",
        cfg["normalise_height_at_SC_level"],
        WIDGET_CFG,
        adv_cfg_textsize=True,
    )
    height_normalisation_box.grid(row=6, column=0)
    # export average y coordinates
    analyse_average_y_box = gaita_widgets.checkbox(
        cfg_window,
        "Analyse y-coordinate averages",
        cfg["analyse_average_y"],
        WIDGET_CFG,
        adv_cfg_textsize=True,
    )
    analyse_average_y_box.grid(row=7, column=0)

    #  .............................  advanced output  .................................
    # advanced output header
    adv_cfg_output_header_label = gaita_widgets.header_label(
        cfg_window, "Output", WIDGET_CFG
    )
    adv_cfg_output_header_label.grid(row=8, column=0, rowspan=2, sticky="nsew")
    # number of joints to plot
    plot_joint_num_label, plot_joint_num_entry = gaita_widgets.label_and_entry_pair(
        cfg_window,
        "Number of joints to plot in detail:",
        cfg["plot_joint_number"],
        WIDGET_CFG,
        adv_cfg_textsize=True,
    )
    plot_joint_num_label.grid(row=10, column=0)
    plot_joint_num_entry.grid(row=11, column=0)
    # plot plots to python
    showplots_checkbox = gaita_widgets.checkbox(
        cfg_window,
        "Don't show plots in GUI (save only)",
        cfg["dont_show_plots"],
        WIDGET_CFG,
        adv_cfg_textsize=True,
    )
    showplots_checkbox.grid(row=12, column=0)
    # plot SE
    plot_SE_box = gaita_widgets.checkbox(
        cfg_window,
        "Use standard error instead of standard deviation for plots",
        cfg["plot_SE"],
        WIDGET_CFG,
        adv_cfg_textsize=True,
    )
    plot_SE_box.grid(row=13, column=0)
    # color palette
    color_palette_string = "Choose figures' color palette"
    color_palette_label = ctk.CTkLabel(
        cfg_window,
        text=color_palette_string,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    color_palette_label.grid(row=14, column=0)
    color_palette_entry = ctk.CTkOptionMenu(
        cfg_window,
        values=COLOR_PALETTES_LIST,
        variable=cfg["color_palette"],
        fg_color=FG_COLOR,
        button_color=FG_COLOR,
        button_hover_color=HOVER_COLOR,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    color_palette_entry.grid(row=15, column=0)
    # legend outside
    legend_outside_checkbox = gaita_widgets.checkbox(
        cfg_window,
        "Plot legends outside of figures' panels",
        cfg["legend_outside"],
        WIDGET_CFG,
        adv_cfg_textsize=True,
    )
    legend_outside_checkbox.grid(row=16, column=0)

    # results dir
    results_dir_label, results_dir_entry = gaita_widgets.label_and_entry_pair(
        cfg_window,
        "Save Results subfolders to directory below instead of to data's",
        cfg["results_dir"],
        WIDGET_CFG,
        adv_cfg_textsize=True,
    )
    results_dir_label.grid(row=17, column=0)
    results_dir_entry.grid(row=18, column=0)

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
        row=19, column=0, rowspan=2, sticky="nsew", padx=10, pady=(10, 5)
    )
    # maximise widgets
    cfg_window.columnconfigure(0, weight=1, uniform="Silent_Creme")
    cfg_window.rowconfigure(list(range(20)), weight=1, uniform="Silent_Creme")


# %%..............  LOCAL FUNCTION(S) #3 - BUILD COLUMN INFO WINDOW  ...................
def build_column_info_window(root, cfg, root_dimensions):
    """Build a window allowing users to configure custom column names if required"""
    columnwindow = ctk.CTkToplevel(root)
    columnwindow.geometry("%dx%d+%d+%d" % root_dimensions)
    columnwindow.title("Custom column names & features")
    gui_utils.fix_window_after_its_creation(columnwindow)

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
            label, entry = gaita_widgets.label_and_entry_pair(
                window,
                "Joint #" + str(len(cfg[key])),
                cfg[key][-1],
                WIDGET_CFG,
            )
            label.grid(row=nrows + 1, column=0, sticky="ew")
            entry.grid(row=nrows + 2, column=0)
        elif key == "angles":
            for a, angle_key in enumerate(cfg[key]):
                if angle_key == "name":
                    this_case = "Angle"
                elif angle_key == "lower_joint":
                    this_case = "Lower Joint"
                elif angle_key == "upper_joint":
                    this_case = "Upper Joint"
                label, entry = gaita_widgets.label_and_entry_pair(
                    window,
                    this_case + " #" + str(len(cfg[key][angle_key])),
                    cfg[key][angle_key][-1],
                    WIDGET_CFG,
                )
                label.grid(row=nrows + 1, column=angle_column + a, sticky="ew")
                entry.grid(row=nrows + 2, column=angle_column + a)
        # maximise columns
        for c in range(window.grid_size()[0]):
            window.grid_columnconfigure(c, weight=1)

    # ...................  Scrollable Window Configuration  ............................
    scrollable_rows = 8

    # ...................  Column 0: hind limb joint names  ............................
    joint_column = 0
    # header label
    joint_label = gaita_widgets.header_label(columnwindow, "Joints", WIDGET_CFG)
    joint_label.grid(row=0, column=joint_column, sticky="nsew", pady=(0, 5))
    # initialise scrollable frame for joints
    joint_frame = ctk.CTkScrollableFrame(columnwindow)
    joint_frame.grid(row=1, column=joint_column, rowspan=scrollable_rows, sticky="nsew")
    # initialise labels & entries with joint defaults
    initialise_labels_and_entries(joint_frame, "joints", "Joint ")
    # add joint button
    add_joint_button = gaita_widgets.header_button(
        columnwindow, "Add joint", WIDGET_CFG
    )
    add_joint_button.configure(
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
    angle_label = gaita_widgets.header_label(
        columnwindow, "Angle Configuration", WIDGET_CFG
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
    add_angle_button = gaita_widgets.header_button(
        columnwindow, "Add angle", WIDGET_CFG
    )
    add_angle_button.configure(
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
        fg_color=CLOSE_COLOR,
        hover_color=CLOSE_HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        command=lambda: (columnwindow.destroy()),
    )
    columncfg_done_button.grid(
        row=3 + scrollable_rows,
        column=joint_column,
        columnspan=4,
        sticky="nsew",
        padx=200,
        pady=10,
    )
    # maximise everything in columnwindow
    gui_utils.maximise_widgets(columnwindow)


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


# %%..................  LOCAL FUNCTION(S) #4 - BUILD DONE WINDOW  ......................
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
            run_analysis(this_runs_results, this_runs_cfg),
            donewindow.destroy(),
        ),
    )
    done_button.grid(row=4, column=0, sticky="nsew", pady=10, padx=200)

    gui_utils.maximise_widgets(donewindow)


# %%..........  LOCAL FUNCTION(S) #5 - PREPARE & CALL AUTOGAITA  ....................


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
    """Prepare for one execution of autogaita_universal3D & execute"""
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
    try_to_run_gaita("Universal 3D", this_info, this_folderinfo, this_runs_cfg, False)


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
    try_to_run_gaita("Universal 3D", this_info, this_folderinfo, this_runs_cfg, True)


# %%..............  LOCAL FUNCTION(S) #6 - VARIOUS HELPER FUNCTIONS  ...................


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


# %% what happens if we hit run
if __name__ == "__main__":
    run_universal3D_gui()

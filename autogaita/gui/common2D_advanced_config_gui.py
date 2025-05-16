# %%...............  SHARED 2D WINDOW - ADVANCED CONFIGURATION  ........................
import autogaita.gui.gui_utils as gui_utils
import autogaita.gui.gaita_widgets as gaita_widgets
import customtkinter as ctk
from autogaita.gui.gui_utils import create_folder_icon
import tkinter as tk
import os
from tkinter import filedialog
from customtkinter import CTkImage


def build_cfg_window(root, cfg, widget_cfg, root_dimensions):
    """Build advanced configuration window"""
    # unpack root window dimensions
    w = root_dimensions[0]
    h = root_dimensions[1]
    # build window
    cfg_window = ctk.CTkToplevel(root)
    cfg_window.title("Advanced Configuration")
    cfg_window.geometry(f"{int(w / 2)}x{h}+{int(w / 4)}+0")
    gui_utils.fix_window_after_its_creation(cfg_window)

    # unpack
    FG_COLOR = widget_cfg["FG_COLOR"]
    HOVER_COLOR = widget_cfg["HOVER_COLOR"]
    HEADER_FONT_NAME = widget_cfg["HEADER_FONT_NAME"]
    HEADER_FONT_SIZE = widget_cfg["HEADER_FONT_SIZE"]
    CLOSE_COLOR = widget_cfg["CLOSE_COLOR"]
    CLOSE_HOVER_COLOR = widget_cfg["CLOSE_HOVER_COLOR"]
    TEXT_FONT_NAME = widget_cfg["TEXT_FONT_NAME"]
    ADV_CFG_TEXT_FONT_SIZE = widget_cfg["ADV_CFG_TEXT_FONT_SIZE"]
    COLOR_PALETTES_LIST = widget_cfg["COLOR_PALETTES_LIST"]

    # advanced analysis header
    adv_cfg_analysis_header_label = gaita_widgets.header_label(
        cfg_window,
        "Analysis",
        widget_cfg,
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
    standardise_y_at_SC_level_box = gaita_widgets.checkbox(
        cfg_window,
        "Standardise y-coordinates separately for all step cycles",
        cfg["standardise_y_at_SC_level"],
        widget_cfg,
        adv_cfg_textsize=True,
    )
    standardise_y_at_SC_level_box.grid(row=7, column=0, columnspan=2)

    # y standardisation to a specific joint not global minimum
    standardise_y_to_joint_box = gaita_widgets.checkbox(
        cfg_window,
        "Standardise y to a joint instead of to global minimum",
        cfg["standardise_y_to_a_joint"],
        widget_cfg,
        adv_cfg_textsize=True,
    )
    standardise_y_to_joint_box.configure(
        command=lambda: gui_utils.change_widget_state_based_on_checkbox(
            cfg, "standardise_y_to_a_joint", y_standardisation_joint_entry
        ),
    )
    standardise_y_to_joint_box.grid(row=8, column=0, columnspan=2)

    # y standardisation joint string label & entry
    y_standardisation_joint_label, y_standardisation_joint_entry = (
        gaita_widgets.label_and_entry_pair(
            cfg_window,
            "Y-standardisation joint:",
            cfg["y_standardisation_joint"][0],
            widget_cfg,
            adv_cfg_textsize=True,
        )
    )
    y_standardisation_joint_label.grid(row=9, column=0, sticky="e")
    y_standardisation_joint_entry.grid(row=9, column=1, sticky="w")
    # to initialise the widget correctly, run this function once
    gui_utils.change_widget_state_based_on_checkbox(
        cfg, "standardise_y_to_a_joint", y_standardisation_joint_entry
    )

    # analyse average x coordinates
    analyse_average_x_box = gaita_widgets.checkbox(
        cfg_window,
        "Analyse x-coordinate averages",
        cfg["analyse_average_x"],
        widget_cfg,
        adv_cfg_textsize=True,
    )
    analyse_average_x_box.configure(
        command=lambda: gui_utils.change_widget_state_based_on_checkbox(
            cfg, "analyse_average_x", standardise_x_coordinates_box
        ),
    )
    analyse_average_x_box.grid(row=10, column=0)

    # standardise x coordinates
    standardise_x_coordinates_box = gaita_widgets.checkbox(
        cfg_window,
        "Standardise x-coordinates",
        cfg["standardise_x_coordinates"],
        widget_cfg,
        adv_cfg_textsize=True,
    )
    standardise_x_coordinates_box.configure(
        command=lambda: gui_utils.change_widget_state_based_on_checkbox(
            cfg, "standardise_x_coordinates", x_standardisation_joint_entry
        ),
    )
    standardise_x_coordinates_box.grid(row=10, column=1)
    gui_utils.change_widget_state_based_on_checkbox(
        cfg, "analyse_average_x", standardise_x_coordinates_box
    )

    # x standardisation joint string label & entry
    x_standardisation_joint_label, x_standardisation_joint_entry = (
        gaita_widgets.label_and_entry_pair(
            cfg_window,
            "X-standardisation joint:",
            cfg["x_standardisation_joint"][0],
            widget_cfg,
            adv_cfg_textsize=True,
        )
    )
    x_standardisation_joint_label.grid(row=11, column=0, sticky="e")
    x_standardisation_joint_entry.grid(row=11, column=1, sticky="w")
    gui_utils.change_widget_state_based_on_checkbox(
        cfg, "standardise_x_coordinates", x_standardisation_joint_entry
    )

    # invert y-axis
    if "invert_y_axis" in cfg.keys():
        invert_y_axis_box = gaita_widgets.checkbox(
            cfg_window,
            "Invert y-axis",
            cfg["invert_y_axis"],
            widget_cfg,
            adv_cfg_textsize=True,
        )
        invert_y_axis_box.grid(row=12, column=0, columnspan=2)

    # Standardise all (primary) joint coordinates by a fixed decimal value
    frame_coordinate_standardisation = ctk.CTkFrame(cfg_window, fg_color="transparent")
    frame_coordinate_standardisation.grid(row=13, column=0, columnspan=3, rowspan=2, sticky="w")
    cfg ["coordinate_standardisation_xls"] = tk.StringVar()

    # coordinate standardisation label & entry
    coordinate_standardisation_xls_label = ctk.CTkLabel(
        frame_coordinate_standardisation,
        text="Excel file for primary-joint coordinate standardisation:",
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE)
        )
    coordinate_standardisation_xls_label.grid(row=0, column=0, sticky="w", padx=10)
    coordinate_standardisation_xls_entry = ctk.CTkEntry(
        frame_coordinate_standardisation,
        width=250,
        font =(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    coordinate_standardisation_xls_entry.grid(row=0, column=1,pady=5, sticky="w")
    # browse coordinate_standardisation_xls function
    def browse_coordinate_standardisation_xls():
        filetypes = [("Excel files", "*.xlsx *.xls")]
        filename = filedialog.askopenfilename(filetypes= filetypes)
        
        if filename:
            coordinate_standardisation_xls_entry.delete(0, tk.END)
            coordinate_standardisation_xls_entry.insert(0, filename) 
            cfg["coordinate_standardisation_xls"].set(filename)
    # browse button
    folder_icon= create_folder_icon() 
    coordinate_standardisation_xls_button = ctk.CTkButton(
        frame_coordinate_standardisation,
        width=25,
        text="",
        image=folder_icon,
        command=browse_coordinate_standardisation_xls,
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR
    )
    coordinate_standardisation_xls_button.grid(row=0, column=2, pady=5)
   

    #  .............................  advanced output  .................................
    # advanced analysis header
    adv_cfg_output_header_label = gaita_widgets.header_label(
        cfg_window,
        "Output",
        widget_cfg,
    )
    adv_cfg_output_header_label.grid(
        row=15, column=0, rowspan=2, columnspan=2, sticky="nsew", pady=(10, 0)
    )

    # number of hindlimb (primary) joints to plot
    plot_joint_num__label, plot_joint_num_entry = gaita_widgets.label_and_entry_pair(
        cfg_window,
        "Number of primary joints to plot in detail:",
        cfg["plot_joint_number"],
        widget_cfg,
        adv_cfg_textsize=True,
    )
    plot_joint_num__label.grid(row=17, column=0, columnspan=2)
    plot_joint_num_entry.grid(row=18, column=0, columnspan=2)

    # save to xls
    save_to_xls_box = gaita_widgets.checkbox(
        cfg_window,
        "Save results as .xlsx instead of .csv files",
        cfg["save_to_xls"],
        widget_cfg,
        adv_cfg_textsize=True,
    )
    save_to_xls_box.grid(row=19, column=0, columnspan=2)

    # plot SE
    plot_SE_box = gaita_widgets.checkbox(
        cfg_window,
        "Use standard error instead of standard deviation for plots",
        cfg["plot_SE"],
        widget_cfg,
        adv_cfg_textsize=True,
    )
    plot_SE_box.grid(row=20, column=0, columnspan=2)

    # color palette
    color_palette_string = "Choose figures' color palette"
    color_palette_label = ctk.CTkLabel(
        cfg_window,
        text=color_palette_string,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    color_palette_label.grid(row=21, column=0, columnspan=2)
    color_palette_entry = ctk.CTkOptionMenu(
        cfg_window,
        values=COLOR_PALETTES_LIST,
        variable=cfg["color_palette"],
        fg_color=FG_COLOR,
        button_color=FG_COLOR,
        button_hover_color=HOVER_COLOR,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
    )
    color_palette_entry.grid(row=22, column=0, columnspan=2)

    # legend outside
    legend_outside_checkbox = gaita_widgets.checkbox(
        cfg_window,
        "Plot legends outside of figures' panels",
        cfg["legend_outside"],
        widget_cfg,
        adv_cfg_textsize=True,
    )
    legend_outside_checkbox.grid(row=23, column=0, columnspan=2)

    # results dir
    # Frame for results dir
    results_dir_frame = ctk.CTkFrame(cfg_window, fg_color="transparent")
    results_dir_frame.grid(row=24, column=0,columnspan=3, sticky="w")
    # results_dir label & entry
    results_dir_entry = ctk.CTkEntry(
        results_dir_frame,
        width=200,
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE),
         )
    results_dir_label = ctk.CTkLabel(
        results_dir_frame,
        text="Save Results subfolders to this directory instead of to data's:",
        font=(TEXT_FONT_NAME, ADV_CFG_TEXT_FONT_SIZE)
        )
    results_dir_label.grid(row=0, column=0, sticky="w", padx=10)
    results_dir_entry.grid(row=0, column=1,sticky="w")
    
    # browse results_dir function
    cfg["results_dir"] = tk.StringVar()
    
    def browse_results_dir():
        folder = filedialog.askdirectory()
        if folder:
            results_dir_entry.delete(0, tk.END)
            results_dir_entry.insert(0, folder)
            cfg["results_dir"].set(folder)
    # browse button 
    folder_icon = create_folder_icon()
    browse_results_dir_button = ctk.CTkButton(
        results_dir_frame,
        width=25,
        text="",
        image=folder_icon,
        command=browse_results_dir,
        fg_color=FG_COLOR,
        hover_color=HOVER_COLOR
        )
    browse_results_dir_button.grid(row=0, column=2, padx=(0, 10), sticky="w")
    
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
        row=26, column=0, columnspan=2, rowspan=2, sticky="nsew", padx=10, pady=(10, 5)
    )
    # maximise widgets
    cfg_window.columnconfigure(list(range(2)), weight=1, uniform="Silent_Creme")
    cfg_window.rowconfigure(list(range(25)), weight=1, uniform="Silent_Creme")

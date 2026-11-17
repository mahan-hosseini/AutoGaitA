# %% imports
import autogaita.gui.gaita_widgets as gaita_widgets
import autogaita.gui.gui_utils as gui_utils
from autogaita.group.group_cross_species import (
    prepare_cross_species_columns,
    cross_species_report_to_string,
)
from autogaita.group.group_constants import (
    CROSS_SPECIES_DIR_NAME,
    CROSS_SPECIES_JOINT_PREFIX,
)
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import os
import json

# %% constants
CFG_KEY = "cross_species_columns"  # key of the species dict in group_gui_config.json
DEFAULT_SPECIES_NUM = 2
DEFAULT_JOINT_NUM = 3
INFO_STRING = (
    "Name each species and list its joints. All species need the same number "
    + "of joints. For Universal 3D, enter joint names without the body side (e.g. "
    + " 'Midfoot', not 'Midfoot, left').\n\n"
    + "Rename Columns identifies each group's species, renames its joints (and the "
    + "angles at them) to Joint1, Joint2, ... and saves the results to a "
    + f"'{CROSS_SPECIES_DIR_NAME}' folder in each group's directory. Joints that "
    + "are not listed are dropped.\n\n"
    + f"Afterwards, use these '{CROSS_SPECIES_DIR_NAME}' folders as your group "
    + "directories (i.e. path to first level results) in main GUI."
)


# %% ..........................  cross species window  .................................


def cross_species_window(
    mainwindow, group_names, group_dirs, cfg, widget_cfg, config_file_path
):
    """Build the cross species preparation window

    Parameters
    ----------
    group_names, group_dirs : lists of tk.StringVar (the main window's entries)
    cfg : the group GUI's cfg dict - cfg[CFG_KEY] stores the species dict
    config_file_path : path of group_gui_config.json (the species dict is saved there)
    """
    window = ctk.CTkToplevel(mainwindow)
    window.title("Cross Species Preparation")
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    window.geometry(
        f"{int(screen_width * 0.6)}x{int(screen_height * 0.6)}"
        + f"+{int(screen_width * 0.2)}+{int(screen_height * 0.2)}"
    )
    gui_utils.fix_window_after_its_creation(window)

    # rows: one [species StringVar, [joint StringVars]] per species
    rows = initial_rows(window, cfg.get(CFG_KEY, {}))

    # nested functions (called by the edit buttons) - edit rows & rebuild the table
    def add_species():
        rows.append(
            [
                tk.StringVar(window, ""),
                [tk.StringVar(window, "") for _ in range(len(rows[0][1]))],
            ]
        )
        build_table(table_frame, rows, widget_cfg)

    def remove_species():
        if len(rows) > 1:
            rows.pop()
            build_table(table_frame, rows, widget_cfg)

    def add_joint():
        for _, joint_vars in rows:
            joint_vars.append(tk.StringVar(window, ""))
        build_table(table_frame, rows, widget_cfg)

    def remove_joint():
        if len(rows[0][1]) > 1:
            for _, joint_vars in rows:
                joint_vars.pop()
            build_table(table_frame, rows, widget_cfg)

    # header & info
    header_label = gaita_widgets.header_label(
        window, "Cross Species Preparation", widget_cfg
    )
    header_label.grid(row=0, column=0, sticky="nsew")
    info_label = ctk.CTkLabel(
        window,
        text=INFO_STRING,
        font=(widget_cfg["TEXT_FONT_NAME"], widget_cfg["ADV_CFG_TEXT_FONT_SIZE"]),
        wraplength=int(screen_width * 0.55),
        justify="left",
    )
    info_label.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    # species & joints table
    table_frame = ctk.CTkScrollableFrame(window, orientation="horizontal")
    table_frame.grid(row=2, column=0, sticky="nsew", padx=10)
    build_table(table_frame, rows, widget_cfg)

    # edit buttons
    edit_frame = ctk.CTkFrame(window, fg_color="transparent")
    edit_frame.grid(row=3, column=0, pady=10)
    edit_buttons = [
        ("+ Species", add_species),
        ("- Species", remove_species),
        ("+ Joint", add_joint),
        ("- Joint", remove_joint),
    ]
    for column, (button_text, button_command) in enumerate(edit_buttons):
        ctk.CTkButton(
            edit_frame,
            text=button_text,
            fg_color=widget_cfg["FG_COLOR"],
            hover_color=widget_cfg["HOVER_COLOR"],
            font=(widget_cfg["TEXT_FONT_NAME"], widget_cfg["TEXT_FONT_SIZE"]),
            command=button_command,
        ).grid(row=0, column=column, padx=5)

    # rename button
    rename_button = gaita_widgets.header_button(window, "Rename Columns", widget_cfg)
    rename_button.configure(
        command=lambda: rename_columns(
            window, rows, group_names, group_dirs, cfg, widget_cfg, config_file_path
        )
    )
    rename_button.grid(row=4, column=0, pady=10)

    window.grid_columnconfigure(0, weight=1)
    window.grid_rowconfigure(2, weight=1)


def initial_rows(window, saved_species_joints):
    """Build the rows' tk vars from the saved species dict (or default empty rows)"""
    if saved_species_joints:
        species_and_joints = list(saved_species_joints.items())
    else:
        species_and_joints = [("", [""] * DEFAULT_JOINT_NUM)] * DEFAULT_SPECIES_NUM
    joint_num = max(max(len(joints) for _, joints in species_and_joints), 1)
    return [
        [
            tk.StringVar(window, species),
            [
                tk.StringVar(window, joints[j] if j < len(joints) else "")
                for j in range(joint_num)
            ],
        ]
        for species, joints in species_and_joints
    ]


def build_table(table_frame, rows, widget_cfg):
    """(Re-)build the table of species (rows) & joints (columns)"""
    for child in table_frame.winfo_children():
        child.destroy()
    font = (widget_cfg["TEXT_FONT_NAME"], widget_cfg["TEXT_FONT_SIZE"])
    joint_num = len(rows[0][1])
    headers = ["Species"] + [
        CROSS_SPECIES_JOINT_PREFIX + str(j + 1) for j in range(joint_num)
    ]
    for column, header in enumerate(headers):
        ctk.CTkLabel(table_frame, text=header, font=font).grid(
            row=0, column=column, padx=5, pady=5
        )
    for row, (species_var, joint_vars) in enumerate(rows, start=1):
        for column, var in enumerate([species_var] + joint_vars):
            ctk.CTkEntry(table_frame, textvariable=var, font=font).grid(
                row=row, column=column, padx=5, pady=5
            )


def rename_columns(
    window, rows, group_names, group_dirs, cfg, widget_cfg, config_file_path
):
    """Collect the species dict, save it & run cross species preparation"""
    # collect species dict from the table (skip fully blank rows)
    species_joints = {}
    for species_var, joint_vars in rows:
        species = species_var.get().strip()
        joints = [var.get() for var in joint_vars]
        if not species and not any(joint.strip() for joint in joints):
            continue
        if not species:
            show_error("A species name is empty!", "Joints: " + ", ".join(joints))
            return
        if species in species_joints:
            show_error("Duplicate species!", f"{species} is listed more than once.")
            return
        species_joints[species] = joints
    # save to cfg & config file so it's there next time
    cfg[CFG_KEY] = species_joints
    save_species_joints_to_config_file(species_joints, config_file_path)
    # check group dirs before running
    group_names = [var.get() for var in group_names]
    group_dirs = [var.get() for var in group_dirs]
    for group_name, group_dir in zip(group_names, group_dirs):
        if not os.path.isdir(group_dir):
            show_error(
                "Folder not found!",
                f"No directory found for group {group_name} at:\n{group_dir}",
            )
            return
    # run
    try:
        report = prepare_cross_species_columns(group_names, group_dirs, species_joints)
    except Exception as error:
        show_error("Cross Species Preparation failed!", str(error))
        return
    build_report_window(window, report, widget_cfg)


def show_error(title, message):
    """Show an error message box & print it"""
    print(f"\n{title}\n{message}")
    messagebox.showerror(title=title, message=message)


def save_species_joints_to_config_file(species_joints, config_file_path):
    """Store the species dict in the cfg part (idx 1) of group_gui_config.json"""
    with open(config_file_path, "r") as config_json_file:
        configs_list = json.load(config_json_file)
    configs_list[1][CFG_KEY] = species_joints
    with open(config_file_path, "w") as config_json_file:
        json.dump(configs_list, config_json_file, indent=4)


def build_report_window(parent, report, widget_cfg):
    """List which species each group was identified as"""
    report_window = ctk.CTkToplevel(parent)
    report_window.title("Cross Species Preparation Done")
    screen_width = report_window.winfo_screenwidth()
    screen_height = report_window.winfo_screenheight()
    report_window.geometry(
        f"{int(screen_width * 0.5)}x{int(screen_height * 0.4)}"
        + f"+{int(screen_width * 0.25)}+{int(screen_height * 0.3)}"
    )
    gui_utils.fix_window_after_its_creation(report_window)

    header_label = gaita_widgets.header_label(
        report_window, "Please check the identified species", widget_cfg
    )
    header_label.grid(row=0, column=0, sticky="nsew")
    report_textbox = ctk.CTkTextbox(
        report_window,
        font=(widget_cfg["TEXT_FONT_NAME"], widget_cfg["ADV_CFG_TEXT_FONT_SIZE"]),
        wrap="none",
    )
    report_textbox.insert("1.0", cross_species_report_to_string(report))
    report_textbox.configure(state="disabled")
    report_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    hint_label = ctk.CTkLabel(
        report_window,
        text=f"Use the '{CROSS_SPECIES_DIR_NAME}' folders listed above as your group "
        + "directories.",
        font=(widget_cfg["TEXT_FONT_NAME"], widget_cfg["ADV_CFG_TEXT_FONT_SIZE"]),
    )
    hint_label.grid(row=2, column=0, sticky="nsew", padx=10)
    close_button = gaita_widgets.header_button(report_window, "Close", widget_cfg)
    close_button.configure(command=report_window.destroy)
    close_button.grid(row=3, column=0, pady=10)

    report_window.grid_columnconfigure(0, weight=1)
    report_window.grid_rowconfigure(1, weight=1)

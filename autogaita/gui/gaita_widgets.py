import customtkinter as ctk
import os
import tkinter as tk
from tkinter import filedialog
from autogaita.gui.gui_utils import create_folder_icon

# This script contains functions to create widgets that are shared across GUIs.


def header_label(
    window,
    header_string,
    widget_cfg,
):
    """Header labels"""
    return ctk.CTkLabel(
        window,
        text=header_string,
        fg_color=widget_cfg["FG_COLOR"],
        text_color=widget_cfg["HEADER_TXT_COLOR"],
        font=(widget_cfg["HEADER_FONT_NAME"], widget_cfg["MAIN_HEADER_FONT_SIZE"]),
    )


def header_button(window, button_string, widget_cfg):
    """Header button"""
    return ctk.CTkButton(
        window,
        text=button_string,
        fg_color=widget_cfg["FG_COLOR"],
        hover_color=widget_cfg["HOVER_COLOR"],
        font=(widget_cfg["HEADER_FONT_NAME"], widget_cfg["HEADER_FONT_SIZE"]),
    )


def exit_button(window, widget_cfg):
    """Exit button"""
    return ctk.CTkButton(
        window,
        text="Exit",
        fg_color=widget_cfg["CLOSE_COLOR"],
        hover_color=widget_cfg["CLOSE_HOVER_COLOR"],
        font=(widget_cfg["HEADER_FONT_NAME"], widget_cfg["HEADER_FONT_SIZE"]),
    )


def label_and_entry_pair(
    window, label_text, entry_variable, widget_cfg, adv_cfg_textsize=False
):
    """Flexible label & entry widget-pair"""
    label = ctk.CTkLabel(
        window,
        text=label_text,
        font=(widget_cfg["TEXT_FONT_NAME"], widget_cfg["TEXT_FONT_SIZE"]),
    )
    entry = ctk.CTkEntry(
        window,
        textvariable=entry_variable,
        font=(widget_cfg["TEXT_FONT_NAME"], widget_cfg["TEXT_FONT_SIZE"]),
    )
    if adv_cfg_textsize:
        label.configure(
            font=(widget_cfg["TEXT_FONT_NAME"], widget_cfg["ADV_CFG_TEXT_FONT_SIZE"])
        )
        entry.configure(
            font=(widget_cfg["TEXT_FONT_NAME"], widget_cfg["ADV_CFG_TEXT_FONT_SIZE"])
        )
    return label, entry


def checkbox(window, label_text, entry_variable, widget_cfg, adv_cfg_textsize=False):
    """Checkbox"""
    checkbox = ctk.CTkCheckBox(
        window,
        text=label_text,
        variable=entry_variable,
        onvalue=True,
        offvalue=False,
        hover_color=widget_cfg["HOVER_COLOR"],
        fg_color=widget_cfg["FG_COLOR"],
        font=(widget_cfg["TEXT_FONT_NAME"], widget_cfg["TEXT_FONT_SIZE"]),
    )
    if adv_cfg_textsize:
        checkbox.configure(
            font=(widget_cfg["TEXT_FONT_NAME"], widget_cfg["ADV_CFG_TEXT_FONT_SIZE"])
        )
    return checkbox


def make_browse(
    parent_window,
    row,  # row of frame in parent_window
    column,  # column of frame in parent_window
    widget_cfg,
    entry_width=300,  # usual width of entry, needs to be less than 300 for group gui
    columnspan=None,
    sticky=None,
    text_var=None,  # for group gui where we dont have var_dict => only set text_var
    var_key=None,  # key for text_var in var_dict e.g. root_dir, results_dir
    var_dict=None,  # dictionary of var_key e.g. cfg, results
    is_file=False,  # ask for directory instead of file
    filetypes=None,  # to set default filetype
    initial_dir=None,  # function to get initial directory
    pady=None,
    adv_cfg_textsize=False,  # if true, use ADV_CFG_TEXT_FONT_SIZE
):
    """Entry & Browse button - placed in a frame. Function takes a lot of optional parameters to be able to deal with all the different use cases of this button across our different GUIs."""

    if (
        text_var is None and var_dict is not None
    ):  # we either need var_key AND var_dict or only text_var
        if (
            var_key not in var_dict
        ):  # make sure not to overwerite existing variables, important for configs
            var_dict[var_key] = tk.StringVar()
        text_var = var_dict[var_key]

    if is_file:
        filetypes = [("Excel files", "*.xlsx *.xls")]  # default filetype

    if adv_cfg_textsize:
        font_setting = (
            widget_cfg["TEXT_FONT_NAME"],
            widget_cfg["ADV_CFG_TEXT_FONT_SIZE"],
        )
    else:
        font_setting = (widget_cfg["TEXT_FONT_NAME"], widget_cfg["TEXT_FONT_SIZE"])

    # Frame
    frame = ctk.CTkFrame(parent_window, fg_color="transparent")
    frame.grid(row=row, column=column, sticky=sticky, columnspan=columnspan, pady=pady)

    # Entry
    entry = ctk.CTkEntry(
        frame, textvariable=text_var, font=font_setting, width=entry_width
    )
    entry.grid(row=0, column=1)

    def callback():  # function for browse buttons
        try:
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        except:
            desktop_dir = os.path.join(os.path.expanduser("~"))
        if initial_dir is None:
            dir_path = desktop_dir  # default directory: Desktop
        else:
            dir_path = initial_dir()  # call function to get initial directory
        if not os.path.exists(dir_path):
            dir_path = desktop_dir

        if is_file:
            selected = filedialog.askopenfilename(
                initialdir=dir_path, filetypes=filetypes
            )  # ask for file
        else:
            selected = filedialog.askdirectory(initialdir=dir_path)  # ask for directory
        if selected:
            entry.delete(0, tk.END)  # empty the entry first
            entry.insert(
                0, selected
            )  # insert the selected file or directory at index 0 of entry
            text_var.set(
                selected
            )  # set the chosen file as variable, e.g. "sctable_filename"
        parent_window.focus_force()  # bring focus back to root window or else button stays clicked

    # Browse button
    icon = create_folder_icon()  # load picture of folder icon for browse button
    button = ctk.CTkButton(
        frame,
        width=30,
        image=icon,
        text="",
        command=callback,
        fg_color=widget_cfg["FG_COLOR"],
        hover_color=widget_cfg["HOVER_COLOR"],
    )
    button.grid(row=0, column=2, padx=5)
    return entry

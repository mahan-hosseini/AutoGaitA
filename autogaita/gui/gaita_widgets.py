import customtkinter as ctk

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

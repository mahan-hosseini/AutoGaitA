import customtkinter as ctk

# This script contains functions to create widgets that are shared across GUIs.


def header_label(
    window,
    header_string,
    WIDGET_CFG,
):
    """Header labels"""
    return ctk.CTkLabel(
        window,
        text=header_string,
        fg_color=WIDGET_CFG["FG_COLOR"],
        text_color=WIDGET_CFG["HEADER_TXT_COLOR"],
        font=(WIDGET_CFG["HEADER_FONT_NAME"], WIDGET_CFG["MAIN_HEADER_FONT_SIZE"]),
    )


def header_button(window, button_string, WIDGET_CFG):
    """Header button"""
    return ctk.CTkButton(
        window,
        text=button_string,
        fg_color=WIDGET_CFG["FG_COLOR"],
        hover_color=WIDGET_CFG["HOVER_COLOR"],
        font=(WIDGET_CFG["HEADER_FONT_NAME"], WIDGET_CFG["HEADER_FONT_SIZE"]),
    )


def exit_button(window, WIDGET_CFG):
    """Exit button"""
    return ctk.CTkButton(
        window,
        text="Exit",
        fg_color=WIDGET_CFG["CLOSE_COLOR"],
        hover_color=WIDGET_CFG["CLOSE_HOVER_COLOR"],
        font=(WIDGET_CFG["HEADER_FONT_NAME"], WIDGET_CFG["HEADER_FONT_SIZE"]),
    )


def label_and_entry_pair(
    window, label_text, entry_variable, WIDGET_CFG, adv_cfg_textsize=False
):
    """Flexible label & entry widget-pair"""
    label = ctk.CTkLabel(
        window,
        text=label_text,
        font=(WIDGET_CFG["TEXT_FONT_NAME"], WIDGET_CFG["TEXT_FONT_SIZE"]),
    )
    entry = ctk.CTkEntry(
        window,
        textvariable=entry_variable,
        font=(WIDGET_CFG["TEXT_FONT_NAME"], WIDGET_CFG["TEXT_FONT_SIZE"]),
    )
    if adv_cfg_textsize:
        label.configure(
            font=(WIDGET_CFG["TEXT_FONT_NAME"], WIDGET_CFG["ADV_CFG_TEXT_FONT_SIZE"])
        )
        entry.configure(
            font=(WIDGET_CFG["TEXT_FONT_NAME"], WIDGET_CFG["ADV_CFG_TEXT_FONT_SIZE"])
        )
    return label, entry


def checkbox(window, label_text, entry_variable, WIDGET_CFG, adv_cfg_textsize=False):
    """Checkbox"""
    checkbox = ctk.CTkCheckBox(
        window,
        text=label_text,
        variable=entry_variable,
        onvalue=True,
        offvalue=False,
        hover_color=WIDGET_CFG["HOVER_COLOR"],
        fg_color=WIDGET_CFG["FG_COLOR"],
        font=(WIDGET_CFG["TEXT_FONT_NAME"], WIDGET_CFG["TEXT_FONT_SIZE"]),
    )
    if adv_cfg_textsize:
        checkbox.configure(
            font=(WIDGET_CFG["TEXT_FONT_NAME"], WIDGET_CFG["ADV_CFG_TEXT_FONT_SIZE"])
        )
    return checkbox

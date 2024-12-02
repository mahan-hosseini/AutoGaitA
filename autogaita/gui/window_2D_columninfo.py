# %%..............  SHARED 2D WINDOW - COLUMN & ANGLE INFO  .......................
# Note
# ----
# Hindlimb and forelimb joints were re-named to primary and secondary joints @ v0.4.0.
# I kept the old variable/key-names for compatibility with autogaita_dlc.
# => Except for input to build_beam_jointadd_window since that is used for a string
import autogaita.gui.gui_utils as gui_utils
import autogaita.gui.gaita_widgets as gaita_widgets
import customtkinter as ctk
import tkinter as tk


def build_column_info_window(root, cfg, widget_cfg, root_dimensions):
    """Build a window allowing users to configure custom column names if required"""
    columnwindow = ctk.CTkToplevel(root)
    columnwindow.geometry("%dx%d+%d+%d" % root_dimensions)
    columnwindow.title("Custom column names & features")
    gui_utils.fix_window_after_its_creation(columnwindow)

    # unpack
    FG_COLOR = widget_cfg["FG_COLOR"]
    HEADER_TXT_COLOR = widget_cfg["HEADER_TXT_COLOR"]
    HEADER_FONT_NAME = widget_cfg["HEADER_FONT_NAME"]
    HEADER_FONT_SIZE = widget_cfg["HEADER_FONT_SIZE"]
    CLOSE_COLOR = widget_cfg["CLOSE_COLOR"]
    CLOSE_HOVER_COLOR = widget_cfg["CLOSE_HOVER_COLOR"]

    # .............  Nested Function: Add joint label & entry  .........................
    def add_joint(cfg, window, key):
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
                label_string = "Primary Joint #" + str(len(cfg[key]))
            elif key == "fore_joints":
                label_string = "Secondary Joint #" + str(len(cfg[key]))
            elif key == "beam_hind_jointadd":
                label_string = "Left beam-subtraction joint #" + str(len(cfg[key]))
            elif key == "beam_fore_jointadd":
                label_string = "Right beam-subtraction joint #" + str(len(cfg[key]))
            label, entry = gaita_widgets.label_and_entry_pair(
                window, label_string, cfg[key][-1], widget_cfg
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
                    widget_cfg,
                )
                label.grid(row=nrows + 1, column=angle_column + a, sticky="ew")
                entry.grid(row=nrows + 2, column=angle_column + a)
        # maximise columns
        for c in range(window.grid_size()[0]):
            window.grid_columnconfigure(c, weight=1)

    # ...............  Nested Function: Beam jointadd window  ..........................
    def build_beam_window(cfg, widget_cfg):
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
        gui_utils.fix_window_after_its_creation(beamwindow)
        beam_scrollable_rows = 1
        total_padx = 20
        left_padx = (total_padx, total_padx / 2)
        right_padx = (total_padx / 2, total_padx)
        # ................... left section - left beam / hind joints ...................
        # left beam label & entry
        beam_left_label, beam_left_entry = gaita_widgets.label_and_entry_pair(
            beamwindow,
            "Left beam column (primary joints')",
            cfg["beam_col_left"][0],
            widget_cfg,
        )
        beam_left_label.grid(row=0, column=0, sticky="nsew")
        beam_left_entry.grid(row=1, column=0)
        # empty label one (for spacing)
        empty_label_one = ctk.CTkLabel(beamwindow, text="")
        empty_label_one.grid(row=2, column=0)
        # important: cfg key for forelimb joint add
        hindlimb_key = "beam_hind_jointadd"
        # hindlimb jointadd label
        hind_jointsubtract_label = ctk.CTkLabel(
            beamwindow,
            text="Left beam: additional joints subtracted",
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        )
        hind_jointsubtract_label.grid(row=3, column=0, sticky="nsew")
        # initialise scrollable frame for beamsubtract windows
        hind_jointsubtract_frame = ctk.CTkScrollableFrame(beamwindow)
        hind_jointsubtract_frame.grid(
            row=4,
            column=0,
            rowspan=beam_scrollable_rows,
            sticky="nsew",
        )
        # initialise labels & entries
        initialise_labels_and_entries(
            cfg,
            widget_cfg,
            hind_jointsubtract_frame,
            hindlimb_key,
            "Left beam-subtraction joint",
        )
        # add button
        add_hindjoint_button = gaita_widgets.header_button(
            beamwindow,
            "Add left beam-subtraction joint",
            widget_cfg,
        )
        add_hindjoint_button.configure(
            command=lambda: add_joint(
                cfg, hind_jointsubtract_frame, hindlimb_key
            ),  # input = cfg's key
        )
        add_hindjoint_button.grid(
            row=4 + beam_scrollable_rows,
            column=0,
            sticky="nsew",
            padx=left_padx,
            pady=20,
        )
        # .................. right section - right beam / fore joints ..................
        # right beam label & entry
        beam_right_label, beam_right_entry = gaita_widgets.label_and_entry_pair(
            beamwindow,
            "Right beam column (secondary joints')",
            cfg["beam_col_right"][0],
            widget_cfg,
        )
        beam_right_label.grid(row=0, column=1, sticky="nsew")
        beam_right_entry.grid(row=1, column=1)
        # empty label two (for spacing)
        empty_label_two = ctk.CTkLabel(beamwindow, text="")
        empty_label_two.grid(row=2, column=1)
        # important: cfg key for forelimb joint add
        forelimb_key = "beam_fore_jointadd"
        # hindlimb jointadd label
        fore_jointsubtract_label = ctk.CTkLabel(
            beamwindow,
            text="Right beam: additional joints subtracted",
            fg_color=FG_COLOR,
            text_color=HEADER_TXT_COLOR,
            font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
        )
        fore_jointsubtract_label.grid(row=3, column=1, sticky="nsew")
        # initialise scrollable frame for beamsubtract windows
        fore_jointsubtract_frame = ctk.CTkScrollableFrame(beamwindow)
        fore_jointsubtract_frame.grid(
            row=4,
            column=1,
            rowspan=beam_scrollable_rows,
            sticky="nsew",
        )
        # initialise labels & entries
        initialise_labels_and_entries(
            cfg,
            widget_cfg,
            fore_jointsubtract_frame,
            forelimb_key,
            "Right beam-subtraction joint",
        )
        # add button
        add_forejoint_button = gaita_widgets.header_button(
            beamwindow,
            "Add right beam-subtraction joint",
            widget_cfg,
        )
        add_forejoint_button.configure(
            command=lambda: add_joint(
                cfg, fore_jointsubtract_frame, forelimb_key
            ),  # input = cfg's key
        )
        add_forejoint_button.grid(
            row=4 + beam_scrollable_rows,
            column=1,
            sticky="nsew",
            padx=right_padx,
            pady=20,
        )
        # .................... bottom section - update & close  ........................
        # empty label three (for spacing)
        empty_label_three = ctk.CTkLabel(beamwindow, text="")
        empty_label_three.grid(row=5 + beam_scrollable_rows, column=0, columnspan=2)
        # done button
        beam_done_button = ctk.CTkButton(
            beamwindow,
            text="I am done, update cfg!",
            fg_color=CLOSE_COLOR,
            hover_color=CLOSE_HOVER_COLOR,
            font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
            command=lambda: beamwindow.destroy(),
        )
        beam_done_button.grid(
            row=6 + beam_scrollable_rows,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=20,
            pady=20,
        )
        # maximise widgets
        gui_utils.maximise_widgets(beamwindow)

    # ...................  Scrollable Window Configuration  ............................
    scrollable_rows = 7

    # ...................  Column 0: hind limb joint names  ............................
    hind_column = 0
    # header label
    hind_joint_label = ctk.CTkLabel(
        columnwindow,
        text="Primary Joints",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
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
    initialise_labels_and_entries(
        cfg, widget_cfg, hindlimb_frame, "hind_joints", "Primary Joint "
    )
    # add joint button
    add_hind_joint_button = gaita_widgets.header_button(
        columnwindow,
        "Add Primary Joint",
        widget_cfg,
    )
    add_hind_joint_button.configure(
        command=lambda: add_joint(
            cfg, hindlimb_frame, "hind_joints"
        ),  # 2nd input = cfg's key
    )
    add_hind_joint_button.grid(
        row=2 + scrollable_rows, column=hind_column, sticky="nsew", padx=5, pady=(10, 5)
    )
    # beam config window label
    beam_window_label = ctk.CTkLabel(columnwindow, text="")  # empty for spacing only
    beam_window_label.grid(
        row=4 + scrollable_rows,
        column=hind_column,
        columnspan=2,
        sticky="nsew",
        padx=1,
        pady=(0, 5),
    )
    # beam config window button
    beam_window_button = gaita_widgets.header_button(
        columnwindow,
        "Baseline (Beam) Configuration",
        widget_cfg,
    )
    beam_window_button.configure(
        command=lambda: build_beam_window(cfg, widget_cfg),
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
        text="Secondary Joints",
        fg_color=FG_COLOR,
        text_color=HEADER_TXT_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
    )
    fore_joint_label.grid(row=0, column=fore_column, sticky="nsew", pady=(0, 5))
    # initialise scrollable frame for forelimb
    forelimb_frame = ctk.CTkScrollableFrame(columnwindow)
    forelimb_frame.grid(
        row=1, column=fore_column, rowspan=scrollable_rows, sticky="nsew"
    )
    # initialise labels & entries with fore limb defaults
    initialise_labels_and_entries(
        cfg,
        widget_cfg,
        forelimb_frame,
        "fore_joints",
        "Secondary Joint ",
    )
    # add joint button
    add_fore_joint_button = gaita_widgets.header_button(
        columnwindow,
        "Add Secondary Joint",
        widget_cfg,
    )
    add_fore_joint_button.configure(
        command=lambda: add_joint(
            cfg, forelimb_frame, "fore_joints"
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
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
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
            cfg,
            widget_cfg,
            angle_frame,
            ["angles", angle_key],
            this_case,
            angle_column + a,
        )
    # add angle trio button
    add_angle_button = gaita_widgets.header_button(
        columnwindow,
        "Add Angle",
        widget_cfg,
    )
    add_angle_button.configure(
        command=lambda: add_joint(cfg, angle_frame, "angles"),  # 2nd input = cfg's key
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
    done_label = ctk.CTkLabel(columnwindow, text="")  # empty for spacing only
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
        fg_color=CLOSE_COLOR,
        hover_color=CLOSE_HOVER_COLOR,
        font=(HEADER_FONT_NAME, HEADER_FONT_SIZE),
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
    gui_utils.maximise_widgets(columnwindow)


def initialise_labels_and_entries(
    cfg, widget_cfg, window, key, which_case_string, *args
):
    """Add labels & entries for joint column information areas"""
    # unpack
    TEXT_FONT_NAME = widget_cfg["TEXT_FONT_NAME"]
    TEXT_FONT_SIZE = widget_cfg["TEXT_FONT_SIZE"]
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

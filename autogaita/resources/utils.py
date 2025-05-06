# ...................................  imports  ........................................
import autogaita
import pandas as pd
import numpy as np
import os
import traceback
import math
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
import customtkinter as ctk

# .................................  constants  ........................................
from autogaita.resources.constants import ISSUES_TXT_FILENAME, INFO_TEXT_WIDTH, TIME_COL
from autogaita.universal3D.universal3D_constants import LEGS_COLFORMAT


# ...............................  error handling  .....................................
def try_to_run_gaita(tracking_software, info, folderinfo, cfg, multirun_flag):
    """Try to run AutoGaitA for a single dataset - print and log error if there was any
    error that prevented completion of the main code

    Note
    ----
    Needs to know "which gaita" (DLC, SLEAP or Universal 3D) should be run and if "this run" is part
    of a call to one of our multiruns!
    """

    # first print some info
    line_row = "-" * INFO_TEXT_WIDTH
    empty_row = " " * INFO_TEXT_WIDTH
    software_string = ""
    if tracking_software == "DLC":
        software_string = "D E E P L A B C U T"
    elif tracking_software == "SLEAP":
        software_string = "S L E A P"
    elif tracking_software == "Universal 3D":
        software_string = "U N I V E R S A L  3 D"
    message_1 = f"A U T O G A I T A | {software_string}"
    message_2 = "Analysing"
    message_3 = info["name"]
    side_space_1 = " " * ((INFO_TEXT_WIDTH - len(message_1)) // 2)
    side_space_2 = " " * ((INFO_TEXT_WIDTH - len(message_2)) // 2)
    if len(message_3) >= INFO_TEXT_WIDTH:
        side_space_3 = ""
    else:
        side_space_3 = " " * ((INFO_TEXT_WIDTH - len(message_3)) // 2)
    # wow
    message = f"\n\n\n{line_row}\n{side_space_1}{message_1}{side_space_1}\n{empty_row}\n{side_space_2}{message_2}{side_space_2}\n{side_space_3}{message_3}{side_space_3}\n{line_row}\n"
    print(message)

    # try to run gaita
    try:
        if tracking_software == "DLC":
            autogaita.dlc(info, folderinfo, cfg)
        elif tracking_software == "SLEAP":
            autogaita.sleap(info, folderinfo, cfg)
        elif tracking_software == "Universal 3D":
            autogaita.universal3D(info, folderinfo, cfg)
        else:
            print("tracking_software has to be DLC, SLEAP or Universal 3D - try again.")
    # catch these errors (don't catch all possbile errors - bad practice!)
    except (
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        FileNotFoundError,
        IOError,
        OSError,
        PermissionError,
        MemoryError,
        OverflowError,
        FloatingPointError,
        pd.errors.ParserError,
        pd.errors.DtypeWarning,
        np.linalg.LinAlgError,
    ):
        error_traceback = traceback.format_exc()  # capture traceback of error
        # modify and print message
        skip_message = (
            "* ! ! ! ! ! ! ATTENTION  PLEASE ! ! ! ! ! ! *"
            + "\n* Whoopsie - Something unexpected is wrong! *"
            + "\n* See below & check Issues.txt for details. *"
        )
        if multirun_flag:
            skip_message += (
                "\n*   We'll continue with the next dataset!   *"
                + "\n\n*********************************************"
                + "\n*               Error Details               *"
                + "\n*********************************************"
                + f"\n{error_traceback}"
            )
        else:
            skip_message += (
                "\n\n*********************************************"
                + "\n*               Error Details               *"
                + "\n*********************************************\n"
                + f"\n{error_traceback}"
            )
        print(skip_message)
        # store message
        if not os.path.exists(info["results_dir"]):
            os.makedirs(info["results_dir"])
        textfile = os.path.join(info["results_dir"], ISSUES_TXT_FILENAME)
        with open(textfile, "a") as f:
            f.write(skip_message)
    return


# ...........................  generic helper functions  ...............................
def write_issues_to_textfile(message, info):
    """If there are any issues with this data, inform the user in this file"""
    textfile = os.path.join(info["results_dir"], ISSUES_TXT_FILENAME)
    with open(textfile, "a") as f:
        f.write(message)


def print_finish(info):
    """Print that we finished this program"""
    line_row = "-" * INFO_TEXT_WIDTH
    empty_row = " " * INFO_TEXT_WIDTH
    finished_message_1 = "A U T O G A I T A | D O N E"
    finished_message_2 = "Results are here"
    side_space_1 = " " * ((INFO_TEXT_WIDTH - len(finished_message_1)) // 2)
    side_space_2 = " " * ((INFO_TEXT_WIDTH - len(finished_message_2)) // 2)
    message = (
        "\n\n\n"
        + line_row
        + "\n"
        + side_space_1
        + finished_message_1
        + side_space_2
        + "\n"
        + empty_row
        + "\n"
        + side_space_2
        + finished_message_2
        + side_space_2
        + "\n"
        + str(info["results_dir"])
        + "\n"
        + line_row
    )
    print(message)


def compute_angle(joint_angle, joint2, joint3):
    """Compute a given angle at a joint & a given timepoint"""
    # prep our boolean to check if angle was broken
    broken = False
    # 1) vector between our angle-joint and the other two joints
    v1 = (joint_angle[0] - joint2[0], joint_angle[1] - joint2[1])
    v2 = (joint_angle[0] - joint3[0], joint_angle[1] - joint3[1])
    # 2) dot product and magnitudes of both vectors
    # => dot product is sum of each index multiplied by the other vector's index
    # => magnitude is square root of all items squared and them summed together
    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    mag_v1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    mag_v2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
    # 3) cosine of the angle and angle
    # => if needed: clamp to valid range to handle floating point errors
    cos_angle = dot_product / (mag_v1 * mag_v2)
    try:
        acos_angle = math.acos(cos_angle)
    except ValueError:  # cos_angle wasn't in the -1 to +1 range
        cos_angle = max(-1, min(1, cos_angle))  # clamp to valid range
        acos_angle = math.acos(cos_angle)
        broken = True
    angle = math.degrees(acos_angle)
    return angle, broken


def write_angle_warning(step, a, angles, broken_angle_idxs, info, **kwargs):
    """Write a warning to the Issues.txt file if angles were broken"""
    # Make sure you write the first WARNING message just once
    issues_file = os.path.join(info["results_dir"], ISSUES_TXT_FILENAME)
    # the file always exists in /autogaita, but not with all /tests - handling that here
    if os.path.exists(issues_file):
        with open(issues_file, "r") as f:
            issues = f.read()
    else:
        issues = ""
    if "arc cosine to -1" not in issues:
        message = (
            "\n\n***********\n! WARNING !\n***********\n"
            + "\nWe had to limit the input of the arc cosine to -1 to +1 when "
            + "computing some angles.\nThis likely is just a rounding issue with Python"
            + " but could hint at problems with your tracking, check to be sure.\n\n"
        )
    # write the which-config broke angle - message always
    message += "\n\nArc-cosine of angle fixed for this configuration:"
    if "legname" in kwargs:  # handle Universal 3D legname
        message += f"\nLeg: {kwargs['legname']}"
    time_col_idx = step.columns.get_loc(TIME_COL)
    start_time = step.iloc[broken_angle_idxs[0], time_col_idx]
    end_time = step.iloc[broken_angle_idxs[-1], time_col_idx]
    message += (
        f"\n\nAngle: {angles['name'][a]}"
        + f"\nLower Joint: {angles['lower_joint'][a]}"
        + f"\nUpper Joint: {angles['upper_joint'][a]}"
        + f"\nCycle-time: {start_time}-{end_time}s"
    )
    print(message)
    write_issues_to_textfile(message, info)


def bin_num_to_percentages(bin_num):
    """Convert bin_num to a list of percentages"""
    # smaller than 100 means we know its integers and there are no duplicates
    if bin_num < 100:
        return [int(((s + 1) / bin_num) * 100) for s in range(bin_num)]
    # special case for 100
    elif bin_num == 100:  #
        return [s for s in range(1, 101)]
    # use floats to avoid integer duplicates for more than 100 bins
    else:
        return [round((((s + 1) / bin_num) * 100), 2) for s in range(bin_num)]


def standardise_primary_joint_coordinates(data, tracking_software, info, cfg):
    """Standardises all primary joint coordinates by a fixed decimal value which is divided from all dimensions' coordinates
    => Note in Universal 3D it's just called joint
    """
    # unpack
    name = info["name"]
    coordinate_standardisation_xls = cfg["coordinate_standardisation_xls"]
    if tracking_software != "Universal 3D":
        ID_string = str(info["mouse_num"])
        run_string = str(info["run_num"])
        joints = cfg["hind_joints"]
        angles = cfg["angles"]
    else:
        ID_string = name
        joints = cfg["joints"]
        angles = cfg["angles"]
    # first test: check if all joints used in angles are present in joints
    angle_issue_message = ""
    clean_angles = {"name": [], "lower_joint": [], "upper_joint": []}
    for i in range(len(angles["name"])):
        if all(
            angle_joint in joints
            for angle_joint in [
                angles["name"][i],
                angles["lower_joint"][i],
                angles["upper_joint"][i],
            ]
        ):
            clean_angles["name"].append(angles["name"][i])
            clean_angles["lower_joint"].append(angles["lower_joint"][i])
            clean_angles["upper_joint"].append(angles["upper_joint"][i])
        else:
            if not angle_issue_message:
                angle_issue_message += (
                    "\n***********\n! WARNING !\n***********\n"
                    + "\nYou are standardising your coordinates to fixed values / ID!"
                    + "\nYou must ensure that all joints used in angle-computations "
                    + "are present in your (hind) joints list and are thus "
                    + "standardised!\nThis would otherwise lead to broken angles."
                    + "\nProblematic angles are:"
                    + "\n\n-----------------------"
                )
            angle_issue_message += (
                f"\nName: {angles['name'][i]}"
                + f"\nLower Joint: {angles['lower_joint'][i]}"
                + f"\nUpper Joint: {angles['upper_joint'][i]}"
                + "\n-----------------------"
            )
    # rare case of overwriting cfg within autogaita!
    if angle_issue_message:
        angle_issue_message += (
            "\nWe will update your cfg (!) & continue with the remaining angles!"
        )
        print(angle_issue_message)
        write_issues_to_textfile(angle_issue_message, info)
    cfg["angles"] = clean_angles
    # test if xls exists - if not quit autogaita
    # => note that some_prep will be stopped if this should return None
    if not os.path.exists(coordinate_standardisation_xls):
        message = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "No coordinate standardisation xls file found at:"
            + f"\n{coordinate_standardisation_xls}!"
            + "\nFix the path or remove the value from the config (GUI) if you "
            + "do not wish you standardise coordinates."
            + "\nNote that horizontal (i.e. x- in 2D) or height (i.e. y- in 2D) "
            + "standardisation is something else!"
            + "\nCancelling AutoGaitA!"
        )
        print(message)
        write_issues_to_textfile(message, info)
        raise FileNotFoundError
    # load the file (string because of comparison in conditon)
    coord_stand_df = pd.read_excel(coordinate_standardisation_xls).astype(str)
    if not all(coord_stand_df.columns.isin(["ID", "Run", "Standardisation Value"])):
        message = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + "The coordinate standardisation Excel file does not have the correct "
            + "column names - refer to our Template file!"
            + "\nPlease check the xls file and try again."
            + "\nCancelling AutoGaitA!"
        )
        print(message)
        write_issues_to_textfile(message, info)
        raise ValueError
    # extract the row we need
    if tracking_software != "Universal 3D":
        condition = (coord_stand_df["ID"] == ID_string) & (
            coord_stand_df["Run"] == run_string
        )
    else:
        condition = coord_stand_df["ID"] == ID_string
    coord_stand_df = coord_stand_df[condition]
    if len(coord_stand_df) != 1:
        message = "\n******************\n! CRITICAL ERROR !\n******************\n"
        if len(coord_stand_df) == 0:
            message += (
                f"Unable to find {name} in the coordinate standardisation xls file!"
            )
        elif len(coord_stand_df) > 1:
            message += f"Found multiple entries for {name} in the coordinate standardisation xls file!"
        message += (
            "\nPlease check the xls file and try again." + "\nCancelling AutoGaitA!"
        )
        print(message)
        write_issues_to_textfile(message, info)
        raise ValueError
    # extract standardisation value from xls
    try:
        # if-len-lines in error-message block above ensure that the line below is
        # indexing correctly using iloc[0, 2] - condition is always of len==1!
        coordinate_standardisation_value = float(coord_stand_df.iloc[0, 2])
    except ValueError:
        message = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + f"Unable to convert standardisation value for {name} to a float!"
            + "\nPlease check the xls file and try again."
            + "\nCancelling AutoGaitA!"
        )
        print(message)
        write_issues_to_textfile(message, info)
        raise ValueError
    # ensure that value is equal to or larger than 1 (otherwise we would increase vals)
    if coordinate_standardisation_value < 1:
        message = (
            "\n******************\n! CRITICAL ERROR !\n******************\n"
            + f"Standardisation value for {name} is smaller than 1!"
            + "\nPlease read the doc for why this is not allowed."
            + "\nIf you do not want to standardise this dataset, use a value of 1."
            + "\nCancelling AutoGaitA!"
        )
        print(message)
        write_issues_to_textfile(message, info)
        raise ValueError
    # all tests are passed - standardise coordinates
    # => if we are in 3D we have to check for bodyside-specificity, add all cols
    #    (joint + coord) to a list and use the list for looping when standardising
    if tracking_software != "Universal 3D":
        coordinates = ("x", "y")
    else:
        coordinates = ("X", "Y", "Z")
    cols_to_standardise = []
    for joint in joints:
        for coord in coordinates:
            central_joint = joint + coord
            side_specific_joint = joint + LEGS_COLFORMAT[0] + coord
            if central_joint in data.columns:
                cols_to_standardise.append(central_joint)
            if side_specific_joint in data.columns:
                for leg in LEGS_COLFORMAT:
                    cols_to_standardise.append(joint + leg + coord)
    data.loc[:, cols_to_standardise] = (
        data.loc[:, cols_to_standardise] / coordinate_standardisation_value
    )
    return data, cfg


# ................................  plot panel  ........................................
class PlotPanel:
    def __init__(self, fg_color, hover_color):
        self.figures = []
        self.current_fig_index = 0
        self.fg_color = fg_color
        self.hover_color = hover_color

    # .........................  loading screen  ................................
    def build_plot_panel_loading_screen(self):
        """Builds a loading screen that is shown while plots are generated"""
        # Build window
        self.loading_screen = ctk.CTkToplevel()
        self.loading_screen.title("Loading...")
        self.loading_screen.geometry("300x300")
        self.loading_label_strings = [
            "Plots are generated, please wait.",
            "Plots are generated, please wait..",
            "Plots are generated, please wait...",
        ]
        self.loading_label = ctk.CTkLabel(
            self.loading_screen, text=self.loading_label_strings[0]
        )
        self.loading_label.pack(pady=130, padx=40, anchor="w")

        # Animate the text
        self.animate(counter=1)

    # Cycle through loading labels to animate the loading screen
    def animate(self, counter):
        self.loading_label.configure(text=self.loading_label_strings[counter])
        self.loading_screen.after(
            500, self.animate, (counter + 1) % len(self.loading_label_strings)
        )

    def destroy_plot_panel_loading_screen(self):
        self.loading_screen.destroy()

    # .........................  plot panel   ................................
    def build_plot_panel(self):
        """Creates the window/"panel" in which the plots are shown"""
        # Set up of the plotpanel
        ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
        ctk.set_default_color_theme("green")  # Themes: blue , dark-blue, green
        self.plotwindow = ctk.CTkToplevel()
        self.plotwindow.title(
            f"AutoGaitA Figure {self.current_fig_index + 1}/{len(self.figures)}"
        )

        # Set size to 50% of screen
        screen_width = self.plotwindow.winfo_screenwidth()
        window_width = int(screen_width * 0.5)
        # 0.75 to gain a ration of 1.333 (that of matplotlib figures) and 1.05 for toolbar + buttons
        window_height = window_width * 0.75 * 1.05
        self.plotwindow.geometry(f"{window_width}x{window_height}")

        # Adjust figures for the plot panel
        for fig in self.figures:
            # dpi adjusted to increase visibilty/readability
            fig.set_dpi(100)
            # constrained layout to adjust margins within the figure
            # => note: in case there are a lot of steps in one run (-> the legend is
            #          super long) the figure won't be displayed properly.
            fig.set_constrained_layout(True)

        # Initialize the plot panel with the first figure
        self.plot_panel = FigureCanvasTkAgg(
            self.figures[self.current_fig_index], master=self.plotwindow
        )  # index used for buttons
        self.plot_panel.get_tk_widget().grid(
            row=0, column=0, padx=10, pady=10, sticky="nsew"
        )

        # Create toolbar frame and place it in the middle row
        self.toolbar_frame = tk.Frame(self.plotwindow)
        self.toolbar_frame.grid(row=1, column=0, sticky="ew")

        self.toolbar = NavigationToolbar2Tk(self.plot_panel, self.toolbar_frame)
        self.toolbar.update()

        # Create navigation buttons frame
        self.button_frame = tk.Frame(self.plotwindow)
        self.button_frame.grid(row=2, column=0, sticky="ew")

        self.prev_button = ctk.CTkButton(
            self.button_frame,
            text="<< Previous",
            fg_color=self.fg_color,
            hover_color=self.hover_color,
            command=self.show_previous,
        )
        self.next_button = ctk.CTkButton(
            self.button_frame,
            text="Next >>",
            fg_color=self.fg_color,
            hover_color=self.hover_color,
            command=self.show_next,
        )
        self.prev_button.grid(row=0, column=0, sticky="ew")
        self.next_button.grid(row=0, column=1, sticky="ew")

        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        # Configure grid layout
        self.plotwindow.grid_rowconfigure(0, weight=1)
        self.plotwindow.grid_rowconfigure(1, weight=0)
        self.plotwindow.grid_rowconfigure(2, weight=0)
        self.plotwindow.grid_columnconfigure(0, weight=1)

    def show_previous(self):
        if self.current_fig_index > 0:
            self.current_fig_index -= 1
            self.update_plot_and_toolbar()

    def show_next(self):
        if self.current_fig_index < len(self.figures) - 1:
            self.current_fig_index += 1
            self.update_plot_and_toolbar()

    def update_plot_and_toolbar(self):
        # Clear the current plot panel
        self.plot_panel.get_tk_widget().grid_forget()

        # Update the plot panel with the new figure
        self.plot_panel = FigureCanvasTkAgg(
            self.figures[self.current_fig_index], master=self.plotwindow
        )
        self.plot_panel.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.plot_panel.draw()

        # Destroy toolbar and create a new one
        # (This has to be done, otherwise the toolbar won't function for a new plot)
        self.toolbar.destroy()
        self.toolbar = NavigationToolbar2Tk(self.plot_panel, self.toolbar_frame)
        self.toolbar.update()

        # Update title
        self.plotwindow.title(
            f"AutoGaitA Plot Panel {self.current_fig_index + 1}/{len(self.figures)}"
        )

    def destroy_plot_panel(self):
        # Needed if no SCs after checks
        self.loading_screen.destroy()

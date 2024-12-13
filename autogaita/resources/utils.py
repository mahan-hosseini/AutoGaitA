# ...................................  imports  ........................................
import autogaita
import pandas as pd
import numpy as np
import os
import traceback
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
import customtkinter as ctk


# .................................  constants  ........................................
from autogaita.resources.constants import ISSUES_TXT_FILENAME, INFO_TEXT_WIDTH


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
    message_1 = "G A I T A | S T A R T"
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
    finished_message_1 = "G A I T A | D O N E"
    finished_message_2 = "Results are here"
    side_space_1 = " " * ((INFO_TEXT_WIDTH - len(finished_message_1)) // 2)
    side_space_2 = " " * ((INFO_TEXT_WIDTH - len(finished_message_2)) // 2)
    message = (
        line_row
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
        + info["results_dir"]
        + "\n"
        + line_row
    )
    print(message)


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

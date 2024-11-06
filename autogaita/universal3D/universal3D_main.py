# %% imports
from autogaita.universal3D.universal3D_1_preparation import some_prep
from autogaita.universal3D.universal3D_2_sc_extraction import (
    extract_stepcycles,
    check_stepcycles,
)
from autogaita.universal3D.universal3D_3_analysis import analyse_and_export_stepcycles
from autogaita.universal3D.universal3D_4_plots import plot_results
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
import customtkinter as ctk

# %% constants
matplotlib.use("agg")
# Agg is a non-interactive backend for plotting that can only write to files
# this is used to generate and save the plot figures
# later a tkinter backend (FigureCanvasTkAgg) is used for the plot panel
# increase resolution of figures
plt.rcParams["figure.dpi"] = 300
from autogaita.universal3D.universal3D_constants import FG_COLOR, HOVER_COLOR

# %%
# ......................................................................................
# ........................  an important note for yourself  ............................
# ......................................................................................
# Please read this (& check_data_column_names!) when you are confused about col-names.
# It's a bit tricky in this code, see comments & doc about this issue in:
# 1. check_and_fix_cfg_strings (why am I here, read the others)
# 2. check_data_column_names (read me first)
# 3. add_features (then me)
# 4. plot_results (me if you really have to)
# => mainly (from 2.):
# Bodyside-specific colnames have to end WITHOUT a space (because we concat
# "name" + ", leg " + "Z" - so leg ends with a space)
# Bodyside-nonspecific colnames have to end WITH a space (because we concat "name "
# + "Z" so name has to end with a space)
# ......................................................................................


# %% main program


def universal3D(info, folderinfo, cfg):
    """Runs the main program for a given subject's run

    Procedure
    ---------
    1) import & preparation
    2) step cycle extraction
    3) z-normalisation, y-flipping & feature computation for individual step cycles
    4) step cycle normalisaion, dataframe creation & XLS-exportation
    5) plots
    """
    # .............. initiate plot panel class and build loading screen ................
    # create class instance independently of "dont_show_plots" to not break the code
    plot_panel_instance = PlotPanel()

    if cfg["dont_show_plots"] is True:
        pass  # going on without building the loading screen

    elif cfg["dont_show_plots"] is False:  # -> show plot panel
        # build loading screen
        plot_panel_instance.build_plot_panel_loading_screen()

    # ...............................  preparation  ....................................
    data, global_Y_max = some_prep(info, folderinfo, cfg)
    if (data is None) & (global_Y_max is None):
        return

    # ..........................  step-cycle extraction  ...............................
    all_cycles = extract_stepcycles(data, info, folderinfo, cfg)
    all_cycles = check_stepcycles(all_cycles, info)
    if not all_cycles:  # only None if both leg's SCs were None
        if cfg["dont_show_plots"] is False:  # otherwise stuck at loading
            plot_panel_instance.destroy_plot_panel()
        return

    # ......  main analysis: y-flipping, features, df-creation & exports  ..............
    results = analyse_and_export_stepcycles(data, all_cycles, global_Y_max, info, cfg)

    # ..................................  plots  .......................................
    plot_results(results, all_cycles, info, cfg, plot_panel_instance)

    # ..............................  print finish  ....................................
    print_finish(info, cfg)


class PlotPanel:
    def __init__(self):
        self.figures = []
        self.current_fig_index = 0

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
            f"AutoGaitA Figure {self.current_fig_index+1}/{len(self.figures)}"
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
            fg_color=FG_COLOR,
            hover_color=HOVER_COLOR,
            command=self.show_previous,
        )
        self.next_button = ctk.CTkButton(
            self.button_frame,
            text="Next >>",
            fg_color=FG_COLOR,
            hover_color=HOVER_COLOR,
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
            f"AutoGaitA Plot Panel {self.current_fig_index+1}/{len(self.figures)}"
        )

    def destroy_plot_panel(self):
        # Needed if no SCs after checks
        self.loading_screen.destroy()


# %% local functions 5 - print finish


def print_finish(info, cfg):
    """Print that we finished this program"""
    print("\n***************************************************")
    print("* GAITA FINISHED - RESULTS WERE SAVED HERE:       *")
    print("* " + info["results_dir"] + " *")
    print("***************************************************")


# %% what happens if we just hit run
if __name__ == "__main__":
    universal3D_info_message = (
        "\n*************\nnot like this\n*************\n"
        + "You are trying to execute autogaita.universal3D as a script, but that is not "
        + "possible.\nIf you prefer a non-GUI approach, please either: "
        + "\n1. Call this as a function, i.e. autogaita.universal3D(info, folderinfo, cfg)"
        + "\n2. Use the single or multirun scripts in the batchrun_scripts folder"
    )
    print(universal3D_info_message)

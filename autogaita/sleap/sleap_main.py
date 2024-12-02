# %% imports
from autogaita.sleap.sleap_1_preparation import some_prep
from autogaita.sleap.sleap_2_sc_extraction import extract_stepcycles
from autogaita.common2D.common2D_utils import handle_issues
from autogaita.common2D.common2D_3_analysis import analyse_and_export_stepcycles
from autogaita.common2D.common2D_4_plots import plot_results
from autogaita.gaita_res.utils import print_finish, PlotPanel
import matplotlib
import matplotlib.pyplot as plt

# .................................  constants  ........................................
matplotlib.use("agg")
# Agg is a non-interactive backend for plotting that can only write to files
# this is used to generate and save the plot figures
# later a tkinter backend (FigureCanvasTkAgg) is used for the plot panel
plt.rcParams["figure.dpi"] = 300  # increase resolution of figures
from autogaita.gui.gui_constants import SLEAP_FG_COLOR, SLEAP_HOVER_COLOR


# .................................  main program  .....................................


def sleap(info, folderinfo, cfg):
    """Runs the main program for a given ID's run

    Procedure
    ---------
    1) import & preparation
    2) step cycle extraction
    3) x/y-standardisation & feature computation for individual step cycles
    4) step cycle normalisation, dataframe creation & XLS-exportation
    5) plots
    """
    # .............. initiate plot panel class and build loading screen ................
    # create class instance independently of "dont_show_plots" to not break the code
    plot_panel_instance = PlotPanel(SLEAP_FG_COLOR, SLEAP_HOVER_COLOR)

    if cfg["dont_show_plots"] is True:
        pass  # going on without building the loading screen

    elif cfg["dont_show_plots"] is False:  # -> show plot panel
        # build loading screen
        plot_panel_instance.build_plot_panel_loading_screen()

    # ................................  preparation  ...................................
    data = some_prep(info, folderinfo, cfg)
    if data is None:
        return

    # .........................  step-cycle extraction  ................................
    all_cycles = extract_stepcycles(data, info, folderinfo, cfg)
    if all_cycles is None:
        handle_issues("scs_invalid", info)
        if cfg["dont_show_plots"] is False:  # otherwise stuck at loading
            plot_panel_instance.destroy_plot_panel()
        return

    # .........  main analysis: sc-lvl y-norm, features, df-creation & export ..........
    results = analyse_and_export_stepcycles(data, all_cycles, info, cfg)

    # ................................  plots  .........................................
    plot_results(info, results, cfg, plot_panel_instance)

    # ............................  print finish  ......................................
    print_finish(info)


# %% what happens if we just hit run
if __name__ == "__main__":
    sleap_info_message = (
        "\n*************\nnot like this\n*************\n"
        + "You are trying to execute autogaita.sleap as a script, but that is not "
        + "possible.\nIf you prefer a non-GUI approach, please either: "
        + "\n1. Call this as a function, i.e. autogaita.sleap(info, folderinfo, cfg)"
        + "\n2. Use the single or multirun scripts in the batchrun_scripts folder"
    )
    print(sleap_info_message)

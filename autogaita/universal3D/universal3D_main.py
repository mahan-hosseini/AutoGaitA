# ...................................  imports  ........................................
from autogaita.universal3D.universal3D_1_preparation import some_prep
from autogaita.universal3D.universal3D_2_sc_extraction import (
    extract_stepcycles,
    check_stepcycles,
)
from autogaita.universal3D.universal3D_3_analysis import analyse_and_export_stepcycles
from autogaita.universal3D.universal3D_4_plots import plot_results
from autogaita.gaita_res.utils import print_finish, PlotPanel
import matplotlib
import matplotlib.pyplot as plt

# .................................  constants  ........................................
matplotlib.use("agg")
# Agg is a non-interactive backend for plotting that can only write to files
# this is used to generate and save the plot figures
# later a tkinter backend (FigureCanvasTkAgg) is used for the plot panel
plt.rcParams["figure.dpi"] = 300  # increase resolution of figures
from autogaita.gui.gui_constants import UNIVERSAL3D_FG_COLOR, UNIVERSAL3D_HOVER_COLOR

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


# .................................  main program  .....................................
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
    plot_panel_instance = PlotPanel(UNIVERSAL3D_FG_COLOR, UNIVERSAL3D_HOVER_COLOR)

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
    print_finish(info)


# ..................................  if we hit run  ...................................
if __name__ == "__main__":
    universal3D_info_message = (
        "\n*************\nnot like this\n*************\n"
        + "You are trying to execute autogaita.universal3D as a script, but that is not "
        + "possible.\nIf you prefer a non-GUI approach, please either: "
        + "\n1. Call this as a function, i.e. autogaita.universal3D(info, folderinfo, cfg)"
        + "\n2. Use the single or multirun scripts in the batchrun_scripts folder"
    )
    print(universal3D_info_message)

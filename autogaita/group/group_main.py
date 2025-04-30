# ...................................  imports  ........................................
from autogaita.group.group_1_preparation import some_prep
from autogaita.group.group_2_data_processing import (
    import_data,
    avg_and_std,
    grand_avg_and_std,
    load_previous_runs_dataframes,
)
from autogaita.group.group_3_PCA import PCA_main
from autogaita.group.group_4_stats import (
    create_stats_df,
    cluster_extent_test,
    anova_design_sanity_check,
    ANOVA_main,
)
from autogaita.group.group_5_plots import plot_results
from autogaita.group.group_utils import print_start, tukeys_only_info_message
from autogaita.resources.utils import print_finish, PlotPanel
import matplotlib
import matplotlib.pyplot as plt

# .................................  constants  ........................................
# SET PLT BACKEND
# Agg is a non-interactive backend for plotting that can only write to files
# this is used to generate and save the plot figures
# later a tkinter backend (FigureCanvasTkAgg) is used for the plot panel
matplotlib.use("agg")
plt.rcParams["figure.dpi"] = 300  # increase resolution of figures
from autogaita.gui.gui_constants import GROUP_FG_COLOR, GROUP_HOVER_COLOR


# .................................  main program  .....................................
def group(folderinfo, cfg):
    """Runs the main program for a group-level analysis comparing 2-5 groups

    Procedure
    ---------
    1) prepare some cfg and folderinfo - e.g., read bin_num/read jsons/global vars
    2) import the results folders and create dfs and raw_dfs (non-standardised) SC data
    3) compute average/std (ID-level) and grand-average/grand-std dataframes
    4) PCA
    5) prepare stats: create stats_df
    6) perform the cluster-extent permutation test
    7) perform the RM-/Mixed-ANOVA
    8) plots
    """
    # .............. initiate plot panel class and build loading screen ................
    # create class instance independently of "dont_show_plots" to not break the code
    plot_panel_instance = PlotPanel(GROUP_FG_COLOR, GROUP_HOVER_COLOR)

    if cfg["dont_show_plots"] is True:
        pass  # going on without building the loading screen

    elif cfg["dont_show_plots"] is False:  # -> show plot panel
        # build loading screen
        plot_panel_instance.build_plot_panel_loading_screen()

    # ................................  preparation  ...................................
    # => either creates and sanity-checks folderinfo & cfg or loads it from a previous
    #    run's config.json file (if load_dir)
    # => there is an IMPORTANT NOTE about this in some_prep!
    folderinfo, cfg = some_prep(folderinfo, cfg)

    # ..............................  print start  ....................................
    # => print start after some_prep since we do some stuff to cfg["PCA_bins"] there
    print_start(folderinfo, cfg)

    # .....................  import & transform (a) or load (b)  .......................

    # approach a - import & transform (i.e. no previous results to load from)
    if not folderinfo["load_dir"]:
        # "dfs" are x-/Y-standardised automatically if 1st-level standardised x/Y
        # => if this is the case, it translates to all average & std dfs as well
        dfs, raw_dfs, cfg = import_data(folderinfo, cfg)
        avg_dfs, std_dfs = avg_and_std(dfs, folderinfo, cfg)
        g_avg_dfs, g_std_dfs = grand_avg_and_std(avg_dfs, folderinfo, cfg)

    # approach b - load previous run's dfs (avg, g_avg & g_std_dfs)
    else:
        try:
            # creating cfg["bin_num"] here too (since done in import_data in (a)!)
            avg_dfs, g_avg_dfs, g_std_dfs, cfg = load_previous_runs_dataframes(
                folderinfo, cfg
            )
        except (FileNotFoundError, ValueError):
            return

    # ...................................  PCA  ........................................
    if cfg["PCA_variables"]:  # empty lists are falsey!
        PCA_main(avg_dfs, folderinfo, cfg, plot_panel_instance)
    plt.close("all")  # OK since all figures passed to save-funcs & PlotPanel

    # ..............................  prepare statistics  ..............................
    stats_df = create_stats_df(avg_dfs, folderinfo, cfg)

    # ......................  cluster-extent permutation test  .........................
    if cfg["stats_variables"]:  # empty lists are falsey!
        if cfg["do_permtest"]:
            for stats_var in cfg["stats_variables"]:
                cluster_extent_test(
                    stats_df,
                    g_avg_dfs,
                    g_std_dfs,
                    stats_var,
                    folderinfo,
                    cfg,
                    plot_panel_instance,
                )
        plt.close("all")

        # ..................................  ANOVA  ...................................
        if cfg["do_anova"]:  # indentation since we check for stats-vars here too!
            if anova_design_sanity_check(stats_df, folderinfo, cfg) is not True:
                just_do_tukeys = True
                tukeys_only_info_message(folderinfo)
            else:
                just_do_tukeys = False
            # this function is called ANOVA_main even though we might just run Tukeys
            # with it and not exactly an ANOVA as well
            # => see conditions in sanity check setting just_do_tukeys
            for stats_var in cfg["stats_variables"]:
                ANOVA_main(
                    stats_df,
                    g_avg_dfs,
                    g_std_dfs,
                    stats_var,
                    just_do_tukeys,
                    folderinfo,
                    cfg,
                    plot_panel_instance,
                )
        plt.close("all")

    # ..................................  plots  .......................................
    plot_results(g_avg_dfs, g_std_dfs, folderinfo, cfg, plot_panel_instance)

    # ..............................  print finish  ....................................
    print_finish(folderinfo)


# ..................................  if we hit run  ...................................
if __name__ == "__main__":
    group_info_message = (
        "\n*************\nnot like this\n*************\n"
        + "You are trying to execute autogaita.group as a script, but that is not "
        + "possible.\nIf you prefer a non-GUI approach, please either: "
        + "\n1. Call this as a function, i.e. autogaita.group(folderinfo, cfg)"
        + "\n2. Use the dlc or universal 3Drun scripts in the batchrun_scripts folder"
    )
    print(group_info_message)

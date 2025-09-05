import os
from autogaita.resources.utils import write_issues_to_textfile
from autogaita.resources.constants import INFO_TEXT_WIDTH
from autogaita.group.group_constants import (
    GROUP_CONFIG_TXT_FILENAME,
    PCA_CUSTOM_SCATTER_OUTER_SEPARATOR,
    STATS_PLOTS_LEGEND_SIZE,
    STATS_PLOTS_SUPLABEL_SIZE,
)
import numpy as np
import matplotlib.pyplot as plt


# %% .........................  print start and finish  ................................
def print_start(folderinfo, cfg):
    """Print some info about starting this analysis"""

    # header
    gaita_string = "A U T O G A I T A | G R O U P"
    space_add = " " * ((INFO_TEXT_WIDTH - len(gaita_string)) // 2)
    start_string = (
        "\n"
        + "-" * INFO_TEXT_WIDTH
        + "\n"
        + space_add
        + gaita_string
        + space_add
        + "\n"
        + "-" * INFO_TEXT_WIDTH
        + "\n\nGroup Names\n-----------"
    )

    # groups
    for group_name in folderinfo["group_names"]:
        start_string += "\n" + group_name

    # load dir
    if folderinfo["load_dir"]:
        start_string += "\n\nLoad Directory\n--------------\n" + folderinfo["load_dir"]

    # pca
    PCA_string = "P R I N C I P A L | C O M P O N E N T | A N A L Y S I S"
    space_add = " " * ((INFO_TEXT_WIDTH - len(PCA_string)) // 2)
    start_string += (
        "\n\n\n"
        + "-" * INFO_TEXT_WIDTH
        + "\n"
        + space_add
        + PCA_string
        + space_add
        + "\n"
        + "-" * INFO_TEXT_WIDTH
    )
    if cfg["PCA_variables"]:
        start_string += "\n\nFeatures\n--------"
        for PCA_var in cfg["PCA_variables"]:
            start_string += "\n" + PCA_var
        if cfg["PCA_n_components"] > 0 and cfg["PCA_n_components"] < 1:
            start_string += (
                "\n\nPC-Number Configuration\n-----------------------\n"
                + str(cfg["PCA_n_components"] * 100)
                + "% of variance explained"
            )
        else:
            start_string += (
                "\n\nPC-Number Configuration\n-----------------------\n"
                + str(cfg["PCA_n_components"])
                + " principal components"
            )
        if cfg["PCA_custom_scatter_PCs"]:
            cfg["PCA_custom_scatter_PCs"] = cfg["PCA_custom_scatter_PCs"].replace(
                " ", ""  # remove spaces for user if they included them (not allowed!)
            )
            # string cannot end with the ; separator this will break later
            while cfg["PCA_custom_scatter_PCs"].endswith(  # in case users are funny
                PCA_CUSTOM_SCATTER_OUTER_SEPARATOR
            ):
                cfg["PCA_custom_scatter_PCs"] = cfg["PCA_custom_scatter_PCs"][:-1]
            start_string += "\n\nCustom Scatterplot Configuration:"
            for i, custom_scatter_PCs in enumerate(
                cfg["PCA_custom_scatter_PCs"].split(PCA_CUSTOM_SCATTER_OUTER_SEPARATOR)
            ):
                start_string += "\nPlot " + str(i + 1) + " - " + custom_scatter_PCs
        if cfg["PCA_bins"]:
            start_string += "\n\nCustom Bin Configuration\n----------------------"
            start_string += "\n" + cfg["PCA_bins"]
    else:
        start_string += "\n\nNo PCA wanted!"

    # stats
    stats_string = "S T A T I S T I C S"
    space_add = " " * ((INFO_TEXT_WIDTH - len(stats_string)) // 2)
    start_string += (
        "\n\n\n"
        + "-" * INFO_TEXT_WIDTH
        + "\n"
        + space_add
        + stats_string
        + space_add
        + "\n"
        + "-" * INFO_TEXT_WIDTH
    )
    if cfg["stats_variables"]:
        start_string += "\n\nFeatures\n--------"
        for stats_var in cfg["stats_variables"]:
            start_string += "\n" + stats_var
        start_string += "\n\nConfiguration\n-------------"
        if cfg["do_anova"]:
            start_string += "\n" + cfg["anova_design"]
        else:
            start_string += "\nNo ANOVA"
        if cfg["do_permtest"]:
            start_string += (
                "\nCluster-extent permutation test with "
                + str(cfg["permutation_number"])
                + " permutations"
            )
        else:
            start_string += "\nNo Permutation Test"
        start_string += (
            "\nAlpha Level of " + str(cfg["stats_threshold"] * 100) + "%\n\n"
        )
    else:
        start_string += "\n\nNo stats wanted!\n\n"

    # done - print & save
    print(start_string)
    with open(
        os.path.join(folderinfo["results_dir"], GROUP_CONFIG_TXT_FILENAME), "w"
    ) as f:
        f.write(start_string)


# %% ......................  plotting helper functions  ...........................
def save_figures(figure, results_dir, figure_file_string):
    """Save figures as pngs to results_dir and as svgs to separate subfolders"""
    # pngs to results_dir
    figure.savefig(
        os.path.join(results_dir, figure_file_string + ".png"),
        bbox_inches="tight",
    )
    # svgs to subfolders
    svg_dir = os.path.join(results_dir, "SVG Figures")
    if not os.path.exists(svg_dir):
        os.makedirs(svg_dir)
    figure.savefig(
        os.path.join(svg_dir, figure_file_string + ".svg"), bbox_inches="tight"
    )


def ytickconvert_mm_to_cm(axis):
    """Convert axis y-ticks from mm (of data) to cm"""
    y_ticks = axis.get_yticks()
    y_ticklabels = []
    for t in y_ticks:
        y_ticklabels.append(str(round(t / 10, 2)))
    axis.set_yticks(y_ticks, labels=y_ticklabels)


def ylabel_velocity_and_acceleration(feature, unit, sampling_rate):
    """Generate strings for velo and accel ylabels"""
    ylabel = feature
    ylabel += " ("
    ylabel += unit  # unit must reflect conversion (x in pixel or cm)
    ylabel += " / "
    ylabel += str(int((1 / sampling_rate) * 1000))
    ylabel += " ms)"
    return ylabel


# %% ........................  misc. helper functions  .................................
def tukeys_only_info_message(folderinfo):
    """Inform user about the fact that we are only doing Tukeys due to our ANOVA sanity check failing"""
    tukeys_only_info_message = (
        "\n***********\n! WARNING !\n***********\n\n"
        + "Your ANOVA settings were wrong.This either happens because: \n 1) You ran "
        + "a one-way ANOVA with wrong inputs (there should be another message about "
        + "this) or \n 2) You attempted to run a two-way design which is not "
        + "supported yet.\nWe will run Tukey's test for multiple comparisons anyways."
    )
    print(tukeys_only_info_message)
    write_issues_to_textfile(tukeys_only_info_message, folderinfo)


def check_mouse_conversion(feature, cfg, **kwargs):
    """For DLC: check if we have to convert mm to cm (for plotting x/y/velo/accel)"""
    if "convert_to_mm" not in cfg.keys():
        return False
    else:
        if cfg["convert_to_mm"] is False:
            return False
        else:
            # case 1: just x/y in mm
            if (
                feature.endswith(" x")
                or feature.endswith(" y")
                or (feature in ["x", "y"])
            ):
                return True
            if feature in ["Velocity", "Acceleration"]:
                # case 2: velo/accel as in plot functions
                if "stats_var" not in kwargs.keys():
                    return True
                # case 3: velo/accel as in stats functions
                # => make sure it's not angular!
                elif "Angle" not in kwargs["stats_var"]:
                    return True
    return False


def setup_stats_plots_vars(contrasts, bin_num):
    """Set up variables for all stats plots"""
    if len(contrasts) <= 5:
        f, ax = plt.subplots(len(contrasts), 1, layout="constrained")
        stats_plots_suplabel_size = STATS_PLOTS_SUPLABEL_SIZE
        if len(contrasts) == 1:
            stats_plots_legend_size = STATS_PLOTS_LEGEND_SIZE + 4
            ax = np.atleast_1d(ax)  # quick hack so we can index ax as a list
        else:
            stats_plots_legend_size = STATS_PLOTS_LEGEND_SIZE
    else:
        if len(contrasts) == 6:  # 4 groups
            f, ax = plt.subplots(3, 2, layout="constrained", figsize=(15, 10))
        elif len(contrasts) == 10:  # 5 groups
            f, ax = plt.subplots(5, 2, layout="constrained", figsize=(15, 10))
        elif len(contrasts) == 15:  # 6 groups
            f, ax = plt.subplots(5, 3, layout="constrained", figsize=(15, 10))
        ax = ax.ravel()  # so we can index it as 1D array
        stats_plots_suplabel_size = STATS_PLOTS_SUPLABEL_SIZE + 5
        stats_plots_legend_size = STATS_PLOTS_LEGEND_SIZE + 1
    # x is linear space between 0 and 100% with bin_num steps
    x = np.linspace(0, 100, bin_num)
    return f, ax, stats_plots_legend_size, stats_plots_suplabel_size, x

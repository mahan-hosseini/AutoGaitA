import os

from autogaita.group.group_constants import ISSUES_TXT_FILENAME


# %% .........................  print start and finish  ................................
def print_start(folderinfo, cfg):
    """Print some info about starting this analysis"""

    # header
    start_string = (
        "\n******************\n AutoGaitA_Group \n******************"
        + "\n\nContrasting Groups:"
    )
    # groups
    for group_name in folderinfo["group_names"]:
        start_string += "\n" + group_name
    # pca
    start_string += "\n\n\n*****\n PCA \n*****"
    if cfg["PCA_variables"]:
        start_string += "\n\nFeatures:"
        for PCA_var in cfg["PCA_variables"]:
            start_string += "\n" + PCA_var
        start_string += (
            "\n\nConfiguration:\n" + str(cfg["number_of_PCs"]) + " principal components"
        )
    else:
        start_string += "\n\nNo PCA wanted!"
    # stats
    start_string += "\n\n\n*************\n Statistics \n*************"
    if cfg["stats_variables"]:
        start_string += "\n\nFeatures:"
        for stats_var in cfg["stats_variables"]:
            start_string += "\n" + stats_var
        start_string += "\n\nConfiguration:"
        if cfg["do_anova"]:
            start_string += "\n" + cfg["anova_design"]
        else:
            start_string += "\nNo Anova"
        start_string += (
            "\nCluster-extent permutation test with "
            + str(cfg["permutation_number"])
            + " permutations"
        )
        start_string += (
            "\nAlpha Level of " + str(cfg["stats_threshold"] * 100) + "%\n\n"
        )
    else:
        start_string += "\n\nNo stats wanted!\n\n"

    # done - print
    print(start_string)


def print_finish(folderinfo):
    """Inform the user about being done."""
    print("\n***************************************************************")
    print("*      GAITA FINISHED - YOUR RESULTS WERE STORED HERE:        *")
    print(folderinfo["results_dir"])
    print("***************************************************************")


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


def write_issues_to_textfile(message, results_dir):
    """Write issues to a textfile"""
    issues_textfile = os.path.join(results_dir, ISSUES_TXT_FILENAME)
    with open(issues_textfile, "a") as f:
        f.write(message)


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

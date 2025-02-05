# %% imports
from autogaita.universal3D.universal3D_utils import (
    extract_feature_column,
    transform_joint_and_leg_to_colname,
)
from autogaita.resources.utils import write_issues_to_textfile
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D

import matplotlib
import pdb

# %% constants
from autogaita.resources.constants import TIME_COL
from autogaita.universal3D.universal3D_constants import (
    LEGS,
    SC_LAT_LEGEND_FONTSIZE,
    ANGLE_PLOTS_YLIMITS,
    STICK_LINEWIDTH,
)

# %% workflow step #4 - various plots

# A Note
# ------
# I initially decided to use extract_sc_idxs instead of all_cycles when I first wrote
# this for mice data to be independent from the previous pipeline - just so plotting
# stuff could at some point be ran just by loading the XLS files that
# analyse_and_export_stepcycles outputs However, I am now using all_cycles instead of
# sc_idxs because for humans we have multiple runs per subject and I need to understand
# which SC latencies correspond to which run.
# This might change in the future but for now let's do it this way.
# => Idea: you could just save all_cycles to a file and then load that as well as XLS
#          to plot independently from previous things.

# Another 2 (more recent) Notes
# --------------------------
# In all functions below I added checks to see if joints/angles were bodyside-specific
# e.g., "Ankle, left Z" or "Pelvis Z"
# => We still loop over legname in plot_results as before since even though the column
#    might not be bodyside-specific, the data dfs (e.g. all_steps_data) contain
#    different values based on the leg that performed the step-cycles
#
# Only use extract_feature_column when you index using .iloc afterwards (don't be
# surprised that we don't use this local func everywhere, since the first couple of
# plotting functions extract values using .loc!)


# ................................  master function  ...................................
def plot_results(results, all_cycles, info, cfg, plot_panel_instance):
    """Plot various results"""

    # unpack
    angles = cfg["angles"]
    y_acceleration = cfg["y_acceleration"]
    angular_acceleration = cfg["angular_acceleration"]
    analyse_average_y = cfg["analyse_average_y"]
    dont_show_plots = cfg["dont_show_plots"]
    if dont_show_plots:
        plt.switch_backend("Agg")

    # unpack - output specific vars (results to be plotted)
    for legname in LEGS:  # !!! NU - output...
        all_steps_data = results[legname]["all_steps_data"]
        average_data = results[legname]["average_data"]
        std_data = results[legname]["std_data"]
        sc_num = results[legname]["sc_num"]

        if all_cycles[legname]:

            # ....................  1 - z coords by y coords  ..........................
            plot_joint_z_by_y(
                legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
            )

            # ........................  2 - y coords by time  ..........................
            if analyse_average_y:
                plot_joint_y_by_time(
                    legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
                )

            # ..................  3 - angle by time for each SC  .......................
            if angles["name"]:
                plot_angles_by_time(
                    legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
                )
            # regularly closing figures to save memory
            # => no problem to do this since we pass figure-vars to save-functions and Panel
            plt.close("all")

            # ............................  4 - stick diagram  .........................
            plot_stickdiagrams(
                legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
            )

            # .................  5 - average 5-joints' z over SC percentage  ...........
            plot_joint_z_by_average_SC(
                legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
            )

            # .................  6 - average 5-joints' y over SC percentage  ...........
            if analyse_average_y:
                plot_joint_y_by_average_SC(
                    legname,
                    average_data,
                    std_data,
                    sc_num,
                    info,
                    cfg,
                    plot_panel_instance,
                )

            # ...................  7 - average angles over SC percentage  ..............
            if angles["name"]:
                plot_angles_by_average_SC(
                    legname,
                    average_data,
                    std_data,
                    sc_num,
                    info,
                    cfg,
                    plot_panel_instance,
                )
            plt.close("all")

            # .............  8 - average y velocities over SC percentage   .............
            plot_y_velocities_by_average_SC(
                legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
            )

            # ..........  9 - average angular velocities over SC percentage  ...........
            if angles["name"]:
                plot_angular_velocities_by_average_SC(
                    legname,
                    average_data,
                    std_data,
                    sc_num,
                    info,
                    cfg,
                    plot_panel_instance,
                )

            # .......  optional - 10 - average x acceleration over SC percentage  ......
            if y_acceleration:
                plot_y_acceleration_by_average_SC(
                    legname,
                    average_data,
                    std_data,
                    sc_num,
                    info,
                    cfg,
                    plot_panel_instance,
                )

            # ....  optional - 11 - average angular acceleration over SC percentage  ...
            if angles["name"]:
                if angular_acceleration:
                    plot_angular_acceleration_by_average_SC(
                        legname,
                        average_data,
                        std_data,
                        sc_num,
                        info,
                        cfg,
                        plot_panel_instance,
                    )
            plt.close("all")
        else:
            no_plots_message = (
                "\n***********\n! WARNING !\n***********\n"
                + "No step cycles found for "
                + legname
                + " leg!"
                + "\nWe thus skip all figures for this leg!\n"
            )
            print(no_plots_message)
            write_issues_to_textfile(no_plots_message, info)

    # ........................optional - 12 - build plot panel..........................
    if dont_show_plots is True:
        pass  # going on without building the plot window
    elif dont_show_plots is False:  # -> show plot panel
        # Destroy loading screen and build plot panel with all figures
        plot_panel_instance.destroy_plot_panel_loading_screen()
        plot_panel_instance.build_plot_panel()


# ................................  inner functions  ...................................


def plot_joint_z_by_y(
    legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
):
    """1 - Plot joints' z coordinates as a function of their y for each SC"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    sampling_rate = cfg["sampling_rate"]
    dont_show_plots = cfg["dont_show_plots"]
    plot_joints = cfg["plot_joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    max_cycle_num = 0
    for cycles in all_cycles[legname]:
        if len(cycles) > max_cycle_num:
            max_cycle_num = len(cycles)
    f = [[] for _ in range(len(plot_joints))]
    ax = [[] for _ in range(len(plot_joints))]

    # plot
    for j, joint in enumerate(plot_joints):  # joint loop (figures)
        f[j], ax[j] = plt.subplots(
            len(all_cycles[legname]),
            1,
            sharex=True,
            sharey=True,
            gridspec_kw={"hspace": 0},
        )
        for r, run_cycles in enumerate(all_cycles[legname]):  # run loop (axis)
            sc_num = len(run_cycles)
            try:  # handle only 1 run in "stuff by y" plots
                ax[j][r].set_prop_cycle(
                    plt.cycler("color", sns.color_palette(color_palette, max_cycle_num))
                )
            except:
                ax[j].set_prop_cycle(
                    plt.cycler("color", sns.color_palette(color_palette, max_cycle_num))
                )
            # check for bodyside-specificity
            if joint + "Y" in all_steps_data.columns:
                y_col_string = joint + "Y"
                z_col_string = joint + "Z"
            else:
                y_col_string = transform_joint_and_leg_to_colname(joint, legname, "Y")
                z_col_string = transform_joint_and_leg_to_colname(joint, legname, "Z")
            for s in range(sc_num):
                this_sc_idx = run_cycles[s]
                this_y = all_steps_data.loc[
                    this_sc_idx[0] : this_sc_idx[1], y_col_string
                ]
                this_z = all_steps_data.loc[
                    this_sc_idx[0] : this_sc_idx[1], z_col_string
                ]
                this_label = generate_sc_latency_label(this_sc_idx, sampling_rate)
                try:
                    ax[j][r].plot(this_y, this_z, label=this_label)
                except:
                    ax[j].plot(this_y, this_z, label=this_label)
            # axis stuff
            try:
                if legend_outside is True:
                    ax[j][r].legend(
                        fontsize=SC_LAT_LEGEND_FONTSIZE,
                        loc="center left",
                        bbox_to_anchor=(1, 0.5),
                    )
                elif legend_outside is False:
                    ax[j][r].legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
                median_z_val = [round(np.median(ax[j][r].get_yticks()), 2)]
                median_z_val_label = [str(median_z_val[0])]  # has to be of same len
                ax[j][r].set_yticks(median_z_val, median_z_val_label)
            except:
                if legend_outside is True:
                    ax[j].legend(
                        fontsize=SC_LAT_LEGEND_FONTSIZE + 3,
                        loc="center left",
                        bbox_to_anchor=(1, 0.5),
                    )
                elif legend_outside is False:
                    ax[j].legend(fontsize=SC_LAT_LEGEND_FONTSIZE + 3)
                median_z_val = [round(np.median(ax[j].get_yticks()), 2)]
                median_z_val_label = [str(median_z_val[0])]  # has to be of same len
                ax[j].set_yticks(median_z_val, median_z_val_label)
            # title
            figure_file_string = (
                name + " - " + legname + " - " + joint + " z by y coordinates"
            )
            try:
                ax[j][0].set_title(figure_file_string)
            except:
                ax[j].set_title(figure_file_string)
        # figure stuff
        f[j].supxlabel("y")
        f[j].supylabel("z")
        save_figures(f[j], results_dir, figure_file_string)
        if dont_show_plots:
            plt.close(f[j])

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f[j])


def plot_joint_y_by_time(
    legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
):
    """2 - Plot joints' y coordinates as a function of time for each SC"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    sampling_rate = cfg["sampling_rate"]
    dont_show_plots = cfg["dont_show_plots"]
    plot_joints = cfg["plot_joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    max_cycle_num = 0
    for cycles in all_cycles[legname]:
        if len(cycles) > max_cycle_num:
            max_cycle_num = len(cycles)
    f = [[] for _ in range(len(plot_joints))]
    ax = [[] for _ in range(len(plot_joints))]

    # plot
    for j, joint in enumerate(plot_joints):  # joint loop (figures)
        f[j], ax[j] = plt.subplots(
            len(all_cycles[legname]),
            1,
            sharex=True,
            sharey=True,
            gridspec_kw={"hspace": 0},
        )
        for r, run_cycles in enumerate(all_cycles[legname]):  # run loop (axis)
            sc_num = len(run_cycles)
            try:  # handle only 1 run in "stuff by y" plots
                ax[j][r].set_prop_cycle(
                    plt.cycler("color", sns.color_palette(color_palette, max_cycle_num))
                )
            except:
                ax[j].set_prop_cycle(
                    plt.cycler("color", sns.color_palette(color_palette, max_cycle_num))
                )
            # check for bodyside-specificity
            if joint + "X" in all_steps_data.columns:
                y_col_string = joint + "Y"
            else:
                y_col_string = transform_joint_and_leg_to_colname(joint, legname, "Y")
            for s in range(sc_num):
                this_sc_idx = run_cycles[s]
                this_time = all_steps_data.loc[
                    this_sc_idx[0] : this_sc_idx[1], TIME_COL
                ]
                this_y = all_steps_data.loc[
                    this_sc_idx[0] : this_sc_idx[1], y_col_string
                ]
                this_label = generate_sc_latency_label(this_sc_idx, sampling_rate)
                try:
                    ax[j][r].plot(this_time, this_y, label=this_label)
                except:
                    ax[j].plot(this_time, this_y, label=this_label)
            # axis stuff
            try:
                if legend_outside is True:
                    ax[j][r].legend(
                        fontsize=SC_LAT_LEGEND_FONTSIZE,
                        loc="center left",
                        bbox_to_anchor=(1, 0.5),
                    )
                elif legend_outside is False:
                    ax[j][r].legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
                median_y_val = [round(np.median(ax[j][r].get_yticks()), 2)]
                median_y_val_label = [str(median_y_val[0])]  # has to be of same len
                ax[j][r].set_yticks(median_y_val, median_y_val_label)
            except:
                if legend_outside is True:
                    ax[j].legend(
                        fontsize=SC_LAT_LEGEND_FONTSIZE + 3,
                        loc="center left",
                        bbox_to_anchor=(1, 0.5),
                    )
                elif legend_outside is False:
                    ax[j].legend(fontsize=SC_LAT_LEGEND_FONTSIZE + 3)
                median_y_val = [round(np.median(ax[j].get_yticks()), 2)]
                median_y_val_label = [str(median_y_val[0])]  # has to be of same len
                ax[j].set_yticks(median_y_val, median_y_val_label)
            # title
            figure_file_string = (
                name + " - " + legname + " - " + joint + " y coordinate by time "
            )
            try:
                ax[j][0].set_title(figure_file_string)
            except:
                ax[j].set_title(figure_file_string)
        # figure stuff
        f[j].supxlabel("Time (s)")
        f[j].supylabel("y")
        save_figures(f[j], results_dir, figure_file_string)
        if dont_show_plots:
            plt.close(f[j])

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f[j])


def plot_angles_by_time(
    legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
):
    """3 - Plot joints' angles as a function of time for each SC"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    sampling_rate = cfg["sampling_rate"]
    dont_show_plots = cfg["dont_show_plots"]
    angles = cfg["angles"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    max_cycle_num = 0
    for cycles in all_cycles[legname]:
        if len(cycles) > max_cycle_num:
            max_cycle_num = len(cycles)
    f = [[] for _ in range(len(angles["name"]))]
    ax = [[] for _ in range(len(angles["name"]))]

    # plot
    for a, angle in enumerate(angles["name"]):  # angle loop (figures)
        f[a], ax[a] = plt.subplots(1, 1)
        for run_cycles in all_cycles[legname]:  # run loop (color-cycler-reset)
            sc_num = len(run_cycles)
            ax[a].set_prop_cycle(
                plt.cycler("color", sns.color_palette(color_palette, max_cycle_num))
            )
            # check for bodyside-specificity
            if angle + "Angle" in all_steps_data.columns:
                angle_col_string = angle + "Angle"
            else:
                angle_col_string = transform_joint_and_leg_to_colname(
                    angle, legname, "Angle"
                )
            for s in range(sc_num):
                this_sc_idx = run_cycles[s]
                this_time = all_steps_data.loc[
                    this_sc_idx[0] : this_sc_idx[1], TIME_COL
                ]
                this_angle = all_steps_data.loc[
                    this_sc_idx[0] : this_sc_idx[1], angle_col_string
                ]
                this_label = generate_sc_latency_label(this_sc_idx, sampling_rate)
                ax[a].plot(this_time, this_angle, label=this_label)
            # legend
            if legend_outside is True:
                ax[a].legend(
                    fontsize=SC_LAT_LEGEND_FONTSIZE,
                    loc="center left",
                    bbox_to_anchor=(1, 0.5),
                )
            elif legend_outside is False:
                ax[a].legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
            # title
            figure_file_string = (
                name + " - " + legname + " - " + angle + " angle by time"
            )
            ax[a].set_title(figure_file_string)
        # figure stuff
        f[a].supxlabel("Time (s)")
        f[a].supylabel("Angle (degree)")
        save_figures(f[a], results_dir, figure_file_string)
        if dont_show_plots:
            plt.close(f[a])

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f[a])


def plot_stickdiagrams(
    legname, all_steps_data, all_cycles, info, cfg, plot_panel_instance
):
    """4 - Plot a stick diagram"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    sampling_rate = cfg["sampling_rate"]
    dont_show_plots = cfg["dont_show_plots"]
    plot_joints = cfg["plot_joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    max_cycle_num = 0
    for cycles in all_cycles[legname]:
        if len(cycles) > max_cycle_num:
            max_cycle_num = len(cycles)
    f, ax = plt.subplots(
        len(all_cycles[legname]),
        1,
        sharex=True,
        sharey=True,
        gridspec_kw={"hspace": 0},
    )
    f_3d, ax_3d = plt.subplots(  # 3d stick diagram
        len(all_cycles[legname]),
        1,
        sharex=True,
        sharey=True,
        gridspec_kw={"hspace": 0},
        subplot_kw={"projection": "3d"},
    )
    f_3d.set_size_inches(f.get_size_inches())  # match figure sizes
    color_cycle = plt.cycler("color", sns.color_palette(color_palette, max_cycle_num))

    # plot
    for r, run_cycles in enumerate(all_cycles[legname]):  # run loop (axis)
        this_sc_num = len(run_cycles)
        try:  # handle 1 run with valid SCs
            ax_3d[r].set_prop_cycle(color_cycle)
            ax[r].set_prop_cycle(color_cycle)
        except:
            ax_3d.set_prop_cycle(color_cycle)
            ax.set_prop_cycle(color_cycle)
        for c, this_color_dict in zip(range(this_sc_num), color_cycle):  # SC loop
            this_sc_idx = run_cycles[c]
            this_color = this_color_dict["color"][:3]
            this_label = generate_sc_latency_label(this_sc_idx, sampling_rate)
            # for tps from SC1 to SCend - plot(joint1x, joint1y) or x/y/z
            for i in range(
                this_sc_idx[0], this_sc_idx[1] + 1
            ):  # timepoint loop (of this SC)
                this_xs = list()  # for each timepoint, define joints' coords new
                this_ys = list()
                this_zs = list()
                for joint in plot_joints:
                    # check for bodyside-specificity
                    if joint + "Y" in all_steps_data.columns:
                        x_col_string = joint + "X"
                        y_col_string = joint + "Y"
                        z_col_string = joint + "Z"
                    else:
                        x_col_string = transform_joint_and_leg_to_colname(
                            joint, legname, "X"
                        )
                        y_col_string = transform_joint_and_leg_to_colname(
                            joint, legname, "Y"
                        )
                        z_col_string = transform_joint_and_leg_to_colname(
                            joint, legname, "Z"
                        )
                    this_xs.append(all_steps_data.loc[i, x_col_string])
                    this_ys.append(all_steps_data.loc[i, y_col_string])
                    this_zs.append(all_steps_data.loc[i, z_col_string])
                    # plot args/axis being a list or not is based on label and sc number
                    plot_args = {
                        "color": this_color,
                        "lw": STICK_LINEWIDTH,
                        "label": (
                            this_label
                            if i == range(this_sc_idx[0], this_sc_idx[1] + 1)[0]
                            else None
                        ),
                    }
                    try:
                        ax_3d[r].plot(this_xs, this_ys, this_zs, **plot_args)
                        ax[r].plot(this_ys, this_zs, **plot_args)
                    except:
                        ax_3d.plot(this_xs, this_ys, this_zs, **plot_args)
                        ax.plot(this_ys, this_zs, **plot_args)
        # axis stuff
        try:
            if legend_outside is True:
                ax_3d[r].legend(
                    fontsize=SC_LAT_LEGEND_FONTSIZE,
                    loc="center left",
                    bbox_to_anchor=(1, 0.5),
                )
                ax[r].legend(
                    fontsize=SC_LAT_LEGEND_FONTSIZE,
                    loc="center left",
                    bbox_to_anchor=(1, 0.5),
                )
            elif legend_outside is False:
                ax_3d[r].legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
                ax[r].legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
            median_z_val = [round(np.median(ax[r].get_yticks()), 2)]
            median_z_val_label = [str(median_z_val[0])]  # has to be of same len
            ax_3d[r].set_zticks(median_z_val, median_z_val_label)
            ax[r].set_yticks(median_z_val, median_z_val_label)
        except:
            if legend_outside is True:
                ax_3d.legend(
                    fontsize=SC_LAT_LEGEND_FONTSIZE + 3,
                    loc="center left",
                    bbox_to_anchor=(1, 0.5),
                )
                ax.legend(
                    fontsize=SC_LAT_LEGEND_FONTSIZE + 3,
                    loc="center left",
                    bbox_to_anchor=(1, 0.5),
                )
            elif legend_outside is False:
                ax_3d.legend(fontsize=SC_LAT_LEGEND_FONTSIZE + 3)
                ax.legend(fontsize=SC_LAT_LEGEND_FONTSIZE + 3)
            median_z_val = [round(np.median(ax.get_yticks()), 2)]
            median_z_val_label = [str(median_z_val[0])]  # has to be of same len
            ax_3d.set_zticks(median_z_val, median_z_val_label)
            ax.set_yticks(median_z_val, median_z_val_label)
        # 3d view & axes-sizes equal to 2d figure
        try:
            ax_3d[r].view_init(elev=20, azim=-90)
            # pos = ax[r].get_position()
            # ax_3d[r].set_position([pos.x0, pos.y0, pos.width, pos.height])
            ax_3d[r].set_box_aspect([20, 2, 1])
            # ax_3d[r].set_xlim(ax[r].get_xlim())
            # ax_3d[r].set_zlim(ax[r].get_ylim())
        except:
            ax_3d.view_init(elev=20, azim=0)
            ax_3d.set_position(ax.get_position())
    # title
    figure_file_string = name + " - " + legname + " - Stick Diagram"
    try:
        ax_3d[0].set_title(figure_file_string + " - 3D")
        ax[0].set_title(figure_file_string)
    except:
        ax_3d.set_title(figure_file_string + " - 3D")
        ax.set_title(figure_file_string)
    f_3d.supxlabel("y")
    f_3d.supylabel("z")
    f.supxlabel("y")
    f.supylabel("z")
    save_figures(f_3d, results_dir, figure_file_string + " - 3D")
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f_3d)
        plt.close(f)

    pdb.set_trace()

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f_3d)
        plot_panel_instance.figures.append(f)


def plot_joint_z_by_average_SC(
    legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
):
    """5 - Plot joints' z as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    plot_SE = cfg["plot_SE"]
    joints = cfg["joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(joints)))
    )
    x = np.linspace(0, 100, bin_num)
    for joint in joints:  # joint loop (lines)
        # check for bodyside-specificity
        z_col = extract_feature_column(average_data, joint, legname, "Z")
        this_z = average_data.iloc[:, z_col]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, z_col] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, z_col]
        ax.plot(x, this_z, label=joint)
        ax.fill_between(x, this_z - this_std, this_z + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel("z")
    figure_file_string = (
        name + " - " + legname + " - Joint z-coord.s over average step cycle"
    )
    ax.set_title(figure_file_string)
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_joint_y_by_average_SC(
    legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
):
    """5 - Plot joints' y as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    plot_SE = cfg["plot_SE"]
    joints = cfg["joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(joints)))
    )
    x = np.linspace(0, 100, bin_num)
    for joint in joints:  # joint loop (lines)
        # check for bodyside-specificity
        y_col = extract_feature_column(average_data, joint, legname, "Y")
        this_y = average_data.iloc[:, y_col]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col]
        ax.plot(x, this_y, label=joint)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel("y")
    figure_file_string = (
        name + " - " + legname + " - Joint y-coord.s over average step cycle"
    )
    ax.set_title(figure_file_string)
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_angles_by_average_SC(
    legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
):
    """6 - Plot Angles as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    plot_SE = cfg["plot_SE"]
    angles = cfg["angles"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(angles["name"])))
    )
    x = np.linspace(0, 100, bin_num)
    ax.set_xlabel("Percentage")
    ax.set_ylabel("Angle (degree)")
    for angle in angles["name"]:  # angle loop (lines)
        # check for bodyside-specificity
        feature = "Angle"
        angle_col = extract_feature_column(average_data, angle, legname, feature)
        this_angle_val = average_data.iloc[:, angle_col]
        if plot_SE:
            this_std = std_data.iloc[:, angle_col] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, angle_col]  # average & std_data share colnames
        ax.plot(x, this_angle_val, label=angle)
        ax.fill_between(
            x, this_angle_val - this_std, this_angle_val + this_std, alpha=0.2
        )
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_ylim(ANGLE_PLOTS_YLIMITS)
    figure_file_string = (
        name + " - " + legname + " - Joint angles over average step cycle"
    )
    ax.set_title(figure_file_string)
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_y_velocities_by_average_SC(
    legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
):
    """7 - Plot x velocities as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    joints = cfg["joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(joints)))
    )
    x = np.linspace(0, 100, bin_num)
    for joint in joints:  # joint loop (lines)
        # check for bodyside-specificity
        feature = "Velocity"
        y_col = extract_feature_column(average_data, joint, legname, feature)
        this_y = average_data.iloc[:, y_col]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col]
        ax.plot(x, this_y, label=joint)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    # NU: improve handling of different units
    # ax.set_ylabel("Velocity (Y in m / " + str(int((1 / sampling_rate) * 1000)) + "ms")
    ax.set_ylabel("Velocity")
    figure_file_string = (
        name + " - " + legname + " - Joint y-velocities over average step cycle"
    )
    ax.set_title(figure_file_string)
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_angular_velocities_by_average_SC(
    legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
):
    """8 - Plot angular velocities as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    angles = cfg["angles"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(angles["name"])))
    )
    x = np.linspace(0, 100, bin_num)
    for angle in angles["name"]:  # angle loop (lines)
        # check for bodyside-specificity
        feature = "Angle Velocity"
        y_col = extract_feature_column(average_data, angle, legname, feature)
        this_y = average_data.iloc[:, y_col]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col]
        ax.plot(x, this_y, label=angle)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel("Velocity (degree / " + str(int((1 / sampling_rate) * 1000)) + "ms)")
    figure_file_string = (
        name + " - " + legname + " - Angular velocities over average step cycle"
    )
    ax.set_title(figure_file_string)
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_y_acceleration_by_average_SC(
    legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
):
    """9 - (optional) Plot x acceleration as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    joints = cfg["joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(joints)))
    )
    x = np.linspace(0, 100, bin_num)
    for joint in joints:  # joint loop (lines)
        feature = "Acceleration"
        y_col = extract_feature_column(average_data, joint, legname, feature)
        this_y = average_data.iloc[:, y_col]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col]
        ax.plot(x, this_y, label=joint)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel(
        # NU: improve handling of different units
        # "Acceleration (Y in m / " + str(int((1 / sampling_rate) * 1000)) + "ms)"
        "Acceleration"
    )
    figure_file_string = (
        name + " - " + legname + " - Joint y-accelerations over average step cycle"
    )
    ax.set_title(figure_file_string)
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_angular_acceleration_by_average_SC(
    legname, average_data, std_data, sc_num, info, cfg, plot_panel_instance
):
    """
    10 - (optional) Plot angular acceleration as a function of average SC's percentage
    """

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    angles = cfg["angles"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(angles["name"])))
    )
    x = np.linspace(0, 100, bin_num)
    for angle in angles["name"]:  # angle loop (lines)
        feature = "Angle Acceleration"
        y_col = extract_feature_column(average_data, angle, legname, feature)
        this_y = average_data.iloc[:, y_col]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col]
        ax.plot(x, this_y, label=angle)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel(
        "Acceleration (degree / " + str(int((1 / sampling_rate) * 1000)) + "ms)"
    )
    figure_file_string = (
        name + " - " + legname + " - Angular accelerations over average step cycle"
    )
    ax.set_title(figure_file_string)
    save_figures(f, results_dir, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


# ..............................  helper functions  ....................................
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


def generate_sc_latency_label(this_sc_idx, sampling_rate):
    if sampling_rate <= 100:
        float_precision = 2  # how many decimals we round to
    else:
        float_precision = 4
    this_label = (
        str(round(this_sc_idx[0] / sampling_rate, float_precision))
        + "-"
        + str(round(this_sc_idx[1] / sampling_rate, float_precision))
        + "s"
    )
    return this_label

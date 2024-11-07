# %% imports
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# %% constants
from autogaita.core2D.core2D_constants import (
    TIME_COL,
    SC_LAT_LEGEND_FONTSIZE,
)


# %% workflow step #4 - extract SCs from all_steps_data (# !!! NU - load XLS) and plot


# ..............................  master function  .............................

# A note on x-standardisation (14.08.2024)
# => If x-standardisation was performed, original as well as x-standardised dfs are
#    generated and exported to xls
# => Our plotting functions only used all_steps_data, average_data & std_data
# => Conveniently, if x-standardisation is performed, all_steps_data DOES NOT include
#    x-standardisation and is thus still the correct choice for the step-cycle level
#    plots (#1-#5)
# => On the other hand, average_data & std_data (plots #6-12) DO and SHOULD include
#    x-standardisation
# => Note that there is a slight discrepancy because angle-plots are based on
#    x-standardised values  for the step-cycle level plots (#3) but not for the average
#    plots (#8)
#   -- This is not an issue since x-standardisation does not affect angles, even though
#      the values of x change because they change by a constant for all joints (there
#      is a unit test for this)

# A note on updated colour cyclers after pull request that was merged 20.06.2024
# => Using color palettes instead of colour maps as I had previously means that
#    we cycle through neighbouring colours
# => I initially implemented an "equally distant" approach.
# => So for viridis and n=2 (e.g. if 2 groups) it would be purple and yellow
#    (as far away as possible)
# => Now it is dark blue and green
# => Updated approach is aesthetically more pleasing IMO.
# => However it does have the risk of not being able to tell the colours in
#    some cases - e.g. if some accelerations are very overlapping.
# => But - because users can in theses cases just choose a colour palette that
#    in itself has categorical colours (Set1, Dark2, etc.) I still keep the new
#    behaviour
# => Nonetheless, in case you want to use the "old behaviour" at some point it
#    would be coded as commented out in plot_joint_y_by_x


def plot_results(info, results, cfg, plot_panel_instance):
    """Plot results - y coords by x coords & average angles over SC %"""
    # unpack
    fore_joints = cfg["fore_joints"]
    angles = cfg["angles"]
    all_steps_data = results["all_steps_data"]
    average_data = results["average_data"]
    std_data = results["std_data"]
    x_acceleration = cfg["x_acceleration"]
    angular_acceleration = cfg["angular_acceleration"]
    analyse_average_x = cfg["analyse_average_x"]
    dont_show_plots = cfg["dont_show_plots"]
    if dont_show_plots:
        plt.switch_backend("Agg")

    # ....................0 - extract SCs from all_steps_data...........................
    sc_idxs = extract_sc_idxs(all_steps_data)
    cfg["sc_num"] = len(sc_idxs)  # add number of scs for plotting SE if wanted

    # .........................1 - y coords by x coords.................................
    plot_joint_y_by_x(all_steps_data, sc_idxs, info, cfg, plot_panel_instance)

    # .....................2 - x coords by time (optional!).............................
    if analyse_average_x:
        plot_x_by_time(all_steps_data, sc_idxs, info, cfg, plot_panel_instance)

    # ...............................3 - angles by time.................................
    if angles["name"]:
        plot_angles_by_time(all_steps_data, sc_idxs, info, cfg, plot_panel_instance)
    # regularly closing figures to save memory
    # => no problem to do this since we pass figure-vars to save-functions and PlotPanel
    plt.close("all")

    # ..........................4 - hindlimb stick diagram..............................
    plot_hindlimb_stickdiagram(all_steps_data, sc_idxs, info, cfg, plot_panel_instance)

    # ...........................5 - forelimb stick diagram.............................
    if fore_joints:
        plot_forelimb_stickdiagram(
            all_steps_data, sc_idxs, info, cfg, plot_panel_instance
        )

    # .....................6 - average joints' y over SC percentage.....................
    plot_joint_y_by_average_SC(average_data, std_data, info, cfg, plot_panel_instance)

    # ...............7 - average joints' x over SC percentage (optional!)...............
    if analyse_average_x:
        plot_joint_x_by_average_SC(
            average_data, std_data, info, cfg, plot_panel_instance
        )
    plt.close("all")

    # ........................8 - average angles over SC percentage.....................
    if angles["name"]:
        plot_angles_by_average_SC(
            average_data, std_data, info, cfg, plot_panel_instance
        )

    # .................9 - average x velocities over SC percentage......................
    plot_x_velocities_by_average_SC(
        average_data, std_data, info, cfg, plot_panel_instance
    )

    # .............10 - average angular velocities over SC percentage...................
    if angles["name"]:
        plot_angular_velocities_by_average_SC(
            average_data, std_data, info, cfg, plot_panel_instance
        )

    # ............optional - 11 - average x acceleration over SC percentage.............
    if x_acceleration:
        plot_x_acceleration_by_average_SC(
            average_data, std_data, info, cfg, plot_panel_instance
        )

    # .........optional - 12 - average angular acceleration over SC percentage..........
    if angles["name"]:
        if angular_acceleration:
            plot_angular_acceleration_by_average_SC(
                average_data, std_data, info, cfg, plot_panel_instance
            )
    plt.close("all")

    # ........................optional - 13 - build plot panel..........................
    if dont_show_plots is True:
        pass  # going on without building the plot window
    elif dont_show_plots is False:  # -> show plot panel
        # Destroy loading screen and build plot panel with all figures
        plot_panel_instance.destroy_plot_panel_loading_screen()
        plot_panel_instance.build_plot_panel()


# ..................................  inner functions  .................................


def extract_sc_idxs(all_steps_data):
    """0 - Prepare stepcycles on original-length (non-normalised) SCs"""
    # A note on all_steps_data & nan (see xls_separations):
    # ==> (Using range & iloc so we don't have to subtract 1 to nan-idxs)
    # ==> if there is more than 1 SC found, the first row of nan indicates the
    #     END of SC 1
    # ==> the last row of nan indicates the START of the last SC
    # ==> everything inbetween is alternatingly: (if you add 1 to nan-idx) the
    #     start of an SC + (if you subtract -1 to nan-idx) the end of that SC
    # ==> E.g.: separations[1]+1 is 1st idx of SC2 - separations[2]-1 is last
    #     idx of SC2
    check_col = all_steps_data.columns[0]  # take the first col to find nan-separators
    xls_separations = np.where(pd.isnull(all_steps_data[check_col]))[0]
    sc_idxs = []
    # the next line means that we have exactly one step, because we would not
    # build all_steps_data (and have results in the first place) if there was no step
    # Thus, if xls_sep. is empty (len=0) it means that no separations were
    # there, i.e., 1 SC
    if len(xls_separations) == 0:
        sc_idxs.append(range(0, len(all_steps_data)))  # I can do this bc. only 1 SC
    else:
        for b in range(len(xls_separations)):
            if b == 0:
                # SC1 - 0 to (not including) nan/end-idx
                sc_idxs.append(range(xls_separations[b]))
            elif b > 0:  # inbetween SCs
                if (b % 2) == 0:
                    sc_idxs.append(
                        range(
                            xls_separations[b - 1] + 1,  # add 1=start
                            xls_separations[b],
                        )
                    )
            # last SC - I can write it this way because b will always be odd if
            # it refers to the start of a stepcycle & thus: possibly the last
            if xls_separations[b] == xls_separations[-1]:
                sc_idxs.append(range(xls_separations[-1] + 1, len(all_steps_data)))
    return sc_idxs


def plot_joint_y_by_x(all_steps_data, sc_idxs, info, cfg, plot_panel_instance):
    """1 - Plot joints' y coordinates as a function of their x for each SC"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    convert_to_mm = cfg["convert_to_mm"]
    plot_joints = cfg["plot_joints"]
    sampling_rate = cfg["sampling_rate"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    sc_num = len(sc_idxs)
    f = [[] for _ in range(len(plot_joints))]
    ax = [[] for _ in range(len(plot_joints))]

    # plot
    for j, joint in enumerate(plot_joints):  # joint loop (figures)
        f[j], ax[j] = plt.subplots(1, 1)
        # What "Old" colormap approach would look like with seaborn
        # this_map = sns.color_palette(cfg["color_palette"], as_cmap=True)
        # ax[j].set_prop_cycle(plt.cycler("color", this_map(np.linspace(0, 1, sc_num))))
        ax[j].set_prop_cycle(  # New color palette approach
            plt.cycler("color", sns.color_palette(color_palette, sc_num))
        )
        ax[j].set_title(name + " - " + joint + "Y")
        x_col_idx = all_steps_data.columns.get_loc(joint + "x")
        y_col_idx = all_steps_data.columns.get_loc(joint + "y")
        time_col_idx = all_steps_data.columns.get_loc(TIME_COL)
        for s in range(sc_num):
            this_x = all_steps_data.iloc[sc_idxs[s], x_col_idx]
            this_y = all_steps_data.iloc[sc_idxs[s], y_col_idx]
            this_label = generate_sc_latency_label(
                all_steps_data, sc_idxs[s], sampling_rate, time_col_idx
            )
            ax[j].plot(this_x, this_y, label=this_label)
        # legend adjustments
        if legend_outside is True:
            ax[j].legend(
                fontsize=SC_LAT_LEGEND_FONTSIZE,
                loc="center left",
                bbox_to_anchor=(1, 0.5),
            )
        elif legend_outside is False:
            ax[j].legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
        # labels & conversion
        ax[j].set_xlabel("x")  # will be used by conversion func if we convert
        ax[j].set_ylabel("y")
        if convert_to_mm:
            tickconvert_mm_to_cm(ax[j], "both")
        else:
            ax[j].set_xlabel("x (pixels)")
            ax[j].set_ylabel("y (pixels)")
        figure_file_string = " - " + joint + "Y by X coordinates"
        save_figures(f[j], results_dir, name, figure_file_string)
        if dont_show_plots:
            plt.close(f[j])

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f[j])


def plot_x_by_time(all_steps_data, sc_idxs, info, cfg, plot_panel_instance):
    """2 - Plot joints' x coordinates as a function of time for each SC (optional)"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    convert_to_mm = cfg["convert_to_mm"]
    plot_joints = cfg["plot_joints"]
    sampling_rate = cfg["sampling_rate"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    sc_num = len(sc_idxs)
    f = [[] for _ in range(len(plot_joints))]
    ax = [[] for _ in range(len(plot_joints))]

    # plot
    for j, joint in enumerate(plot_joints):  # joint loop (figures)
        f[j], ax[j] = plt.subplots(1, 1)
        ax[j].set_prop_cycle(
            plt.cycler("color", sns.color_palette(color_palette, sc_num))
        )
        ax[j].set_title(name + " - " + joint + "X")
        time_col_idx = all_steps_data.columns.get_loc(TIME_COL)
        x_col_idx = all_steps_data.columns.get_loc(joint + "x")
        for s in range(sc_num):
            this_x = all_steps_data.iloc[sc_idxs[s], time_col_idx]
            this_y = all_steps_data.iloc[sc_idxs[s], x_col_idx]
            this_label = generate_sc_latency_label(
                all_steps_data, sc_idxs[s], sampling_rate, time_col_idx
            )
            ax[j].plot(this_x, this_y, label=this_label)
        # legend adjustments
        if legend_outside is True:
            ax[j].legend(
                fontsize=SC_LAT_LEGEND_FONTSIZE,
                loc="center left",
                bbox_to_anchor=(1, 0.5),
            )
        elif legend_outside is False:
            ax[j].legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
        # labels & conversion
        ax[j].set_xlabel("Time (s)")  # will be used by conversion func if we convert
        ax[j].set_ylabel("x")
        if convert_to_mm:
            tickconvert_mm_to_cm(ax[j], "y")
        else:
            ax[j].set_ylabel("x (pixels)")
        figure_file_string = " - " + joint + "X coordinate by Time"
        save_figures(f[j], results_dir, name, figure_file_string)
        if dont_show_plots:
            plt.close(f[j])

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f[j])


def plot_angles_by_time(all_steps_data, sc_idxs, info, cfg, plot_panel_instance):
    """3 - Plot joints' angles as a function of time for each SC"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    angles = cfg["angles"]
    sampling_rate = cfg["sampling_rate"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    sc_num = len(sc_idxs)
    f = [[] for _ in range(len(angles["name"]))]
    ax = [[] for _ in range(len(angles["name"]))]

    # plot
    for a, angle in enumerate(angles["name"]):  # angle loop (figures)
        f[a], ax[a] = plt.subplots(1, 1)
        ax[a].set_prop_cycle(
            plt.cycler("color", sns.color_palette(color_palette, sc_num))
        )
        ax[a].set_title(name + " - " + angle + "Angle")
        ax[a].set_ylabel("Angle")
        ax[a].set_xlabel("Time (s)")
        x_col_idx = all_steps_data.columns.get_loc(TIME_COL)
        y_col_idx = all_steps_data.columns.get_loc(angle + "Angle")
        time_col_idx = all_steps_data.columns.get_loc(TIME_COL)
        for s in range(sc_num):
            this_x = all_steps_data.iloc[sc_idxs[s], x_col_idx]
            this_y = all_steps_data.iloc[sc_idxs[s], y_col_idx]
            this_label = generate_sc_latency_label(
                all_steps_data, sc_idxs[s], sampling_rate, time_col_idx
            )
            ax[a].plot(this_x, this_y, label=this_label)
        # legend adjustments
        if legend_outside is True:
            ax[a].legend(
                fontsize=SC_LAT_LEGEND_FONTSIZE,
                loc="center left",
                bbox_to_anchor=(1, 0.5),
            )
        elif legend_outside is False:
            ax[a].legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
        figure_file_string = " - " + angle + "Angle by Time"
        save_figures(f[a], results_dir, name, figure_file_string)
        if dont_show_plots:
            plt.close(f[a])

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f[a])


def plot_hindlimb_stickdiagram(all_steps_data, sc_idxs, info, cfg, plot_panel_instance):
    """4 - Plot a stick diagram of the hindlimb"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    convert_to_mm = cfg["convert_to_mm"]
    plot_joints = cfg["plot_joints"]
    sampling_rate = cfg["sampling_rate"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    sc_num = len(sc_idxs)
    f, ax = plt.subplots(1, 1)
    color_cycle = plt.cycler("color", sns.color_palette(color_palette, sc_num))
    ax.set_prop_cycle(color_cycle)
    time_col_idx = all_steps_data.columns.get_loc(TIME_COL)

    # plot
    # => for timepoints from SC1 to SCend - plot(joint1x, joint1y)
    for s, this_color_dict in zip(range(sc_num), color_cycle):  # SC loop (colors)
        this_color = this_color_dict["color"][:3]
        this_label = generate_sc_latency_label(
            all_steps_data, sc_idxs[s], sampling_rate, time_col_idx
        )
        for i in sc_idxs[s]:  # loop over timepoints of current SC
            this_xs = list()  # for each timepoint, define joints' xy coord new
            this_ys = list()
            for joint in plot_joints:
                x_col_idx = all_steps_data.columns.get_loc(joint + "x")
                y_col_idx = all_steps_data.columns.get_loc(joint + "y")
                this_xs.append(all_steps_data.iloc[i, x_col_idx])
                this_ys.append(all_steps_data.iloc[i, y_col_idx])
            if i == sc_idxs[s][0]:
                ax.plot(this_xs, this_ys, color=this_color, label=this_label)
            else:
                ax.plot(this_xs, this_ys, color=this_color)
    ax.set_title(name + " - Primary Stick Diagram")
    # legend adjustments
    if legend_outside is True:
        ax.legend(
            fontsize=SC_LAT_LEGEND_FONTSIZE, loc="center left", bbox_to_anchor=(1, 0.5)
        )
    elif legend_outside is False:
        ax.legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
    # labels & conversion
    ax.set_xlabel("x")  # will be used by conversion func if we convert
    ax.set_ylabel("y")
    if convert_to_mm:
        tickconvert_mm_to_cm(ax, "both")
    else:
        ax.set_xlabel("x (pixels)")
        ax.set_ylabel("y (pixels)")
    figure_file_string = " - Primary Stick Diagram"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_forelimb_stickdiagram(all_steps_data, sc_idxs, info, cfg, plot_panel_instance):
    """5 - Plot a stick diagram of the forelimb (for hindlimb stepcycles)"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    convert_to_mm = cfg["convert_to_mm"]
    fore_joints = cfg["fore_joints"]
    sampling_rate = cfg["sampling_rate"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # some prep
    sc_num = len(sc_idxs)
    f, ax = plt.subplots(1, 1)
    color_cycle = plt.cycler("color", sns.color_palette(color_palette, sc_num))
    ax.set_prop_cycle(color_cycle)
    time_col_idx = all_steps_data.columns.get_loc(TIME_COL)

    # plot
    for s, this_color in zip(range(sc_num), color_cycle):  # SC loop (colors)
        this_color = this_color["color"][:3]
        this_label = generate_sc_latency_label(
            all_steps_data, sc_idxs[s], sampling_rate, time_col_idx
        )
        for i in sc_idxs[s]:
            this_xs = list()
            this_ys = list()
            for joint in fore_joints:
                x_col_idx = all_steps_data.columns.get_loc(joint + "x")
                y_col_idx = all_steps_data.columns.get_loc(joint + "y")
                this_xs.append(all_steps_data.iloc[i, x_col_idx])
                this_ys.append(all_steps_data.iloc[i, y_col_idx])
            if i == sc_idxs[s][0]:
                ax.plot(this_xs, this_ys, color=this_color, label=this_label)
            else:
                ax.plot(this_xs, this_ys, color=this_color)
    ax.set_title(name + " - Secondary Stick Diagram")
    if convert_to_mm:
        tickconvert_mm_to_cm(ax, "both")
    # legend adjustments
    if legend_outside is True:
        ax.legend(
            fontsize=SC_LAT_LEGEND_FONTSIZE, loc="center left", bbox_to_anchor=(1, 0.5)
        )
    elif legend_outside is False:
        ax.legend(fontsize=SC_LAT_LEGEND_FONTSIZE)
    # labels & conversion
    ax.set_xlabel("x")  # will be used by conversion func if we convert
    ax.set_ylabel("y")
    if convert_to_mm:
        tickconvert_mm_to_cm(ax, "both")
    else:
        ax.set_xlabel("x (pixels)")
        ax.set_ylabel("y (pixels)")
    figure_file_string = " - Secondary Stick Diagram"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_joint_y_by_average_SC(average_data, std_data, info, cfg, plot_panel_instance):
    """6 - Plot joints' y as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    convert_to_mm = cfg["convert_to_mm"]
    bin_num = cfg["bin_num"]
    plot_SE = cfg["plot_SE"]
    sc_num = cfg["sc_num"]
    hind_joints = cfg["hind_joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(hind_joints)))
    )
    x = np.linspace(0, 100, bin_num)
    for joint in hind_joints:  # joint loop (lines)
        y_col_idx = average_data.columns.get_loc(joint + "y")
        this_y = average_data.iloc[:, y_col_idx]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col_idx] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col_idx]
        ax.plot(x, this_y, label=joint)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_title(name + " - Joint Y over average step cycle")
    # labels & conversion
    ax.set_xlabel("Percentage")
    ax.set_ylabel("y")  # used by conversion func
    if convert_to_mm:
        tickconvert_mm_to_cm(ax, "y")
    else:
        ax.set_ylabel("y (pixels)")
    figure_file_string = " - Joint Y-coord.s over average step cycle"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_joint_x_by_average_SC(average_data, std_data, info, cfg, plot_panel_instance):
    """7 - Plot joints' x as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    convert_to_mm = cfg["convert_to_mm"]
    bin_num = cfg["bin_num"]
    plot_SE = cfg["plot_SE"]
    sc_num = cfg["sc_num"]
    hind_joints = cfg["hind_joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(hind_joints)))
    )
    x = np.linspace(0, 100, bin_num)
    for joint in hind_joints:  # joint loop (lines)
        x_col_idx = average_data.columns.get_loc(joint + "x")
        this_y = average_data.iloc[:, x_col_idx]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, x_col_idx] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, x_col_idx]
        ax.plot(x, this_y, label=joint)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_title(name + " - Joint X over average step cycle")
    # labels & conversion
    ax.set_xlabel("Percentage")
    ax.set_ylabel("x")  # used by conversion func
    if convert_to_mm:
        tickconvert_mm_to_cm(ax, "y")
    else:
        ax.set_ylabel("x (pixels)")
    figure_file_string = " - Joint X-coord.s over average step cycle"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_angles_by_average_SC(average_data, std_data, info, cfg, plot_panel_instance):
    """8 - Plot Angles as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    plot_SE = cfg["plot_SE"]
    sc_num = cfg["sc_num"]
    angles = cfg["angles"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(angles["name"])))
    )
    x = np.linspace(0, 100, bin_num)
    ax.set_title(name + " - Joint angles over average step cycle")
    ax.set_xlabel("Percentage")
    ax.set_ylabel("Angle (degree)")
    for angle in angles["name"]:  # angle loop (lines)
        y_col_idx = average_data.columns.get_loc(angle + "Angle")
        this_y = average_data.iloc[:, y_col_idx]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col_idx] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col_idx]
        ax.plot(x, this_y, label=angle)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    figure_file_string = " - Joint angles over average step cycle"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_x_velocities_by_average_SC(
    average_data, std_data, info, cfg, plot_panel_instance
):
    """9 - Plot x velocities as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    convert_to_mm = cfg["convert_to_mm"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    sc_num = cfg["sc_num"]
    hind_joints = cfg["hind_joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(hind_joints)))
    )
    x = np.linspace(0, 100, bin_num)
    ax.set_title(name + " - Joint velocities over average step cycle")
    for joint in hind_joints:  # joint loop (lines)
        y_col_idx = average_data.columns.get_loc(joint + "Velocity")
        this_y = average_data.iloc[:, y_col_idx]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col_idx] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col_idx]
        ax.plot(x, this_y, label=joint)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel(
        "Velocity (x in pixel / " + str(int((1 / sampling_rate) * 1000)) + "ms)"
    )
    if convert_to_mm:
        tickconvert_mm_to_cm(ax, "y")
        ax.set_ylabel(
            "Velocity (x in cm / " + str(int((1 / sampling_rate) * 1000)) + "ms)"
        )
    figure_file_string = " - Joint velocities over average step cycle"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_angular_velocities_by_average_SC(
    average_data, std_data, info, cfg, plot_panel_instance
):
    """10 - Plot angular velocities as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    sc_num = cfg["sc_num"]
    angles = cfg["angles"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(angles["name"])))
    )
    x = np.linspace(0, 100, bin_num)
    ax.set_title(name + " - Angular velocities over average step cycle")
    ax.set_xlabel("Percentage")
    ax.set_ylabel("Velocity (degree / " + str(int((1 / sampling_rate) * 1000)) + "ms)")
    for angle in angles["name"]:  # angle loop (lines)
        y_col_idx = average_data.columns.get_loc(angle + "Angle Velocity")  # space
        this_y = average_data.iloc[:, y_col_idx]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col_idx] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col_idx]
        ax.plot(x, this_y, label=angle)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    figure_file_string = " - Angular velocities over average step cycle"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_x_acceleration_by_average_SC(
    average_data, std_data, info, cfg, plot_panel_instance
):
    """11 - (optional) Plot x acceleration as a function of average SC's percentage"""

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    convert_to_mm = cfg["convert_to_mm"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    sc_num = cfg["sc_num"]
    hind_joints = cfg["hind_joints"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(hind_joints)))
    )
    x = np.linspace(0, 100, bin_num)
    ax.set_title(name + " - Joint accelerations over average step cycle")
    for joint in hind_joints:  # joint loop (lines)
        y_col_idx = average_data.columns.get_loc(joint + "Acceleration")  # no space
        this_y = average_data.iloc[:, y_col_idx]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col_idx] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col_idx]
        ax.plot(x, this_y, label=joint)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    ax.set_xlabel("Percentage")
    ax.set_ylabel(
        "Acceleration (x in pixel / " + str(int((1 / sampling_rate) * 1000)) + "ms)"
    )
    if convert_to_mm:
        tickconvert_mm_to_cm(ax, "y")
        ax.set_ylabel(
            "Acceleration (x in cm / " + str(int((1 / sampling_rate) * 1000)) + "ms)"
        )
    figure_file_string = " - Joint acceleration over average step cycle"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def plot_angular_acceleration_by_average_SC(
    average_data, std_data, info, cfg, plot_panel_instance
):
    """12 - (optional) Plot angular acceleration as a function of average SC's
    percentage
    """

    # unpack
    name = info["name"]
    results_dir = info["results_dir"]
    dont_show_plots = cfg["dont_show_plots"]
    bin_num = cfg["bin_num"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    sc_num = cfg["sc_num"]
    angles = cfg["angles"]
    legend_outside = cfg["legend_outside"]
    color_palette = cfg["color_palette"]

    # plot
    f, ax = plt.subplots(1, 1)
    ax.set_prop_cycle(
        plt.cycler("color", sns.color_palette(color_palette, len(angles["name"])))
    )
    x = np.linspace(0, 100, bin_num)
    ax.set_title(name + " - Angular accelerations over average step cycle")
    ax.set_xlabel("Percentage")
    ax.set_ylabel(
        "Acceleration (degree / " + str(int((1 / sampling_rate) * 1000)) + "ms)"
    )
    for angle in angles["name"]:  # angle loop (lines)
        y_col_idx = average_data.columns.get_loc(angle + "Angle Acceleration")
        this_y = average_data.iloc[:, y_col_idx]  # average & std_data share colnames
        if plot_SE:
            this_std = std_data.iloc[:, y_col_idx] / np.sqrt(sc_num)
        else:
            this_std = std_data.iloc[:, y_col_idx]
        ax.plot(x, this_y, label=angle)
        ax.fill_between(x, this_y - this_std, this_y + this_std, alpha=0.2)
    # legend adjustments
    if legend_outside is True:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    elif legend_outside is False:
        ax.legend()
    figure_file_string = " - Angular acceleration over average step cycle"
    save_figures(f, results_dir, name, figure_file_string)
    if dont_show_plots:
        plt.close(f)

    # add figure to plot panel figures list
    if dont_show_plots is False:  # -> show plot panel
        plot_panel_instance.figures.append(f)


def save_figures(figure, results_dir, name, figure_file_string):
    """Save figures as pngs to results_dir and as svgs to separate subfolders"""
    # pngs to results_dir
    figure.savefig(
        os.path.join(results_dir, name + figure_file_string + ".png"),
        bbox_inches="tight",
    )
    # svgs to subfolders
    svg_dir = os.path.join(results_dir, "SVG Figures")
    if not os.path.exists(svg_dir):
        os.makedirs(svg_dir)
    figure.savefig(
        os.path.join(svg_dir, name + figure_file_string + ".svg"), bbox_inches="tight"
    )


def tickconvert_mm_to_cm(axis, whichlabel):
    """Convert axis-ticks from mm (of data) to cm"""
    if (whichlabel == "both") | (whichlabel == "x"):
        x_ticks = axis.get_xticks()
        x_ticklabels = []
        for t in x_ticks:
            x_ticklabels.append(str(round(t / 10, 2)))
        axis.set_xticks(x_ticks, labels=x_ticklabels)
        old_xlabel = axis.get_xlabel()
        axis.set_xlabel(old_xlabel + " (cm)")
    if (whichlabel == "both") | (whichlabel == "y"):
        y_ticks = axis.get_yticks()
        y_ticklabels = []
        for t in y_ticks:
            y_ticklabels.append(str(round(t / 10, 2)))
        axis.set_yticks(y_ticks, labels=y_ticklabels)
        old_ylabel = axis.get_ylabel()
        axis.set_ylabel(old_ylabel + " (cm)")


def generate_sc_latency_label(all_steps_data, this_sc_idx, sampling_rate, time_col_idx):
    if sampling_rate <= 100:
        float_precision = 2  # how many decimals we round to
    else:
        float_precision = 4
    this_label = (
        str(
            round(
                all_steps_data.iloc[this_sc_idx[0], time_col_idx],
                float_precision,
            )
        )
        + "-"
        + str(
            round(
                all_steps_data.iloc[this_sc_idx[-1], time_col_idx],
                float_precision,
            )
        )
        + "s"
    )
    return this_label

# %% imports
from autogaita.group.group_utils import (
    check_mouse_conversion,
    save_figures,
    ytickconvert_mm_to_cm,
    ylabel_velocity_and_acceleration,
)
from autogaita.universal3D.universal3D_utils import extract_feature_column
import numpy as np
import matplotlib.pyplot as plt


# %% constants
from autogaita.group.group_constants import STD_ALPHA, STD_LW


# %% ..........................  workflow step #5 - plots  ............................


def plot_results(g_avg_dfs, g_std_dfs, folderinfo, cfg, plot_panel_instance):
    """Plot results - main function (inner functions loop over groups)"""

    # unpack
    angles = cfg["angles"]
    tracking_software = cfg["tracking_software"]
    # prep
    plot_horizontal_coord = False

    # ........................1 - y coords over average SC..............................
    plot_joint_y_by_average_SC(
        g_avg_dfs, g_std_dfs, folderinfo, cfg, plot_panel_instance
    )
    plt.close("all")

    # .......................2 - x coords over average SC (optional)....................
    if tracking_software in ["DLC", "SLEAP"]:
        if cfg["analyse_average_x"] is True:
            plot_horizontal_coord = True
    elif tracking_software == "Universal 3D":
        if cfg["analyse_average_y"] is True:
            plot_horizontal_coord = True
    if plot_horizontal_coord:
        plot_joint_x_by_average_SC(
            g_avg_dfs, g_std_dfs, folderinfo, cfg, plot_panel_instance
        )
        plt.close("all")

    # ........................3 - angles over average SC................................
    if angles["name"]:
        plot_angles_by_average_SC(
            g_avg_dfs, g_std_dfs, folderinfo, cfg, plot_panel_instance
        )
        plt.close("all")

    # .................4 - average x velocities over SC percentage......................
    plot_x_velocities_by_average_SC(
        g_avg_dfs, g_std_dfs, folderinfo, cfg, plot_panel_instance
    )
    plt.close("all")

    # ..............5 - average angular velocities over SC percentage...................
    if angles["name"]:
        plot_angular_velocities_by_average_SC(
            g_avg_dfs, g_std_dfs, folderinfo, cfg, plot_panel_instance
        )
        plt.close("all")

    # ........................optional - 6 - build plot panel..........................
    if cfg["dont_show_plots"] is True:
        pass  # going on without building the plot window
    elif cfg["dont_show_plots"] is False:  # -> show plot panel
        # Destroy loading screen and build plot panel with all figures
        plot_panel_instance.destroy_plot_panel_loading_screen()
        plot_panel_instance.build_plot_panel()


def plot_joint_y_by_average_SC(
    g_avg_dfs, g_std_dfs, folderinfo, cfg, plot_panel_instance
):
    """1 - Plot joints' y/Z as a function of average SC's percentage"""

    # unpack
    group_names = folderinfo["group_names"]
    results_dir = folderinfo["results_dir"]
    bin_num = cfg["bin_num"]
    joint_color_cycler = cfg["joint_color_cycler"]
    group_color_cycler = cfg["group_color_cycler"]
    which_leg = cfg["which_leg"]
    plot_SE = cfg["plot_SE"]
    tracking_software = cfg["tracking_software"]
    joints = cfg["joints"]
    dont_show_plots = cfg["dont_show_plots"]
    legend_outside = cfg["legend_outside"]

    # A - lines = joints & figures = groups
    for g, group_name in enumerate(group_names):
        f, ax = plt.subplots(1, 1)
        ax.set_prop_cycle(joint_color_cycler)
        x = np.linspace(0, 100, bin_num)
        for joint in joints:
            if tracking_software in ["DLC", "SLEAP"]:
                y_col = g_avg_dfs[g].columns.get_loc(joint + "y")
            elif tracking_software == "Universal 3D":
                # check for bodyside-specificity
                feature = "Z"
                y_col = extract_feature_column(g_avg_dfs[g], joint, which_leg, feature)
            y = g_avg_dfs[g].iloc[:, y_col]  # average & stddata share colnames
            if plot_SE:
                std = g_std_dfs[g].iloc[:, y_col] / np.sqrt(g_std_dfs[g]["N"][0])
            else:
                std = g_std_dfs[g].iloc[:, y_col]
            ax.plot(x, y, label=joint)
            ax.fill_between(x, y - std, y + std, alpha=STD_ALPHA, lw=STD_LW)

        # legend adjustments
        if legend_outside is True:
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        elif legend_outside is False:
            ax.legend()
        ax.set_xlabel("Percentage")
        if tracking_software in ["DLC", "SLEAP"]:
            ax.set_title(group_name + " - Joint Y over average step cycle")
            if check_mouse_conversion("y", cfg):
                ytickconvert_mm_to_cm(ax)
                ax.set_ylabel("y (cm)")
            else:
                ax.set_ylabel("y (pixel)")
            figure_file_string = " - Joint y-coord.s over average step cycle"
        elif tracking_software == "Universal 3D":
            ax.set_title(
                group_name + " - " + which_leg + " Joint Z over average step cycle"
            )
            ax.set_ylabel("Z")
            figure_file_string = " - Joint Z-coord.s over average step cycle"
        save_figures(f, results_dir, group_name + figure_file_string)

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f)

    # B - lines = groups & figures = joints
    for j, joint in enumerate(joints):
        f, ax = plt.subplots(1, 1)
        ax.set_prop_cycle(group_color_cycler)
        x = np.linspace(0, 100, bin_num)
        for g, group_name in enumerate(group_names):
            if tracking_software in ["DLC", "SLEAP"]:
                y_col = g_avg_dfs[g].columns.get_loc(joint + "y")
            elif tracking_software == "Universal 3D":
                # check for bodyside-specificity
                feature = "Z"
                y_col = extract_feature_column(g_avg_dfs[g], joint, which_leg, feature)
            y = g_avg_dfs[g].iloc[:, y_col]  # average & stddata share colnames
            if plot_SE:
                std = g_std_dfs[g].iloc[:, y_col] / np.sqrt(g_std_dfs[g]["N"][0])
            else:
                std = g_std_dfs[g].iloc[:, y_col]
            ax.plot(x, y, label=group_name)
            ax.fill_between(x, y - std, y + std, alpha=STD_ALPHA, lw=STD_LW)
        # legend adjustments
        if legend_outside is True:
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        elif legend_outside is False:
            ax.legend()
        ax.set_xlabel("Percentage")
        if tracking_software in ["DLC", "SLEAP"]:
            ax.set_title(joint + "Y over average step cycle")
            if check_mouse_conversion("y", cfg):
                ytickconvert_mm_to_cm(ax)
                ax.set_ylabel("y (cm)")
            else:
                ax.set_ylabel("y (pixel)")
            figure_file_string = "- Y-coord.s over average step cycle"
        elif tracking_software == "Universal 3D":
            # do title_leg thingy only for B plots, because here we have separate
            # figures for joints / angles (in A plots just throw leg into title)
            if joint + "Z" in g_avg_dfs[g].columns:
                title_leg = ""
            else:
                title_leg = which_leg
            ax.set_title(title_leg + " " + joint + " Z over average step cycle")
            ax.set_ylabel("Z")
            figure_file_string = "- Z-coord.s over average step cycle"
        save_figures(f, results_dir, joint + figure_file_string)

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f)


def plot_joint_x_by_average_SC(
    g_avg_dfs, g_std_dfs, folderinfo, cfg, plot_panel_instance
):
    """2 - Plot joints' x/Y as a function of average SC's percentage"""

    # unpack
    group_names = folderinfo["group_names"]
    results_dir = folderinfo["results_dir"]
    bin_num = cfg["bin_num"]
    joint_color_cycler = cfg["joint_color_cycler"]
    group_color_cycler = cfg["group_color_cycler"]
    which_leg = cfg["which_leg"]
    plot_SE = cfg["plot_SE"]
    tracking_software = cfg["tracking_software"]
    joints = cfg["joints"]
    dont_show_plots = cfg["dont_show_plots"]
    legend_outside = cfg["legend_outside"]

    # A - lines = joints & figures = groups
    for g, group_name in enumerate(group_names):
        f, ax = plt.subplots(1, 1)
        ax.set_prop_cycle(joint_color_cycler)
        x = np.linspace(0, 100, bin_num)
        for joint in joints:
            if tracking_software in ["DLC", "SLEAP"]:
                y_col = g_avg_dfs[g].columns.get_loc(joint + "x")
            elif tracking_software == "Universal 3D":
                # check for bodyside-specificity
                feature = "Y"
                y_col = extract_feature_column(g_avg_dfs[g], joint, which_leg, feature)
            y = g_avg_dfs[g].iloc[:, y_col]  # average & stddata share colnames
            if plot_SE:
                std = g_std_dfs[g].iloc[:, y_col] / np.sqrt(g_std_dfs[g]["N"][0])
            else:
                std = g_std_dfs[g].iloc[:, y_col]
            ax.plot(x, y, label=joint)
            ax.fill_between(x, y - std, y + std, alpha=STD_ALPHA, lw=STD_LW)

        # legend adjustments
        if legend_outside is True:
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        elif legend_outside is False:
            ax.legend()
        ax.set_xlabel("Percentage")
        if tracking_software in ["DLC", "SLEAP"]:
            ax.set_title(group_name + " - Joint X over average step cycle")
            if check_mouse_conversion("x", cfg):
                ytickconvert_mm_to_cm(ax)
                ax.set_ylabel("x (cm)")
            else:
                ax.set_ylabel("x (pixel)")
            figure_file_string = " - Joint x-coord.s over average step cycle"
        elif tracking_software == "Universal 3D":
            ax.set_title(
                group_name + " - " + which_leg + " Joint Y over average step cycle"
            )
            ax.set_ylabel("Y")
            figure_file_string = " - Joint Y-coord.s over average step cycle"
        save_figures(f, results_dir, group_name + figure_file_string)

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f)

    # B - lines = groups & figures = joints
    for j, joint in enumerate(joints):
        f, ax = plt.subplots(1, 1)
        ax.set_prop_cycle(group_color_cycler)
        x = np.linspace(0, 100, bin_num)
        for g, group_name in enumerate(group_names):
            if tracking_software in ["DLC", "SLEAP"]:
                y_col = g_avg_dfs[g].columns.get_loc(joint + "x")
            elif tracking_software == "Universal 3D":
                # check for bodyside-specificity
                feature = "Y"
                y_col = extract_feature_column(g_avg_dfs[g], joint, which_leg, feature)
            y = g_avg_dfs[g].iloc[:, y_col]  # average & stddata share colnames
            if plot_SE:
                std = g_std_dfs[g].iloc[:, y_col] / np.sqrt(g_std_dfs[g]["N"][0])
            else:
                std = g_std_dfs[g].iloc[:, y_col]
            ax.plot(x, y, label=group_name)
            ax.fill_between(x, y - std, y + std, alpha=STD_ALPHA, lw=STD_LW)
        # legend adjustments
        if legend_outside is True:
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        elif legend_outside is False:
            ax.legend()
        ax.set_xlabel("Percentage")
        if tracking_software in ["DLC", "SLEAP"]:
            ax.set_title(joint + "X over average step cycle")
            if check_mouse_conversion("x", cfg):
                ytickconvert_mm_to_cm(ax)
                ax.set_ylabel("x (cm)")
            else:
                ax.set_ylabel("x (pixel)")
            figure_file_string = "- X-coord.s over average step cycle"
        elif tracking_software == "Universal 3D":
            # do title_leg thingy only for B plots, because here we have separate
            # figures for joints / angles (in A plots just throw leg into title)
            if joint + "Y" in g_avg_dfs[g].columns:
                title_leg = ""
            else:
                title_leg = which_leg
            ax.set_title(title_leg + " " + joint + " Y over average step cycle")
            ax.set_ylabel("Y")
            figure_file_string = "- Y-coord.s over average step cycle"
        save_figures(f, results_dir, joint + figure_file_string)

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f)


def plot_angles_by_average_SC(
    g_avg_dfs, g_std_dfs, folderinfo, cfg, plot_panel_instance
):
    """2 - Plot Angles as a function of average SC's percentage"""

    # unpack
    group_names = folderinfo["group_names"]
    results_dir = folderinfo["results_dir"]
    bin_num = cfg["bin_num"]
    angle_color_cycler = cfg["angle_color_cycler"]
    group_color_cycler = cfg["group_color_cycler"]
    which_leg = cfg["which_leg"]
    plot_SE = cfg["plot_SE"]
    tracking_software = cfg["tracking_software"]
    angles = cfg["angles"]
    dont_show_plots = cfg["dont_show_plots"]
    legend_outside = cfg["legend_outside"]

    # A - lines = angles & figures = groups
    for g, group_name in enumerate(group_names):
        f, ax = plt.subplots(1, 1)
        ax.set_prop_cycle(angle_color_cycler)
        x = np.linspace(0, 100, bin_num)
        for angle in angles["name"]:
            if tracking_software in ["DLC", "SLEAP"]:
                y_col = g_avg_dfs[g].columns.get_loc(angle + "Angle")
            elif tracking_software == "Universal 3D":
                # check for bodyside-specificity
                feature = "Angle"
                y_col = extract_feature_column(g_avg_dfs[g], angle, which_leg, feature)
            y = g_avg_dfs[g].iloc[:, y_col]  # sharing colnames
            if plot_SE:
                std = g_std_dfs[g].iloc[:, y_col] / np.sqrt(g_std_dfs[g]["N"][0])
            else:
                std = g_std_dfs[g].iloc[:, y_col]
            ax.plot(x, y, label=angle)
            ax.fill_between(x, y - std, y + std, alpha=STD_ALPHA, lw=STD_LW)
        # legend adjustments
        if legend_outside is True:
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        elif legend_outside is False:
            ax.legend()
        ax.set_xlabel("Percentage")
        ax.set_ylabel("Angle (degrees)")
        if tracking_software in ["DLC", "SLEAP"]:
            ax.set_title(group_name + " - Joint angles over average step cycle")
        elif tracking_software == "Universal 3D":
            ax.set_title(
                group_name + " - " + which_leg + " joint angles over average step cycle"
            )
        figure_file_string = " - Joint angles over average step cycle"
        save_figures(f, results_dir, group_name + figure_file_string)

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f)

    # B - lines = groups & figures = angles
    for a, angle in enumerate(angles["name"]):
        f, ax = plt.subplots(1, 1)
        ax.set_prop_cycle(group_color_cycler)
        x = np.linspace(0, 100, bin_num)
        for g, group_name in enumerate(group_names):
            if tracking_software in ["DLC", "SLEAP"]:
                y_col = g_avg_dfs[g].columns.get_loc(angle + "Angle")
            elif tracking_software == "Universal 3D":
                # check for bodyside-specificity
                feature = "Angle"
                y_col = extract_feature_column(g_avg_dfs[g], angle, which_leg, feature)
            y = g_avg_dfs[g].iloc[:, y_col]  # average & stddata share colnames
            if plot_SE:
                std = g_std_dfs[g].iloc[:, y_col] / np.sqrt(g_std_dfs[g]["N"][0])
            else:
                std = g_std_dfs[g].iloc[:, y_col]
            ax.plot(x, y, label=group_name)
            ax.fill_between(x, y - std, y + std, alpha=STD_ALPHA, lw=STD_LW)
        # legend adjustments
        if legend_outside is True:
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        elif legend_outside is False:
            ax.legend()
        ax.set_xlabel("Percentage")
        ax.set_ylabel("Angle (degrees)")
        if tracking_software in ["DLC", "SLEAP"]:
            ax.set_title(angle + "angle over average step cycle")
        elif tracking_software == "Universal 3D":
            if angle + "Angle" in g_avg_dfs[g].columns:
                title_leg = ""
            else:
                title_leg = which_leg
            ax.set_title(title_leg + " " + angle + " angle over average step cycle")
        figure_file_string = " - Angle over average step cycle"
        save_figures(f, results_dir, angle + figure_file_string)

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f)


def plot_x_velocities_by_average_SC(
    g_avg_dfs, g_std_dfs, folderinfo, cfg, plot_panel_instance
):
    """3 - Plot x velocities as a function of average SC's percentage"""

    # unpack
    group_names = folderinfo["group_names"]
    results_dir = folderinfo["results_dir"]
    bin_num = cfg["bin_num"]
    joint_color_cycler = cfg["joint_color_cycler"]
    group_color_cycler = cfg["group_color_cycler"]
    which_leg = cfg["which_leg"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    tracking_software = cfg["tracking_software"]
    joints = cfg["joints"]
    dont_show_plots = cfg["dont_show_plots"]
    legend_outside = cfg["legend_outside"]

    # A - lines = joints & figures = groups
    for g, group_name in enumerate(group_names):
        f, ax = plt.subplots(1, 1)
        ax.set_prop_cycle(joint_color_cycler)
        x = np.linspace(0, 100, bin_num)
        for joint in joints:
            if tracking_software in ["DLC", "SLEAP"]:
                y_col = g_avg_dfs[g].columns.get_loc(joint + "Velocity")
            elif tracking_software == "Universal 3D":
                # check for bodyside-specificity
                feature = "Velocity"
                y_col = extract_feature_column(g_avg_dfs[g], joint, which_leg, feature)
            y = g_avg_dfs[g].iloc[:, y_col]
            if plot_SE:
                std = g_std_dfs[g].iloc[:, y_col] / np.sqrt(g_std_dfs[g]["N"][0])
            else:
                std = g_std_dfs[g].iloc[:, y_col]
            ax.plot(x, y, label=joint)
            ax.fill_between(x, y - std, y + std, alpha=0.2)
        # legend adjustments
        if legend_outside is True:
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        elif legend_outside is False:
            ax.legend()
        ax.set_xlabel("Percentage")
        if tracking_software in ["DLC", "SLEAP"]:
            if check_mouse_conversion("x", cfg):
                ytickconvert_mm_to_cm(ax)
                unit = "x in cm"
            else:
                unit = "x in pixels"
            ax.set_title(group_name + " - Joint velocities over average step cycle")
        elif tracking_software == "Universal 3D":
            unit = "Y in (your units)"
            ax.set_title(
                group_name
                + " - "
                + which_leg
                + " joint velocities over average step cycle"
            )
        # note unit-input-argument is depending on conditional statements above
        ax.set_ylabel(ylabel_velocity_and_acceleration("Velocity", unit, sampling_rate))
        figure_file_string = " - Joint velocities over average step cycle"
        save_figures(f, results_dir, group_name + figure_file_string)

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f)

    # B - lines = groups & figures = joints
    for j, joint in enumerate(joints):
        f, ax = plt.subplots(1, 1)
        ax.set_prop_cycle(group_color_cycler)
        x = np.linspace(0, 100, bin_num)
        for g, group_name in enumerate(group_names):
            if tracking_software in ["DLC", "SLEAP"]:
                y_col = g_avg_dfs[g].columns.get_loc(joint + "Velocity")
            elif tracking_software == "Universal 3D":
                # check for bodyside-specificity
                feature = "Velocity"
                y_col = extract_feature_column(g_avg_dfs[g], joint, which_leg, feature)
            y = g_avg_dfs[g].iloc[:, y_col]  # average & stddata share colnames
            if plot_SE:
                std = g_std_dfs[g].iloc[:, y_col] / np.sqrt(g_std_dfs[g]["N"][0])
            else:
                std = g_std_dfs[g].iloc[:, y_col]
            ax.plot(x, y, label=group_name)
            ax.fill_between(x, y - std, y + std, alpha=STD_ALPHA, lw=STD_LW)
        # legend adjustments
        if legend_outside is True:
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        elif legend_outside is False:
            ax.legend()
        ax.set_xlabel("Percentage")
        if tracking_software in ["DLC", "SLEAP"]:
            if check_mouse_conversion("x", cfg):
                ytickconvert_mm_to_cm(ax)
                unit = "x in cm"
            else:
                unit = "x in pixels"
            ax.set_title(joint + " - Joint velocities over average step cycle")
        elif tracking_software == "Universal 3D":
            unit = "Y in (your units)"
            if joint + "Velocity" in g_avg_dfs[g].columns:
                title_leg = ""
            else:
                title_leg = which_leg
            ax.set_title(
                title_leg + " " + joint + " velocities over average step cycle"
            )
        # note unit-input-argument is depending on conditional statements above
        ax.set_ylabel(ylabel_velocity_and_acceleration("Velocity", unit, sampling_rate))
        figure_file_string = "- Velocities over average step cycle"
        save_figures(f, results_dir, joint + figure_file_string)

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f)


def plot_angular_velocities_by_average_SC(
    g_avg_dfs, g_std_dfs, folderinfo, cfg, plot_panel_instance
):
    """4 - Plot angular velocities as a function of average SC's percentage"""
    # unpack
    group_names = folderinfo["group_names"]
    results_dir = folderinfo["results_dir"]
    bin_num = cfg["bin_num"]
    angle_color_cycler = cfg["angle_color_cycler"]
    group_color_cycler = cfg["group_color_cycler"]
    which_leg = cfg["which_leg"]
    sampling_rate = cfg["sampling_rate"]
    plot_SE = cfg["plot_SE"]
    tracking_software = cfg["tracking_software"]
    angles = cfg["angles"]
    dont_show_plots = cfg["dont_show_plots"]
    legend_outside = cfg["legend_outside"]

    # A - lines = joints & figures = groups
    for g, group_name in enumerate(group_names):
        f, ax = plt.subplots(1, 1)
        ax.set_prop_cycle(angle_color_cycler)
        x = np.linspace(0, 100, bin_num)
        for angle in angles["name"]:
            if tracking_software in ["DLC", "SLEAP"]:
                y_col = g_avg_dfs[g].columns.get_loc(angle + "Angle Velocity")
            elif tracking_software == "Universal 3D":
                # check for bodyside-specificity
                feature = "Angle Velocity"
                y_col = extract_feature_column(g_avg_dfs[g], angle, which_leg, feature)
            y = g_avg_dfs[g].iloc[:, y_col]
            if plot_SE:
                std = g_std_dfs[g].iloc[:, y_col] / np.sqrt(g_std_dfs[g]["N"][0])
            else:
                std = g_std_dfs[g].iloc[:, y_col]
            ax.plot(x, y, label=angle)
            ax.fill_between(x, y - std, y + std, alpha=0.2)
        # legend adjustments
        if legend_outside is True:
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        elif legend_outside is False:
            ax.legend()
        ax.set_xlabel("Percentage")
        ax.set_ylabel(
            ylabel_velocity_and_acceleration("Velocity", "degrees", sampling_rate)
        )
        if tracking_software in ["DLC", "SLEAP"]:
            ax.set_title(group_name + " - Angular velocities over average step cycle")
        elif tracking_software == "Universal 3D":
            ax.set_title(
                group_name
                + " - "
                + which_leg
                + " angular velocities over average step cycle"
            )
        figure_file_string = " - Angular velocities over average step cycle"
        save_figures(f, results_dir, group_name + figure_file_string)

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f)

    # B - lines = groups & figures = joints
    for a, angle in enumerate(angles["name"]):
        f, ax = plt.subplots(1, 1)
        ax.set_prop_cycle(group_color_cycler)
        x = np.linspace(0, 100, bin_num)
        for g, group_name in enumerate(group_names):
            if tracking_software in ["DLC", "SLEAP"]:
                y_col = g_avg_dfs[g].columns.get_loc(angle + "Angle Velocity")
            elif tracking_software == "Universal 3D":
                # check for bodyside-specificity
                feature = "Angle Velocity"
                y_col = extract_feature_column(g_avg_dfs[g], angle, which_leg, feature)
            y = g_avg_dfs[g].iloc[:, y_col]  # average & stddata share colnames
            if plot_SE:
                std = g_std_dfs[g].iloc[:, y_col] / np.sqrt(g_std_dfs[g]["N"][0])
            else:
                std = g_std_dfs[g].iloc[:, y_col]
            ax.plot(x, y, label=group_name)
            ax.fill_between(x, y - std, y + std, alpha=STD_ALPHA, lw=STD_LW)
        # legend adjustments
        if legend_outside is True:
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        elif legend_outside is False:
            ax.legend()
        ax.set_xlabel("Percentage")
        ax.set_ylabel(
            ylabel_velocity_and_acceleration("Velocity", "degrees", sampling_rate)
        )
        if tracking_software in ["DLC", "SLEAP"]:
            ax.set_title(angle + "- Angular velocities over average step cycle")
        elif tracking_software == "Universal 3D":
            if angle + "Angle" in g_avg_dfs[g].columns:
                title_leg = ""
            else:
                title_leg = which_leg
            ax.set_title(
                title_leg
                + " "
                + angle
                + " - Angular velocities over average step cycle"
            )
        figure_file_string = " - Angular Velocities over average step cycle"
        save_figures(f, results_dir, angle + figure_file_string)

        # add figure to plot panel figures list
        if dont_show_plots is False:  # -> show plot panel
            plot_panel_instance.figures.append(f)

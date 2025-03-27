FLOAT_VARS = ["pixel_to_mm_ratio"]
INT_VARS = [
    "sampling_rate",
    "x_sc_broken_threshold",
    "y_sc_broken_threshold",
    "bin_num",
    "mouse_num",
    "run_num",
    "plot_joint_number",
]
LIST_VARS = [
    "hind_joints",
    "fore_joints",
    "x_standardisation_joint",
    "y_standardisation_joint",
    "beam_hind_jointadd",
    "beam_fore_jointadd",
    "beam_col_left",
    "beam_col_right",
]
DICT_VARS = ["angles"]
# TK_BOOL/STR_VARS are only used for initialising widgets based on cfg file
# (note that numbers are initialised as strings)
TK_BOOL_VARS = [
    "subtract_beam",
    "dont_show_plots",
    "convert_to_mm",
    "x_acceleration",
    "angular_acceleration",
    "save_to_xls",
    "plot_SE",
    "standardise_y_at_SC_level",
    "standardise_y_to_a_joint",
    "standardise_x_coordinates",
    "invert_y_axis",
    "flip_gait_direction",
    "analyse_average_x",
    "legend_outside",
]
TK_STR_VARS = [
    "mouse_num",  # (config file's) results dict
    "run_num",
    "root_dir",
    "sctable_filename",
    "data_string",
    "beam_string",
    "premouse_string",
    "postmouse_string",
    "prerun_string",
    "postrun_string",
    "sampling_rate",  # (config file's) cfg dict
    "pixel_to_mm_ratio",
    "x_sc_broken_threshold",
    "y_sc_broken_threshold",
    "bin_num",
    "plot_joint_number",
    "color_palette",
    "results_dir",
]
GUI_SPECIFIC_VARS = {
    "FLOAT_VARS": FLOAT_VARS,
    "INT_VARS": INT_VARS,
    "LIST_VARS": LIST_VARS,
    "DICT_VARS": DICT_VARS,
    "TK_BOOL_VARS": TK_BOOL_VARS,
    "TK_STR_VARS": TK_STR_VARS,
}

# Issues & stats results are stored in these textfiles (config json from mouseanalysis)
GROUP_CONFIG_TXT_FILENAME = "Group Analysis Configuration.txt"
STATS_TXT_FILENAME = "Stats Summary.txt"
PCA_PERMANOVA_TXT_FILENAME = "PCA PERMANOVA Results.txt"
MULTCOMP_EXCEL_FILENAME_1 = "Stats Multiple Comparison - Version 1.xlsx"
MULTCOMP_EXCEL_FILENAME_2 = "Stats Multiple Comparison - Version 2.xlsx"

# FIRST LEVEL CONFIG VARS TO NOT CHECK FOR EQUIVALENCE
FIRST_LEVEL_CFG_VARS_TO_NOT_CHECK = [
    "sc_times_in_frames",
    "autogaita_version",
    "pixel_to_mm_ratio",
    "coordinate_standardisation_xls",
    "interpolate_data",
]
# TRACKING SOFTWARE FAMILIES
# => DLC & SLEAP can be compared with each other but not with Universal 3D
TRACKING_SOFTWARE_2D = ["DLC", "SLEAP"]
TRACKING_SOFTWARE_3D = ["Universal 3D"]


# DERIVED CFG KEYS TO NOT WRITE TO CONFIG.JSON
# => cyclers not json serialisable and loaded is just used in a unit test
CFG_KEYS_NOT_FOR_JSON = [
    "group_color_cycler",
    "group_color_dict",
    "joint_color_cycler",
    "angle_color_cycler",
    "loaded",
]

# EXPORT XLS
NORM_SHEET_NAME = "Normalised Stepcycles"
ORIG_SHEET_NAME = "Original Stepcycles"
X_STANDARDISED_SHEET_NAME = "X-Standardised Stepcycles"
AVG_SHEET_NAME = "Average Stepcycle"
NORM_GROUP_SHEET_NAME = "Normalised Group Stepcycles"
ORIG_GROUP_SHEET_NAME = "Original Group Stepcycles"
X_STAND_GROUP_SHEET_NAME = "X-Standardised Group Stepcycles"
AVG_GROUP_SHEET_NAME = "Average Group Stepcycles"
STD_GROUP_SHEET_NAME = "Standard Deviation Group Stepcycles"
G_AVG_GROUP_SHEET_NAME = "Grand Average Group Stepcycles"
G_STD_GROUP_SHEET_NAME = "Grand Standard Deviation Group Stepcycles"

# SPLIT STRING (for _dlc first-level) & COLS OF DFs CREATED IN THIS SCRIPT
SPLIT_STRING = " - "
SC_NUM_COL = "SC Number"
GROUP_COL = "Group"
N_COL = "N"  # for grand average dfs

# STATS
CONTRASTS_COL = "Contrasts"
CONTRAST_SPLIT_STR = " & "
TTEST_MASK_THRESHOLD = 0.05
TTEST_P_COL = "Ttest p"
TTEST_T_COL = "Ttest t"
TTEST_MASK_COL = "Ttest Mask"
CLUSTER_TMASS_COL = "Cluster Tmass"
CLUSTER_P_COL = "Cluster p"
CLUSTER_MASK_COL = "Cluster Mask"
MULTCOMP_RESULT_TYPES = ["q", "p", "CI low", "CI high"]
MULTCOMP_RESULT_P_IDENTIFIER = "p"
MULTCOMP_RESULT_SPLIT_STR = " | "
MULTCOMP_EXCEL_COLS = [
    "Tukey's q",
    "p value",
    "CI",
    "reject",
    "sig. level",
]

# PLOTS
PCA_BARPLOT_BARCOLOR = "#c74767"  # deep rose
PCA_BARPLOT_LINECOLOR = "#005f6a"  # petrol
PCA_CUSTOM_SCATTER_OUTER_SEPARATOR = ";"
PCA_CUSTOM_SCATTER_INNER_SEPARATOR = ","
STATS_PLOTS_LEGEND_SIZE = 6
STATS_PLOTS_SUPLABEL_SIZE = 12
BOX_COLOR = "#fe420f"  # significance boxes - col = orangered
BOX_ALPHA = 0.1
STD_ALPHA = 0.2  # std boxes around means
STD_LW = 0

# PLOT GUI COLORS
FG_COLOR = "#5a7d9a"  # steel blue
HOVER_COLOR = "#8ab8fe"  # carolina blue


# CROSS SPECIES PREPARATION
# => species' joints are renamed to JOINT_PREFIX + idx (Joint1 is the most distal one)
#    and saved to a subfolder of each group dir
CROSS_SPECIES_DIR_NAME = "Cross Species Columns"
CROSS_SPECIES_JOINT_PREFIX = "Joint"
# column suffixes that belong to a joint (angle suffixes cover angle columns)
CROSS_SPECIES_2D_COORD_SUFFIXES = ["x", "y", "likelihood"]
CROSS_SPECIES_3D_COORD_SUFFIXES = ["X", "Y", "Z"]
CROSS_SPECIES_JOINT_SUFFIXES = ["Velocity", "Acceleration"]
CROSS_SPECIES_ANGLE_SUFFIXES = ["Angle", "Angle Velocity", "Angle Acceleration"]
CROSS_SPECIES_3D_SIDES = ["", ", left", ", right"]
# first-level cfg keys that hold joint names & are translated in the config.json copy
CROSS_SPECIES_CFG_JOINT_LIST_KEYS = ["hind_joints", "fore_joints", "joints"]
CROSS_SPECIES_CFG_JOINT_STRING_KEYS = [
    "x_standardisation_joint",
    "y_standardisation_joint",
    "z_standardisation_joint",
]
# first-level cfg keys that may differ between species (only skipped if all groups are
# cross-species dirs) - sampling_rate is not checked but users are warned if it differs
CROSS_SPECIES_CFG_VARS_TO_NOT_CHECK = [
    "sampling_rate",
    "x_sc_broken_threshold",
    "y_sc_broken_threshold",
    "invert_y_axis",
    "flip_gait_direction",
    "standardise_y_at_SC_level",
    "standardise_y_to_a_joint",
    "x_standardisation_joint",
    "y_standardisation_joint",
    "fore_joints",
    "standardise_z_at_SC_level",
    "standardise_z_to_a_joint",
    "z_standardisation_joint",
]

# per-ID sheets that group analysis reads & cross species preparation renames
# => the *_GROUP_SHEET_NAMEs above are group outputs (results_dir), not inputs
CROSS_SPECIES_SHEET_NAMES = [
    ORIG_SHEET_NAME,
    NORM_SHEET_NAME,
    X_STANDARDISED_SHEET_NAME,
    AVG_SHEET_NAME,
]

# Issues & stats results are stored in these textfiles (config json from mouseanalysis)
GROUP_CONFIG_TXT_FILENAME = "Group Analysis Configuration.txt"
ISSUES_TXT_FILENAME = "Issues.txt"
STATS_TXT_FILENAME = "Stats Summary.txt"
MULTCOMP_EXCEL_FILENAME_1 = "Stats Multiple Comparison - Version 1.xlsx"
MULTCOMP_EXCEL_FILENAME_2 = "Stats Multiple Comparison - Version 2.xlsx"
CONFIG_JSON_FILENAME = "config.json"

# Info text width
INFO_TEXT_WIDTH = 64

# EXPORT XLS
NORM_SHEET_NAME = "Normalised Stepcycles"
ORIG_SHEET_NAME = "Original Stepcycles"
X_STANDARDISED_SHEET_NAME = "X-Standardised Stepcycles"
NORM_GROUP_SHEET_NAME = "Normalised Group Stepcycles"
ORIG_GROUP_SHEET_NAME = "Original Group Stepcycles"
X_STAND_GROUP_SHEET_NAME = "X-Standardised Group Stepcycles"
AVG_GROUP_SHEET_NAME = "Average Group Stepcycles"
STD_GROUP_SHEET_NAME = "Standard Deviation Group Stepcycles"
G_AVG_GROUP_SHEET_NAME = "Grand Average Group Stepcycles"
G_STD_GROUP_SHEET_NAME = "Grand Standard Deviation Group Stepcycles"

# SPLIT STRING (for _dlc first-level) & COLS OF DFs CREATED IN THIS SCRIPT
SPLIT_STRING = " - "
ID_COL = "ID"
SC_NUM_COL = "SC Number"
GROUP_COL = "Group"
N_COL = "N"  # for grand average dfs
SC_PERCENTAGE_COL = "SC Percentage"

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
STATS_PLOT_LEGEND_SIZE = 6
STATS_PLOTS_SUPLABEL_SIZE = 12
BOX_COLOR = "#fe420f"  # significance boxes - col = orangered
BOX_ALPHA = 0.1
STD_ALPHA = 0.2  # std boxes around means
STD_LW = 0

# PLOT GUI COLORS
FG_COLOR = "#5a7d9a"  # steel blue
HOVER_COLOR = "#8ab8fe"  # carolina blue

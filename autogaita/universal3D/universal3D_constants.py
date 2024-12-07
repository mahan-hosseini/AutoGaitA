LEGS = ["left", "right"]
LEGS_COLFORMAT = [", left ", ", right "]
OUTPUTS = LEGS + ["both"]
ISSUES_TXT_FILENAME = "Issues.txt"  # filename to which we write issues-info
CONFIG_JSON_FILENAME = "config.json"  # filename to which we write cfg-infos
# sc extraction
SCXLS_SUBJCOLS = [
    "Participant",
    "participant",
    "Animal",
    "animal",
    "Subject",
    "subject",
    "ID",
    "id",
]  # SC XLS info
SCXLS_LEGCOLS = ["Leg", "leg", "Legs", "legs", "Side", "side"]
SCXLS_RUNCOLS = ["Run", "run", "Runs", "runs", "Trial", "trial", "Trials", "trials"]
SCXLS_SCCOLS = ["SC Number", "SC number", "sc number", "SC Num", "sc num", "SC num"]
SWINGSTART_COL = "Swing (ti)"
STANCEEND_COL = "Stance (te)"
# simulate walking direction being left to right
SEARCH_WIN_TURN_TIME = 500  # 5 seconds
# export results as xlsx
ORIGINAL_XLS_FILENAME = " - Original Stepcycles"  # filenames of sheet exports
NORMALISED_XLS_FILENAME = " - Normalised Stepcycles"
AVERAGE_XLS_FILENAME = " - Average Stepcycle"
STD_XLS_FILENAME = " - Standard Devs. Stepcycle"
SEPARATOR_IDX = 1  # idx of dfs whenever we have separator rows
DF_TIME_COL = "Time"
DF_LEG_COL = "Leg"
SC_PERCENTAGE_COL = "SC Percentage"
EXCLUDED_COLS_IN_AV_STD_DFS = [DF_TIME_COL, DF_LEG_COL]
REORDER_COLS_IN_STEP_NORMDATA = [DF_TIME_COL, DF_LEG_COL]
# plot stuff
SC_LAT_LEGEND_FONTSIZE = 6
ANGLE_PLOTS_YLIMITS = [80, 190]
STICK_LINEWIDTH = 0.5
# Plot GUI colors
FG_COLOR = "#c0737a"  # dusty rose
HOVER_COLOR = "#b5485d"  # dark rose

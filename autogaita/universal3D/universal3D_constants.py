from autogaita.resources.constants import TIME_COL

# LEG stuff
LEGS = ["left", "right"]
LEGS_COLFORMAT = [", left ", ", right "]
OUTPUTS = LEGS + ["both"]
# sheet name of the combined ("both") sheet in the Average & Std XLS files
# => NOT plain "both" (as in the Original/Normalised files, which concatenate steps) because
#    here body-side columns show each side during its OWN (active) step cycle, while central/
#    axial columns are pooled across both legs' steps - see create_both_average_and_std_sheets
BOTH_ACTIVE_SHEET_NAME = "both (stepping side,pooled mid)"
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
Y_STANDARDISED_XLS_FILENAME = " - Y-Standardised Stepcycles"
NORMALISED_XLS_FILENAME = " - Normalised Stepcycles"
AVERAGE_XLS_FILENAME = " - Average Stepcycle"
STD_XLS_FILENAME = " - Standard Devs. Stepcycle"
SEPARATOR_IDX = 1  # idx of dfs whenever we have separator rows
LEG_COL = "Leg"
EXCLUDED_COLS_IN_AV_STD_DFS = [TIME_COL, LEG_COL]
REORDER_COLS_IN_STEP_NORMDATA = [TIME_COL, LEG_COL]
# plot stuff
SC_LAT_LEGEND_FONTSIZE = 6
ANGLE_PLOTS_YLIMITS = [80, 190]
STICK_LINEWIDTH = 0.5
# Plot GUI colors
FG_COLOR = "#c0737a"  # dusty rose
HOVER_COLOR = "#b5485d"  # dark rose

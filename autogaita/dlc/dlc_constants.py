# Configuration file for DLC-related global constants

# 1 - preparation
DIRECTION_DLC_THRESHOLD = 0.95  # DLC confidence used for direction-detection
TIME_COL = "Time"
ISSUES_TXT_FILENAME = "Issues.txt"
CONFIG_JSON_FILENAME = "config.json"  # filename to which we write cfg-infos

# 2 - sc extraction
SCXLS_MOUSECOLS = [
    "Mouse",
    "mouse",
    "Fly",
    "fly",
    "Animal",
    "animal",
    "Subject",
    "subject",
    "ID",
    "id",
]  # SC XLS info
SCXLS_RUNCOLS = ["Run", "run", "Runs", "runs", "Trial", "trial", "Trials", "trials"]
SCXLS_SCCOLS = ["SC Number", "SC number", "sc number", "SC Num", "sc num", "SC num"]
SWINGSTART_COL = "Swing (ti)"
STANCEEND_COL = "Stance (te)"

# 3 - analysis
ORIGINAL_XLS_FILENAME = " - Original Stepcycles"  # filenames of sheet exports
NORMALISED_XLS_FILENAME = " - Normalised Stepcycles"
AVERAGE_XLS_FILENAME = " - Average Stepcycle"
STD_XLS_FILENAME = " - Standard Devs. Stepcycle"
X_STANDARDISED_XLS_FILENAME = " - X-Standardised Stepcycles"

# 4 - plots
SC_LAT_LEGEND_FONTSIZE = 8
FG_COLOR = "#789b73"  # grey green
HOVER_COLOR = "#287c37"  # darkish green

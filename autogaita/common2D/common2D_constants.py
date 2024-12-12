# Configuration file for DLC/SLEAP-related global constants

# 1 - preparation
DIRECTION_DLC_THRESHOLD = 0.95  # (dlc) confidence used for direction-detection
FILE_ID_STRING_ADDITIONS = ["", "-", "_"]  # (dlc) postrun/postnum string additions

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

from autogaita import gui

DLC_FG_COLOR = "#789b73"  # grey green
DLC_HOVER_COLOR = "#287c37"  # darkish green
SLEAP_FG_COLOR = "#8f8ce7"  # perrywinkle
SLEAP_HOVER_COLOR = "#665fd1"  # dark periwinkle
UNIVERSAL3D_FG_COLOR = "#c0737a"  # dusty rose
UNIVERSAL3D_HOVER_COLOR = "#b5485d"  # dark rose
GROUP_FG_COLOR = "#5a7d9a"  # steel blue
GROUP_HOVER_COLOR = "#016795"  # peacock blue
HEADER_FONT_NAME = "Calibri Bold"
HEADER_FONT_SIZE = 30
HEADER_TXT_COLOR = "#ffffff"  # white
MAIN_HEADER_FONT_SIZE = 35
TEXT_FONT_NAME = "Calibri"
TEXT_FONT_SIZE = 20
ADV_CFG_TEXT_FONT_SIZE = TEXT_FONT_SIZE - 4
CLOSE_COLOR = "#840000"  # dark red
CLOSE_HOVER_COLOR = "#650021"  # maroon

# For how the look like refer to https://r02b.github.io/seaborn_palettes/
COLOR_PALETTES_LIST = [
    "Set1",
    "Set2",
    "Set3",
    "Dark2",
    "Paired",
    "Accent",  # qualitative palettes
    "hls",
    "husl",  # circular palettes
    "rocket",
    "mako",
    "flare",
    "crest",
    "viridis",
    "plasma",
    "inferno",
    "magma",
    "cividis",  # Perceptually uniform palettes
    "rocket_r",
    "mako_r",
    "flare_r",
    "crest_r",
    "viridis_r",
    "plasma_r",
    "inferno_r",
    "magma_r",
    "cividis_r",  # uniform palettes in reversed order
]
WINDOWS_TASKBAR_MAXHEIGHT = 72


# To get the path of the autogaita gui folder I use __file__
# which returns the path of the autogaita gui module imported above.
# Removing the 11 letter long "__init__.py" return the folder path
autogaita_utils_path = gui.__file__
AUTOGAITA_FOLDER_PATH = autogaita_utils_path[:-11]


def get_widget_cfg_dict():
    """Return a copy of the widget_cfg dictionary for usage outside of this module
    (prevents changes to the original dictionary)
    """
    return {
        "HEADER_FONT_NAME": HEADER_FONT_NAME,
        "HEADER_FONT_SIZE": HEADER_FONT_SIZE,
        "HEADER_TXT_COLOR": HEADER_TXT_COLOR,
        "MAIN_HEADER_FONT_SIZE": MAIN_HEADER_FONT_SIZE,
        "TEXT_FONT_NAME": TEXT_FONT_NAME,
        "TEXT_FONT_SIZE": TEXT_FONT_SIZE,
        "ADV_CFG_TEXT_FONT_SIZE": ADV_CFG_TEXT_FONT_SIZE,
        "CLOSE_COLOR": CLOSE_COLOR,
        "CLOSE_HOVER_COLOR": CLOSE_HOVER_COLOR,
        "COLOR_PALETTES_LIST": COLOR_PALETTES_LIST,
        "AUTOGAITA_FOLDER_PATH": AUTOGAITA_FOLDER_PATH,
    }

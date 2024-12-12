import platform
from importlib import resources


# ...............................  general gui stuff  ..................................
def configure_the_icon(root):
    """Configure the icon - in macos it changes the dock icon, in windows it changes
    all windows titlebar icons (taskbar cannot be changed without converting to exe)
    """
    if platform.system().startswith("Darwin"):
        try:
            from Cocoa import NSApplication, NSImage
        except ImportError:
            print("Unable to import pyobjc modules")
        else:
            with resources.path("autogaita.resources", "icon.icns") as icon_path:
                ns_application = NSApplication.sharedApplication()
                logo_ns_image = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
                ns_application.setApplicationIconImage_(logo_ns_image)
    elif platform.system().startswith("win"):
        with resources.path("autogaita.resources", "icon.ico") as icon_path:
            root.iconbitmap(str(icon_path))


def fix_window_after_its_creation(window):
    """Perform some quality of life things after creating a window (root or Toplevel)"""
    window.attributes("-topmost", True)
    window.focus_set()
    window.after(100, lambda: window.attributes("-topmost", False))  # 100 ms


def maximise_widgets(window):
    """Maximises all widgets to look good in fullscreen"""
    # fix the grid to fill the window
    num_rows = window.grid_size()[1]  # maximise rows
    for r in range(num_rows):
        window.grid_rowconfigure(r, weight=1)
    num_cols = window.grid_size()[0]  # maximise cols
    for c in range(num_cols):
        window.grid_columnconfigure(c, weight=1)


# ..............................  change widget states  ................................
def change_ratio_entry_state(cfg, ratio_entry):
    """Change the state of ratio entry widget based on whether user wants
    to convert pixels to mm or not.
    """
    if cfg["convert_to_mm"].get() is True:
        ratio_entry.configure(state="normal")
    elif cfg["convert_to_mm"].get() is False:
        ratio_entry.configure(state="disabled")


def change_y_standardisation_joint_entry_state(cfg, y_standardisation_joint_entry):
    if cfg["standardise_y_to_a_joint"].get() is True:
        y_standardisation_joint_entry.configure(state="normal")
    elif cfg["standardise_y_to_a_joint"].get() is False:
        y_standardisation_joint_entry.configure(state="disabled")


def change_x_standardisation_box_state(cfg, standardise_x_coordinates_box):
    if cfg["analyse_average_x"].get() is True:
        standardise_x_coordinates_box.configure(state="normal")
    elif cfg["analyse_average_x"].get() is False:
        standardise_x_coordinates_box.configure(state="disabled")


def change_x_standardisation_joint_entry_state(cfg, x_standardisation_joint_entry):
    if cfg["standardise_x_coordinates"].get() is True:
        x_standardisation_joint_entry.configure(state="normal")
    elif cfg["standardise_x_coordinates"].get() is False:
        x_standardisation_joint_entry.configure(state="disabled")


def change_ID_entry_state(cfg, ID_entry):
    """Change the state of ID entry widget based on whether user wants to only analyse
    a single dataset.
    """
    if cfg["analyse_singlerun"].get() is True:
        ID_entry.configure(state="normal")
    elif cfg["analyse_singlerun"].get() is False:
        ID_entry.configure(state="disabled")


def change_postname_entry_state(results, postname_entry):
    """Change the state of ID entry widget based on whether user wants to only analyse
    a single dataset.
    """
    if results["postname_flag"].get() is True:
        postname_entry.configure(state="normal")
    elif results["postname_flag"].get() is False:
        postname_entry.configure(state="disabled")

from autogaita.gui.common2D_main_gui import run_common2D_gui


def run_sleap_gui():
    """Helper function to call common2D_main_gui for SLEAP analysis"""
    # NOTE
    # ----
    # This is just so that we can call autogaita.sleap_gui() as before refactoring dlc/
    # sleap GUIs codes into common2D_main_gui
    run_common2D_gui("SLEAP")


# %% what happens if we hit run
if __name__ == "__main__":
    run_sleap_gui()

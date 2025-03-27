from autogaita.gui.common2D_main_gui import run_common2D_gui


def run_dlc_gui():
    """Helper function to call common2D_main_gui for DLC analysis"""
    # NOTE
    # ----
    # This is just so that we can call autogaita.dlc_gui() as before refactoring dlc/
    # sleap GUIs
    run_common2D_gui("DLC")


# %% what happens if we hit run
if __name__ == "__main__":
    run_dlc_gui()

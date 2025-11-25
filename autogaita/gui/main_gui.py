# %% imports
import autogaita
import autogaita.gui.gaita_widgets as gaita_widgets
import autogaita.gui.gui_utils as gui_utils
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from importlib import resources

# %% global constants
from autogaita.gui.gui_constants import (
    DLC_FG_COLOR,
    DLC_HOVER_COLOR,
    SLEAP_FG_COLOR,
    SLEAP_HOVER_COLOR,
    UNIVERSAL3D_FG_COLOR,
    UNIVERSAL3D_HOVER_COLOR,
    GROUP_FG_COLOR,
    GROUP_HOVER_COLOR,
    get_widget_cfg_dict,  # function!
)

WIDGET_CFG = get_widget_cfg_dict()


# %%...............................  MAIN PROGRAM  .....................................


def run_gui():
    # ..........................  root window initialisation ...........................
    # CustomTkinter vars
    ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
    ctk.set_default_color_theme("green")  # Themes: blue , dark-blue, green
    # root
    # => using ghost root because the image stuff breaks if your window is a CTk and not
    #    Toplevel, see https://stackoverflow.com/questions/20251161
    #                  /tkinter-tclerror-image-pyimage3-doesnt-exist
    ghost_root = ctk.CTk()
    ghost_root.withdraw()
    root = ctk.CTkToplevel()
    root.attributes("-topmost", True)
    root.focus_set()
    root.after_idle(root.attributes, "-topmost", False)
    # make it so that window is central & width/heigth of it = 1/2 of screen's
    ws = root.winfo_screenwidth()  # width of the screen
    hs = root.winfo_screenheight()  # height of the screen
    w = min(ws / 4, 800) # width for the Tk root
    h = min(hs / 2, 800) # height for the Tk root
    # calculate x and y coordinates for the Tk root window
    x = (ws / 2) - (w / 2)
    y = (hs / 2) - (h / 1.5)
    root_dimensions = (w, h, x, y)
    # set the dimensions of the screen and where it is placed
    root.geometry("%dx%d+%d+%d" % root_dimensions)
    root.title("AutoGaitA")
    gui_utils.configure_the_icon(root)
    # Set minimum and maximum sizes for the window (if user tries to resize manually)
    # => Prevents users from resizing the window because we decided against dynamically
    #    resizing logo image because it was really annoying (and slowed down stuff)
    # => And I kinda like that this GUI is (on all systems & displays) 1/4 screenwidth
    #    & 1/2 screenheight
    root.minsize(int(w), int(h))
    root.maxsize(int(w), int(h))

    # ...................................  widgets  ....................................
    # 1 - The Logo
    # => load the original logo & resize it using ANTIALIASING (LANCZOS) of PIL
    # => create an initial photo image that tkinter can use & grid it
    # ...............  PACKAGE WAY OF LOADING LOGO  ...............
    with resources.path("autogaita.resources", "logo.png") as image_path:
        original_image = Image.open(image_path)
    # # ...............  LOCAL WAY OF LOADING LOGO  ...............
    # image_path = "logo.png"
    # original_image = Image.open(image_path)
    resized_image = original_image.resize(
        (int(w), int(original_image.height * (w / original_image.width))), Image.LANCZOS
    )
    photo = ImageTk.PhotoImage(resized_image)
    image_label = tk.Label(root, image=photo)
    image_label.grid(row=0, column=0, sticky="nsew")
    # 2 - DLC Button
    WIDGET_CFG["FG_COLOR"] = DLC_FG_COLOR
    WIDGET_CFG["HOVER_COLOR"] = DLC_HOVER_COLOR
    dlc_button = gaita_widgets.header_button(
        root,
        "DeepLabCut",
        WIDGET_CFG,
    )
    dlc_button.configure(command=lambda: autogaita.run_dlc_gui())
    dlc_button.grid(row=1, column=0, sticky="nsew")
    # 3 - SLEAP Button
    WIDGET_CFG["FG_COLOR"] = SLEAP_FG_COLOR
    WIDGET_CFG["HOVER_COLOR"] = SLEAP_HOVER_COLOR
    sleap_button = gaita_widgets.header_button(
        root,
        "SLEAP",
        WIDGET_CFG,
    )
    sleap_button.configure(command=lambda: autogaita.run_sleap_gui())
    sleap_button.grid(row=2, column=0, sticky="nsew")
    # 4 - Universal 3D Button
    WIDGET_CFG["FG_COLOR"] = UNIVERSAL3D_FG_COLOR
    WIDGET_CFG["HOVER_COLOR"] = UNIVERSAL3D_HOVER_COLOR
    universal3D_button = gaita_widgets.header_button(
        root,
        "Universal 3D",
        WIDGET_CFG,
    )
    universal3D_button.configure(command=lambda: autogaita.run_universal3D_gui())
    universal3D_button.grid(row=3, column=0, sticky="nsew")
    # 5 - Group Button
    WIDGET_CFG["FG_COLOR"] = GROUP_FG_COLOR
    WIDGET_CFG["HOVER_COLOR"] = GROUP_HOVER_COLOR
    group_button = gaita_widgets.header_button(
        root,
        "Group",
        WIDGET_CFG,
    )
    group_button.configure(command=lambda: autogaita.run_group_gui())
    group_button.grid(row=4, column=0, sticky="nsew")
    # maximise buttons
    num_rows = root.grid_size()[1]  # maximise rows
    for r in range(1, num_rows):
        root.grid_rowconfigure(r, weight=1)

    # ...................................  mainloop  ...................................
    root.mainloop()


# %% what happens if we hit run
if __name__ == "__main__":
    run_gui()

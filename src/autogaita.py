# %% imports
from autogaita import autogaita_dlc_gui, autogaita_simi_gui, autogaita_group_gui
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from importlib import resources
import platform


# %% global constants
TXT_COLOR = "#ffffff"  # white
FONT_SIZE = 20
DLC_FG_COLOR = "#789b73"  # grey green
DLC_HOVER_COLOR = "#287c37"  # darkish green
SIMI_FG_COLOR = "#c0737a"  # dusty rose
SIMI_HOVER_COLOR = "#b5485d"  # dark rose
GROUP_FG_COLOR = "#5a7d9a"  # steel blue
GROUP_HOVER_COLOR = "#016795"  # peacock blue


# %%...............................  MAIN PROGRAM  .....................................


def gui():
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
    w = ws / 4  # width for the Tk root
    h = hs / 2  # height for the Tk root
    # calculate x and y coordinates for the Tk root window
    x = (ws / 2) - (w / 2)
    y = (hs / 2) - (h / 1.5)
    root_dimensions = (w, h, x, y)
    # set the dimensions of the screen and where it is placed
    root.geometry("%dx%d+%d+%d" % root_dimensions)
    root.title("AutoGaitA")
    configure_the_icon(root)
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
    with resources.path("autogaita", "autogaita_logo.png") as image_path:
        original_image = Image.open(image_path)
    # # ...............  LOCAL WAY OF LOADING LOGO  ...............
    # image_path = "autogaita_logo.png"
    # original_image = Image.open(image_path)
    resized_image = original_image.resize(
        (int(w), int(original_image.height * (w / original_image.width))), Image.LANCZOS
    )
    photo = ImageTk.PhotoImage(resized_image)
    image_label = tk.Label(root, image=photo)
    image_label.grid(row=0, column=0, sticky="nsew")
    # 2 - DLC Button
    dlc_button = ctk.CTkButton(
        root,
        text="DeepLabCut",
        fg_color=DLC_FG_COLOR,
        hover_color=DLC_HOVER_COLOR,
        text_color=TXT_COLOR,
        font=("Britannic Bold", FONT_SIZE),
        command=lambda: autogaita_dlc_gui.dlc_gui(),
    )
    dlc_button.grid(row=1, column=0, sticky="nsew")
    # 3 - Simi Button
    simi_button = ctk.CTkButton(
        root,
        text="Simi Motion",
        fg_color=SIMI_FG_COLOR,
        hover_color=SIMI_HOVER_COLOR,
        text_color=TXT_COLOR,
        font=("Britannic Bold", FONT_SIZE),
        command=lambda: autogaita_simi_gui.simi_gui(),
    )
    simi_button.grid(row=2, column=0, sticky="nsew")
    # 4 - Group Button
    group_button = ctk.CTkButton(
        root,
        text="Group",
        fg_color=GROUP_FG_COLOR,
        hover_color=GROUP_HOVER_COLOR,
        text_color=TXT_COLOR,
        font=("Britannic Bold", FONT_SIZE),
        command=lambda: autogaita_group_gui.group_gui(),
    )
    group_button.grid(row=3, column=0, sticky="nsew")
    # maximise buttons
    num_rows = root.grid_size()[1]  # maximise rows
    for r in range(1, num_rows):
        root.grid_rowconfigure(r, weight=1)

    # ...................................  mainloop  ...................................
    root.mainloop()


# %%.............................  HELPER FUNCTIONS  ...................................
def configure_the_icon(root):
    """Configure the icon - in macos it changes the dock icon, in windows it changes
    all windows titlebar icons (taskbar cannot be changed without converting to exe)
    """
    if platform.system().startswith("Darwin"):
        try:
            from Cocoa import NSApplication, NSImage
        except ImportError:
            print('Unable to import pyobjc modules')
        else:
            with resources.path("autogaita", "autogaita_icon.icns") as icon_path:
                ns_application = NSApplication.sharedApplication()
                logo_ns_image = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
                ns_application.setApplicationIconImage_(logo_ns_image)
    elif platform.system().startswith("win"):
        with resources.path("autogaita", "autogaita_icon.ico") as icon_path:
            root.iconbitmap(str(icon_path))


# %% what happens if we hit run
if __name__ == "__main__":
    gui()

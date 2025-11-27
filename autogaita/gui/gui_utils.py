import platform
from importlib import resources
from PIL import Image
import tkinter as tk
from tkinter.font import Font, nametofont
from customtkinter import CTkImage


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


def change_widget_state_based_on_checkbox(cfg, key_to_check, widget_to_change):
    """Change the state of a widget based on state of another widget."""
    if cfg[key_to_check].get() is True:
        widget_to_change.configure(state="normal")
    elif cfg[key_to_check].get() is False:
        widget_to_change.configure(state="disabled")


def create_folder_icon():
    folder_icon = Image.open(
        resources.files("autogaita.resources").joinpath("folder.png")
    )
    return CTkImage(light_image=folder_icon, dark_image=folder_icon, size=(20, 20))


# ....................  change fontsize based on entry selection  ......................


class TextHighlighter:
    def __init__(self, analysis, ctk_textbox, widget_map, tag_name="highlight_zoom"):
        # note we need to hack a bit using the underlying tk.Text widget for font_tag
        self.ctk_textbox = ctk_textbox  # ctk widget
        self.tk_text_widget = ctk_textbox._textbox  # underlying tk.Text widget
        self.widget_map = widget_map
        self.tag_name = tag_name
        self._setup_font_tag(analysis)

        for entry_widget in self.widget_map.keys():
            # Note: CustomTkinter Entry widgets also use an internal entry,
            # but bindings on the main CTk object usually propagate.
            # If you use CTkEntry, binding directly to it works fine.
            entry_widget.bind("<FocusIn>", self._on_focus_in, add="+")
            entry_widget.bind("<FocusOut>", self._on_focus_out, add="+")

    def _setup_font_tag(self, analysis):
        default_font = nametofont("TkDefaultFont")
        large_font = default_font.copy()
        if analysis == "single":
            font_size = 25
        else:
            font_size = 30
        large_font.configure(size=font_size, weight="bold")
        self.tk_text_widget.tag_config(self.tag_name, font=large_font)

    def _process_event(self, event, mode):
        target_data = self.widget_map.get(event.widget)

        # Handle cases where the event might come from the internal entry of a CTkEntry
        # (If you bind to a CTkEntry, event.widget is often the internal tkinter Entry)
        if not target_data:
            # Try finding the parent if the direct widget isn't in our map
            # This helps if event.widget is the internal entry but we mapped the
            # CTkEntry
            for mapped_widget in self.widget_map:
                if (
                    hasattr(mapped_widget, "_entry")
                    and mapped_widget._entry == event.widget
                ):
                    target_data = self.widget_map[mapped_widget]
                    break

        if not target_data:
            return

        words_to_highlight = (
            [target_data] if isinstance(target_data, str) else target_data
        )

        for word in words_to_highlight:
            self._apply_highlight(word, mode)

    def _on_focus_in(self, event):
        self._process_event(event, "add")

    def _on_focus_out(self, event):
        self._process_event(event, "remove")

    def _apply_highlight(self, word, action):
        # Search using the underlying widget
        start_index = self.tk_text_widget.search(word, "1.0", stopindex=tk.END)
        if not start_index:
            return

        length = len(word)
        end_index = f"{start_index}+{length}c"

        if action == "add":
            self.tk_text_widget.tag_add(self.tag_name, start_index, end_index)
        else:
            self.tk_text_widget.tag_remove(self.tag_name, start_index, end_index)

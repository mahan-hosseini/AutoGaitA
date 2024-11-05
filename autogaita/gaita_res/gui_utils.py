import platform
from importlib import resources


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
            with resources.path("autogaita.gaita_res", "icon.icns") as icon_path:
                ns_application = NSApplication.sharedApplication()
                logo_ns_image = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
                ns_application.setApplicationIconImage_(logo_ns_image)
    elif platform.system().startswith("win"):
        with resources.path("autogaita.gaita_res", "icon.ico") as icon_path:
            root.iconbitmap(str(icon_path))

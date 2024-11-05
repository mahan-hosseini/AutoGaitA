# main gui
from .autogaita import gui  # autogaita.gui()

# 3 sub-guis
from .autogaita_dlc_gui import dlc_gui  # autogaita.dlc_gui()
from .autogaita_universal3D_gui import universal3D_gui  # autogaita.universal3D_gui()
from .autogaita_group_gui import group_gui  # autogaita.group_gui()

# 3 main functions
from .autogaita_dlc import dlc  # autogaita.dlc(info, folderinfo, cfg)
from .autogaita_universal3D import (
    universal3D,
)  # autogaita.universal3D(info, folderinfo, cfg)
from .autogaita_group import group  # autogaita.group(folderinfo, cfg)

# 6 batchrun functions - call via e.g. autogaita.dlc_singlerun()
from .batchrun_scripts.autogaita_dlc_singlerun import dlc_singlerun
from .batchrun_scripts.autogaita_dlc_multirun import dlc_multirun
from .batchrun_scripts.autogaita_universal3D_singlerun import universal3D_singlerun
from .batchrun_scripts.autogaita_universal3D_multirun import universal3D_multirun
from .batchrun_scripts.autogaita_group_dlcrun import group_dlcrun
from .batchrun_scripts.autogaita_group_universal3Drun import group_universal3Drun

# main gui
from .gui.main_gui import run_gui  # autogaita.run_gui()

# 4 sub-guis
from .gui.dlc_gui import run_dlc_gui  # autogaita.run_dlc_gui()
from .gui.sleap_gui import run_sleap_gui  # autogaita.run_sleap_gui()
from .gui.universal3D_gui import (
    run_universal3D_gui,
)  # autogaita.run_universal3D_gui()
from .gui.group_gui import run_group_gui  # autogaita.run_group_gui()

# 4 main functions
from .dlc.dlc_main import dlc  # autogaita.dlc(info, folderinfo, cfg)
from .sleap.sleap_main import sleap  # autogaita.sleap(info, folderinfo, cfg)
from .universal3D.universal3D_main import (
    universal3D,
)  # autogaita.universal3D(info, folderinfo, cfg)
from .group.group_main import group  # autogaita.group(folderinfo, cfg)

# 7 batchrun functions - call via e.g. autogaita.dlc_singlerun()
from .batchrun_scripts.dlc_singlerun import dlc_singlerun
from .batchrun_scripts.dlc_multirun import dlc_multirun
from .batchrun_scripts.sleap_singlerun import sleap_singlerun
from .batchrun_scripts.universal3D_multirun import universal3D_multirun
from .batchrun_scripts.universal3D_singlerun import universal3D_singlerun
from .batchrun_scripts.group_dlcrun import group_dlcrun
from .batchrun_scripts.group_universal3Drun import group_universal3Drun

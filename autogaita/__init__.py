# main gui
from .autogaita import gui  # autogaita.gui()

# 3 sub-guis
from .autogaita_dlc_gui import dlc_gui  # autogaita.dlc_gui()
from .autogaita_simi_gui import simi_gui  # autogaita.simi_gui()
from .autogaita_group_gui import group_gui  # autogaita.group_gui()

# 3 main functions
from .autogaita_dlc import dlc  # autogaita.dlc(info, folderinfo, cfg)
from .autogaita_simi import simi  # autogaita.simi(info, folderinfo, cfg)
from .autogaita_group import group  # autogaita.group(folderinfo, cfg)

# 6 batchrun functions - call via e.g. autogaita.dlc_singlerun()
from .batchrun_scripts.autogaita_dlc_singlerun import dlc_singlerun
from .batchrun_scripts.autogaita_dlc_multirun import dlc_multirun
from .batchrun_scripts.autogaita_simi_singlerun import simi_singlerun
from .batchrun_scripts.autogaita_simi_multirun import simi_multirun
from .batchrun_scripts.autogaita_group_dlcrun import group_dlcrun
from .batchrun_scripts.autogaita_group_simirun import group_simirun

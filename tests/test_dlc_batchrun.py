import autogaita.batchrun_scripts
import os
from pathlib import Path

# ............................  DLC BATCHRUN TEST STRUCTURE  ...........................
# 1. Run dlc_singlerun()
# 2. Check that Average Stepcycle.xlsx exists (means that it ran through)
# 3. Do 1. & 2. for dlc_multirun()


# ..............................  PREPARE - THREE FIXTURES   ...........................

dlc_test_file = "tests/test_data/dlc_data/test_data/Results/Average Stepcycle.xlsx"

if os.getenv("GITHUB_ACTIONS"):
    autogaita.dlc_singlerun()
    this_file_only_exists_if_it_ran_correctly = Path(dlc_test_file)
    assert this_file_only_exists_if_it_ran_correctly.is_file()

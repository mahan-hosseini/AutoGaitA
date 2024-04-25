from autogaita import autogaita_group
import pandas as pd
import pandas.testing as pdt
import filecmp
import os
import shutil
import pdb


def test_group_approval():
    """
    Approval Test of AutoGaitA Group
    --------------------------------
    1. Run autogaita.group for example group (3 beams) data (with the cfg used there), store results @ TEST_PATH
    2. Load the "Grand Average Stepcycles".xlsx & "Grand Standard Devs. Stepcycle.xlsx" files from the repo (TRUE PATH) - test for equivalence with TEST PATH
    3. Then test if PCA XLS file is equal
    4. Finally test if Stats.txt files are equal

    A Note
    ------
    We don't test the cluster extent test in an automated way.
    We have results of simulations that ran for over a week in our preprint.
    If the cluster extent test should change for some reason - re-run those simulations.
    """

    # .............................  0) PREPARATION  ...................................
    # for testing - reset any previous test
    TEST_PATH = "tests/test_data/group_data/"
    TRUE_PATH = "example data/group/"
    if os.path.exists(TEST_PATH):
        shutil.rmtree(TEST_PATH)
        os.mkdir(TEST_PATH)

    # cfg
    cfg = {}
    cfg["do_permtest"] = False
    cfg["do_anova"] = True
    cfg["permutation_number"] = 100
    cfg["number_of_PCs"] = 3
    cfg["save_3D_PCA_video"] = False
    cfg["stats_threshold"] = 0.05
    cfg["plot_SE"] = False
    cfg["which_leg"] = "left"
    cfg["anova_design"] = "RM ANOVA"
    cfg["permutation_number"] = 100
    # NOTE - PCA & stats vars MUST be input in this order
    # (otherwise PCA.Info & Stats.txt wont be equivalent)
    # => it's this order because it resulted from group_gui input (and thus corresponds to the checkbox-order of the features window)
    cfg["PCA_variables"] = [
        "Knee y",
        "Ankle y",
        "Hind paw tao y",
        "Ankle Angle",
        "Knee Angle",
        "Hip Angle",
    ]
    cfg["stats_variables"] = cfg["PCA_variables"]

    # folderinfo
    folderinfo = {}
    folderinfo["group_names"] = ["5 mm", "12 mm", "25 mm"]
    folderinfo["group_dirs"] = [
        "example data/5mm/Results/",
        "example data/12mm/Results/",
        "example data/25mm/Results/",
    ]
    folderinfo["results_dir"] = TEST_PATH

    # ...........................  1) RUN GROUP GAITA  .................................
    autogaita_group.group(folderinfo, cfg)

    # ......................  2) TEST EQUIVALENCE OF GROUP DFs  ........................
    # load true dfs from xlsx files
    true_av_df = pd.read_excel(
        os.path.join(TRUE_PATH, "25 mm - Grand Average Group Stepcycles.xlsx")
    )
    true_std_df = pd.read_excel(
        os.path.join(
            TRUE_PATH, "25 mm - Grand Standard Deviation Group Stepcycles.xlsx"
        )
    )
    test_av_df = pd.read_excel(
        os.path.join(TEST_PATH, "25 mm - Grand Average Group Stepcycles.xlsx")
    )
    test_std_df = pd.read_excel(
        os.path.join(
            TEST_PATH,
            "25 mm - Grand Standard Deviation Group Stepcycles.xlsx",
        )
    )
    # finally assert equivalence of df-pairs
    pdt.assert_frame_equal(test_av_df, true_av_df)
    pdt.assert_frame_equal(test_std_df, true_std_df)

    # .......................  3) TEST EQUIVALENCE OF PCA DF  ..........................
    true_pca_df = pd.read_excel(os.path.join(TRUE_PATH, "PCA Info.xlsx"))
    test_pca_df = pd.read_excel(os.path.join(TEST_PATH, "PCA Info.xlsx"))
    pdt.assert_frame_equal(test_pca_df, true_pca_df)

    # ......................  4) TEST EQUIVALENCE OF STATS.TXT  ........................
    shallow = False  # if True compares only the metadata, not the contents!
    match, mismatch, errors = filecmp.cmpfiles(
        TRUE_PATH, TEST_PATH, ["Stats.txt"], shallow
    )
    assert match == ["Stats.txt"]

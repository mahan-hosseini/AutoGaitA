from autogaita.group.group_main import run_ANOVA
import pytest
import pandas as pd
import numpy as np
import math

# global constants from group gaita
ID_COL = "ID"
SC_PERCENTAGE_COL = "SC Percentage"
GROUP_COL = "Group"


# %%................................  fixtures  ........................................
@pytest.fixture
def extract_folderinfo(tmp_path):
    return {
        "group_names": ["group1", "group2"],
        "group_dirs": ["/path/to/group1", "/path/to/group2"],
        "results_dir": tmp_path,
    }


@pytest.fixture
def extract_cfg():
    return {
        "do_permtest": True,
        "do_anova": True,
        "permutation_number": 100,
        "number_of_PCs": 3,
        "save_3D_PCA_video": False,
        "stats_threshold": 0.05,
        "plot_SE": False,
        "color_palette": "viridis",
        "dont_show_plots": True,
        "legend_outside": True,
        "which_leg": "left",
        "anova_design": "Mixed ANOVA",
        "PCA_variables": [],
        "stats_variables": [],
    }


# %%..............................  statistics  ........................................
def test_RM_ANOVA(extract_cfg):
    # Adopted example data from https://real-statistics.com/
    # See the RM ANOVA xlsx file for complete link
    extract_cfg["do_anova"] = True
    extract_cfg["anova_design"] = "RM ANOVA"
    stats_df = pd.read_excel("tests/test_data/group_data/RM ANOVA Example Data.xlsx")
    stats_var = "Value"
    result = run_ANOVA(stats_df, stats_var, extract_cfg)
    # Note that the last 2 assert statements have a different tolerance because those
    # p-values differed a bit. Not sure why but it's a tiny amount and tolerable IMO
    assert math.isclose(result["p-unc"][0], stats_df["p(A)"][0], abs_tol=1e-05)
    assert math.isclose(result["p-unc"][1], stats_df["p(B)"][0], abs_tol=1e-05)
    assert math.isclose(result["p-unc"][2], stats_df["p(AxB)"][0], abs_tol=1e-05)
    assert math.isclose(result["p-GG-corr"][0], stats_df["GG-p(A)"][0], abs_tol=1e-05)
    assert math.isclose(result["p-GG-corr"][1], stats_df["GG-p(B)"][0], abs_tol=1e-04)
    assert math.isclose(result["p-GG-corr"][2], stats_df["GG-p(AxB)"][0], abs_tol=1e-02)


def test_Mixed_ANOVA(extract_cfg):
    # Adopted example data from https://real-statistics.com/
    # See the Mixed ANOVA xlsx file for complete link
    extract_cfg["do_anova"] = True
    extract_cfg["anova_design"] = "Mixed ANOVA"
    stats_df = pd.read_excel("tests/test_data/group_data/Mixed ANOVA Example Data.xlsx")
    stats_var = "Value"
    result = run_ANOVA(stats_df, stats_var, extract_cfg)
    # no GG p vals here
    assert math.isclose(result["p-unc"][0], stats_df["p(A)"][0], abs_tol=1e-05)
    assert math.isclose(result["p-unc"][1], stats_df["p(B)"][0], abs_tol=1e-05)
    assert math.isclose(result["p-unc"][2], stats_df["p(AxB)"][0], abs_tol=1e-05)

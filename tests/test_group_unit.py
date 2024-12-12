from autogaita.group.group_3_PCA import run_PCA, convert_PCA_bins_to_list
from autogaita.group.group_4_stats import run_ANOVA
import pytest
from sklearn import datasets
import pandas as pd
import numpy as np
import math


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
        "PCA_n_components": 3,
        "PCA_custom_scatter_PCs": "",
        "PCA_save_3D_video": False,  # True
        "PCA_bins": "",
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


# NOTE !!!
# => This test is outdated and wrong because it is for two within subject factors (for
#    example 3 separate behavioural tests and pre/post medication treatment or so -
#    done by each subject)
# => I will not delete this since I might want to re-use it if I should support such
#    designs
#
# def test_twoway_RM_ANOVA(extract_cfg):
#     # Adopted example data from https://real-statistics.com/
#     # See the RM ANOVA xlsx file for complete link
#     extract_cfg["do_anova"] = True
#     extract_cfg["anova_design"] = "RM ANOVA"
#     stats_df = pd.read_excel("tests/test_data/group_data/RM ANOVA Example Data.xlsx")
#     stats_var = "Value"
#     result = run_ANOVA(stats_df, stats_var, extract_cfg)
#     # Note that the last 2 assert statements have a different tolerance because those
#     # p-values differed a bit. Not sure why but it's a tiny amount and tolerable IMO
#     pytest.set_trace()
#     assert math.isclose(result["p-unc"][0], stats_df["p(A)"][0], abs_tol=1e-05)
#     assert math.isclose(result["p-unc"][1], stats_df["p(B)"][0], abs_tol=1e-05)
#     assert math.isclose(result["p-unc"][2], stats_df["p(AxB)"][0], abs_tol=1e-05)
#     assert math.isclose(result["p-GG-corr"][0], stats_df["GG-p(A)"][0], abs_tol=1e-05)
#     assert math.isclose(result["p-GG-corr"][1], stats_df["GG-p(B)"][0], abs_tol=1e-04)
#     assert math.isclose(result["p-GG-corr"][2], stats_df["GG-p(AxB)"][0], abs_tol=1e-02)


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


# %%..................................  PCA  ...........................................
def test_run_PCA(extract_cfg):
    # Replicate the example found in https://www.kdnuggets.com/2023/05/
    # principal-component-analysis-pca-scikitlearn.html using our PCA df and PCA_info
    # structure
    # fmt: off
    true_results_PCA_eigenvectors = [[0.1443294, -0.24518758, -0.00205106, -0.23932041,  0.14199204,  0.39466085, 0.4229343, -0.2985331, 0.31342949, -0.0886167,0.29671456,  0.37616741, 0.28675223],
    [-0.48365155, -0.22493093, -0.31606881,  0.0105905,  -0.299634,   -0.06503951
    , 0.00335981, -0.02877949, -0.03930172, -0.52999567,  0.27923515,  0.16449619,
    -0.36490283],
    [-0.20738262,  0.08901289,  0.6262239,   0.61208035,  0.13075693,  0.14617896,
    0.1506819,   0.17036816,  0.14945431, -0.13730621,  0.08522192,  0.16600459,
    -0.12674592]]
    true_results_PCA_explained_var = [0.36198848, 0.1920749 , 0.11123631]
    # fmt: on
    wine_data = datasets.load_wine(as_frame=True)
    wine_df = wine_data.data
    features = wine_df.columns
    PCA_df, PCA_info = run_PCA(wine_df, features, extract_cfg)
    for i in range(3):
        # absolute values are compared because the signs can be different w. eigenvecs
        assert np.allclose(
            np.absolute(PCA_info["eigenvectors"][i]),
            np.absolute(true_results_PCA_eigenvectors[i]),
            atol=1e-05,
        )
    assert np.allclose(
        PCA_info["explained_vars"], true_results_PCA_explained_var, atol=1e-05
    )


cases = (
    (
        "1-30,50,70-100",
        100,
        np.arange(1, 31).tolist() + [50] + np.arange(70, 101).tolist(),
    ),
    ("1-70", 25, [4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 68]),
    ("2, 10, 22, 44, 50, 79", 50, [2, 10, 22, 44, 50]),
    ("1-50,70-80", 10, [10, 20, 30, 40, 50, 70, 80]),
)  # fmt: skip
@pytest.mark.parametrize("PCA_bins, bin_num, expected_bins_list", cases)
def test_convert_PCA_bins_to_list(
    PCA_bins, bin_num, expected_bins_list, extract_folderinfo, extract_cfg
):
    extract_cfg["PCA_bins"] = PCA_bins
    extract_cfg["bin_num"] = bin_num
    updated_cfg = convert_PCA_bins_to_list(extract_folderinfo, extract_cfg)
    assert np.array_equal(updated_cfg["PCA_bins"], np.array(expected_bins_list))

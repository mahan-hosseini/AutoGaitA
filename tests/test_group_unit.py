from autogaita.group.group_main import (
    import_data,
    avg_and_std,
    create_stats_df,
    cluster_extent_test,
)
from autogaita.group.group_2_data_processing import (
    load_previous_runs_dataframes,
    check_PCA_and_stats_variables,
)
from autogaita.group.group_3_PCA import run_PCA, convert_PCA_bins_to_list
from autogaita.group.group_4_stats import run_ANOVA
import pytest
from sklearn import datasets
import pandas as pd
import pandas.testing as pdt
import numpy as np
import math


# %%................................  fixtures  ........................................
@pytest.fixture
def extract_folderinfo(tmp_path):
    return {
        "group_names": ["group1", "group2"],
        "group_dirs": ["/path/to/group1", "/path/to/group2"],
        "results_dir": tmp_path,
        "load_dir": "",
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


# %%............................  2. data processing  ..................................
def test_check_PCA_and_stats_variables(extract_folderinfo, extract_cfg):
    """Test this sanity check does not have the necessary columns"""
    group_names = ["5 mm", "12 mm", "25 mm"]
    extract_folderinfo["group_names"] = group_names
    extract_folderinfo["load_dir"] = "example data/group"
    # changing PCA/stats vars like this already performs a first test because the load
    # function only runs successfully, if the test_PCA_.. function does
    # => i.e. the features are present in the all 3 kinds of dfs
    extract_cfg["PCA_variables"] = ["Ankle Angle", "Knee Angle"]
    extract_cfg["stats_variables"] = ["Ankle Angle", "Knee Angle"]
    avg_dfs, _, _, extract_cfg = load_repos_group_data(extract_folderinfo, extract_cfg)
    # test correct failure
    # => code means: test that after removing the column our check correctly raises a
    #    ValueError
    avg_dfs[0].drop(columns=["Ankle Angle"], inplace=True)
    with pytest.raises(ValueError):
        check_PCA_and_stats_variables(
            avg_dfs[0], "5 mm", "Average", extract_folderinfo, extract_cfg
        )


def test_load_previous_runs_dataframes(extract_folderinfo, extract_cfg):
    """Testing if errors are raised correctly and if the loaded dfs are eqiuvalent to the ones import_data generates"""
    # 1: fails as wanted if group name wrong (df not found in load dir)
    extract_folderinfo["group_names"] = ["not 5 mm", "12 mm", "25 mm"]
    extract_folderinfo["load_dir"] = "example data/group"
    with pytest.raises(FileNotFoundError):
        avg_dfs, g_avg_dfs, g_std_dfs, extract_cfg = load_repos_group_data(
            extract_folderinfo, extract_cfg
        )
    # 2: avg_dfs equivalent to import_data's avg_dfs
    # "results_dir": tmp_path,
    # "load_dir": "",
    extract_folderinfo["group_names"] = ["5 mm", "12 mm", "25 mm"]
    extract_folderinfo["group_dirs"] = [
        "example data/5mm/Results/",
        "example data/12mm/Results/",
        "example data/25mm/Results/",
    ]
    avg_dfs, g_avg_dfs, g_std_dfs, extract_cfg = load_repos_group_data(
        extract_folderinfo, extract_cfg
    )
    # some prep required for import data & avg_and_std
    extract_cfg["sampling_rate"] = 100
    extract_cfg["bin_num"] = 25
    extract_cfg["save_to_xls"] = [True, True, True]
    extract_cfg["tracking_software"] = "DLC"
    extract_cfg["analyse_average_x"] = True
    i_dfs, _, extract_cfg = import_data(extract_folderinfo, extract_cfg)
    i_avg_dfs, _ = avg_and_std(i_dfs, extract_folderinfo, extract_cfg)
    pytest.set_trace()
    print(i_avg_dfs)
    print(avg_dfs)
    print(i_avg_dfs[0]["ID"])
    print(avg_dfs[0]["ID"])
    for g in range(3):  # dtype of ID is int and float - whatever
        pdt.assert_frame_equal(avg_dfs[g], i_avg_dfs[g], check_dtype=False)


# %%..............................  4. statistics  .....................................


def test_load_dfs_stats_df_perm_test_smoke(extract_folderinfo, extract_cfg):
    """Smoke test three functions:
    1. load_previous_runs-dataframes
    2. create_stats_df
    3. cluster_extent_test
    => Check if it all runs without errors on our repo's example data
    """
    # first, prepare approrpiately & overwrite the fixtures of this script as needed
    # 1) for load_previous_runs_dataframes (called by load repos group data)
    extract_folderinfo["group_names"] = ["5 mm", "12 mm", "25 mm"]
    extract_folderinfo["load_dir"] = "example data/group"
    avg_dfs, g_avg_dfs, g_std_dfs, extract_cfg = load_repos_group_data(
        extract_folderinfo, extract_cfg
    )
    # 2) for stats_df & the permutation test functions
    extract_cfg["sampling_rate"] = 100
    extract_cfg["do_permtest"] = True
    extract_cfg["dont_show_plots"] = True
    extract_cfg["tracking_software"] = "DLC"
    extract_cfg["group_color_dict"] = {"5 mm": "red", "12 mm": "blue", "25 mm": "green"}
    extract_folderinfo["contrasts"] = ["5 mm & 12 mm", "5 mm & 25 mm", "12 mm & 25 mm"]
    stats_df = create_stats_df(avg_dfs, extract_folderinfo, extract_cfg)
    plot_panel_instance = None
    cluster_extent_test(
        stats_df,
        g_avg_dfs,
        g_std_dfs,
        "Ankle Angle",
        extract_folderinfo,
        extract_cfg,
        plot_panel_instance,
    )


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


def load_repos_group_data(extract_folderinfo, extract_cfg):
    """Use load_previous_runs_dataframes to load example data from the repo"""
    extract_cfg["sampling_rate"] = 100
    extract_cfg["group_color_dict"] = {"5 mm": "red", "12 mm": "blue", "25 mm": "green"}
    extract_folderinfo["contrasts"] = ["5 mm & 12 mm", "5 mm & 25 mm", "12 mm & 25 mm"]
    avg_dfs, g_avg_dfs, g_std_dfs, extract_cfg = load_previous_runs_dataframes(
        extract_folderinfo, extract_cfg
    )
    return avg_dfs, g_avg_dfs, g_std_dfs, extract_cfg


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

# Contrast autogaita_dlc results using autogaita_group
from autogaita import autogaita_utils

def group_dlcrun():
    """Batch run group level analyses for results obtained with _dlc"""
    folderinfo = {}
    cfg = {}
    cfg["do_permtest"] = True
    cfg["do_anova"] = True
    cfg["permutation_number"] = 100
    cfg["number_of_PCs"] = 3
    cfg["save_3D_PCA_video"] = True
    cfg["stats_threshold"] = 0.05
    cfg["plot_SE"] = False
    cfg["which_leg"] = "left"

    # mouse anova cfg!
    cfg["anova_design"] = "RM ANOVA"
    cfg["permutation_number"] = 100
    cfg["PCA_variables"] = ["Hind paw tao y", "Ankle y", "Knee y", "Elbow Angle Velocity"]
    cfg["stats_variables"] = [
        # "Hind paw tao y",
        "Ankle y",
        # "Knee y",
        "Ankle Angle",
        # "Knee Angle",
        # "Hip Angle",
        "Elbow Angle"
    ]

    # 2 groups
    folderinfo["group_names"] = ["one", "two"]
    folderinfo["group_dirs"] = [
        "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/Testing/Group1/",
        "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/Testing/Group2/",
    ]

    # results dir
    folderinfo[
        "results_dir"
    # mouse
    ] = "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/Testing/GroupResults/"
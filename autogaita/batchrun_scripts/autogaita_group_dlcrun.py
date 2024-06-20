from autogaita import autogaita_group


def group_dlcrun():
    """
    Batchrun script to run AutoGaitA Group for Results obtained with AutoGaitA DLC.
    folderinfo & cfg dictionaries must be configured as explained in our documentation. See the "AutoGaitA without the GUI" section of our documentation for references to in-depth explanations to all dictionary keys (note that each key of dicts corresponds to some object in the AutoGaitA Group GUI)
    """
    # folderinfo
    # => Note that length of folderinfo's group_names & group_dirs lists determines how #    many groups are compared.
    # => Also note that indices must correspond (i.e., idx #    1's name will be used #    for dataset stored in group_dir's idx 1)
    folderinfo = {}
    folderinfo["group_names"] = ["one", "two"]
    folderinfo["group_dirs"] = [
        "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/Testing/Group 1/",
        "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/Testing/Group 2/",
    ]
    folderinfo["results_dir"] = (
        "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/Testing/GroupResults/"
    )
    # cfg
    cfg = {}
    cfg["do_permtest"] = True
    cfg["do_anova"] = True
    cfg["permutation_number"] = 100
    cfg["number_of_PCs"] = 3
    cfg["save_3D_PCA_video"] = False
    cfg["stats_threshold"] = 0.05
    cfg["plot_SE"] = False
    cfg["color_palette"] = "viridis"
    cfg["legend_outside"] = True
    cfg["which_leg"] = "left"
    cfg["anova_design"] = "Mixed ANOVA"
    cfg["permutation_number"] = 100
    cfg["PCA_variables"] = ["Hind paw tao y", "Ankle y", "Knee y"]
    cfg["stats_variables"] = [
        # "Hind paw tao y",
        "Ankle y",
        # "Knee y",
        "Ankle Angle",
        # "Knee Angle",
        # "Hip Angle",
        # "Elbow Angle"
    ]
    # run
    autogaita_group.group(folderinfo, cfg)


# %% what happens if we just hit run
if __name__ == "__main__":
    group_dlcrun()

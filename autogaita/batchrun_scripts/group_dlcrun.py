import autogaita


def group_dlcrun():
    """
    Batchrun script to run AutoGaitA Group for Results obtained with AutoGaitA DLC.
    folderinfo & cfg dictionaries must be configured as explained in our documentation. See the "AutoGaitA without the GUI" section of our documentation for references to in-depth explanations to all dictionary keys (note that each key of dicts corresponds to some object in the AutoGaitA Group GUI)
    """
    # folderinfo
    # => Note that length of folderinfo's group_names & group_dirs lists determines how #    many groups are compared.
    # => Also note that indices must correspond (i.e., idx #    1's name will be used #    for dataset stored in group_dir's idx 1)
    folderinfo = {}
    folderinfo["group_names"] = [
        # RM Dataset
        "5mm",
        "12mm",
        "25mm",
        # Testing Dataset
        # "one",
        # "two",
        # 6 Group Dataset
        # "36w_5mm",
        # "36w_12mm",
        # "36w_25mm",
        # "104w_5mm",
        # "104w_12mm",
        # "104w_25mm",
    ]
    folderinfo["group_dirs"] = [
        # --------------------------
        # Testing Dataset
        # "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/Testing/Group 1/",
        # "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/Testing/Group 2/",
        # --------------------------
        # RM Dataset (example data in repo)
        "/Users/mahan/sciebo/PythonCode/gaita_repo/example data/5mm/Results/",
        "/Users/mahan/sciebo/PythonCode/gaita_repo/example data/12mm/Results/",
        "/Users/mahan/sciebo/PythonCode/gaita_repo/example data/25mm/Results/",
        # --------------------------
        # 6 Group Dataset (nothing needed)
    ]
    folderinfo["results_dir"] = (
        # "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/example_data_results/"
        "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/Testing/GroupResults/"
        # "/Users/mahan/Desktop/Test6GroupResults/"
    )
    folderinfo["load_dir"] = (
        ""
        # "/Users/mahan/sciebo/Research/AutoGaitA/Mouse/Final Mouse Results/AdultElder3BeamsForPaper"  # for 6 group analysis example
    )
    # cfg
    cfg = {}
    cfg["do_permtest"] = True
    cfg["do_anova"] = True
    cfg["anova_design"] = "RM ANOVA"
    cfg["permutation_number"] = 100
    cfg["PCA_n_components"] = 6
    # cfg["PCA_n_components"] = 0.33
    # cfg["PCA_custom_scatter_PCs"] = "4,5,6;4,5;2,4,6"
    cfg["PCA_custom_scatter_PCs"] = ""
    cfg["PCA_save_3D_video"] = False  # True
    cfg["PCA_bins"] = ""  # "0-10,24,50-75"
    cfg["stats_threshold"] = 0.05
    cfg["plot_SE"] = True
    cfg["color_palette"] = "Set2"
    cfg["dont_show_plots"] = True
    cfg["legend_outside"] = True
    cfg["which_leg"] = "left"
    cfg["PCA_variables"] = [
        # "Hind paw tao y",
        # "Ankle y",
        # "Knee y",
        # "Ankle Angle",
        # "Knee Angle",
        # "Nose x",
        # "Knee y",
        # "Knee x",
        # "Knee Velocity",
        # "Knee Acceleration",
        # "Knee Angle",
        # "Knee Angle Velocity",
        # "Knee Angle Acceleration",
        # "Hip Angle",
    ]
    cfg["stats_variables"] = [
        # "Hind paw tao y",
        "Ankle y",
        # "Knee y",
        # "Ankle Angle",
        # "Knee Angle",
        # "Nose x",
        # "Knee y",
        # "Knee x",
        # "Knee Velocity",
        # "Knee Acceleration",
        # "Knee Angle",
        # "Knee Angle Velocity",
        # "Knee Angle Acceleration",
        # "Hip Angle",
        # "Elbow Angle"
    ]
    # run
    autogaita.group(folderinfo, cfg)


# %% what happens if we just hit run
if __name__ == "__main__":
    group_dlcrun()

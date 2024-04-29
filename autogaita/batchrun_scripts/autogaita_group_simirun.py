from autogaita import autogaita_group


def group_simirun():
    """
    Batchrun script to run AutoGaitA Group for Results obtained with AutoGaitA Simi.
    folderinfo & cfg dictionaries must be configured as explained in our documentation. See the "AutoGaitA without the GUI" section of our documentation for references to in-depth explanations to all dictionary keys (note that each key of dicts corresponds to some object in the AutoGaitA Group GUI)
    """
    # loop over legs - currently no option to do both legs in a single run
    cfg = {}
    for cfg["which_leg"] in ["left", "right"]:
        # folderinfo
        # => Note that length of folderinfo's group_names & group_dirs lists determines #    how many groups are compared.
        # => Also note that indices must correspond (i.e., idx #    1's name will be #    used for dataset stored in group_dir's idx 1)
        folderinfo = {}
        folderinfo["group_names"] = ["Young", "Old"]
        folderinfo["group_dirs"] = [
            "/Users/mahan/sciebo/Research/AutoGaitA/Human/Testing2/Young/",
            "/Users/mahan/sciebo/Research/AutoGaitA/Human/Testing2/Old/",
        ]
        folderinfo["results_dir"] = (
            "/Users/mahan/sciebo/Research/AutoGaitA/Human/Testing2/Group/"
            + cfg["which_leg"]
            + " leg/"
        )
        # cfg
        cfg["do_permtest"] = True
        cfg["do_anova"] = True
        cfg["permutation_number"] = 10
        cfg["number_of_PCs"] = 3
        cfg["save_3D_PCA_video"] = False
        cfg["stats_threshold"] = 0.05
        cfg["plot_SE"] = False
        cfg["anova_design"] = "Mixed ANOVA"
        cfg["PCA_variables"] = [
            "Midfoot, " + cfg["which_leg"] + " Z",
            "Ankle, " + cfg["which_leg"] + " Z",
            "Knee, " + cfg["which_leg"] + " Z",
            "Hip, " + cfg["which_leg"] + " Z",
            "Skullbase Angle",
            "Elbow, " + cfg["which_leg"] + " Angle",
            "Pelvis Z",
            "Shoulder, " + cfg["which_leg"] + " Z",
        ]
        cfg["stats_variables"] = [
            "Midfoot, " + cfg["which_leg"] + " Z",
            "Ankle, " + cfg["which_leg"] + " Z",
            # "Knee, " + cfg["which_leg"] + " Z",
            # "Shoulder, " + cfg["which_leg"] + " Angle",
            "Skullbase Angle",
            "Elbow, " + cfg["which_leg"] + " Angle",
        ]
        # run
        autogaita_group.group(folderinfo, cfg)


# %% what happens if we just hit run
if __name__ == "__main__":
    group_simirun()

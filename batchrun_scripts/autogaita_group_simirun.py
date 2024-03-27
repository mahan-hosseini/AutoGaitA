# Contrast autogaita_simi results using autogaita_group
from autogaita import autogaita_group

def group_simirun():
    """Batch run group level analyses for results obtained with _simi"""
    # constant folderinfo & cfg vars
    folderinfo = {}
    cfg = {}
    cfg["do_permtest"] = True
    cfg["do_anova"] = True
    cfg["permutation_number"] = 10
    cfg["number_of_PCs"] = 3
    cfg["save_3D_PCA_video"] = True
    cfg["stats_threshold"] = 0.05
    cfg["plot_SE"] = False

    # loop over legs
    for cfg["which_leg"] in ["left", "right"]:

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

        # 2 groups - human
        folderinfo["group_names"] = [
            "Young",
            "Old"
            ]
        folderinfo["group_dirs"] = [
            "/Users/mahan/sciebo/Research/AutoGaitA/Human/Testing2/Young/",
            "/Users/mahan/sciebo/Research/AutoGaitA/Human/Testing2/Old/",
        ]

        folderinfo[
            "results_dir"
            # human
        ] = "/Users/mahan/sciebo/Research/AutoGaitA/Human/Testing2/Group/" + cfg["which_leg"] + " leg/"

        autogaita_group.main(folderinfo, cfg)



    # ...........................  with subgroups  .....................................
    # # loop over legs
    # for subgroup in ["Young", "Old", "Both"]:
    #     for cfg["which_leg"] in ["left", "right"]:

    #         cfg["anova_design"] = "RM ANOVA"  # "Mixed ANOVA"
    #         cfg["PCA_variables"] = [
    #             "Midfoot, " + cfg["which_leg"] + " Z",
    #             "Ankle, " + cfg["which_leg"] + " Z",
    #             "Knee, " + cfg["which_leg"] + " Z",
    #             "Hip, " + cfg["which_leg"] + " Z",
    #             "Pelvis Z",
    #         ]
    #         cfg["stats_variables"] = [
    #             "Midfoot, " + cfg["which_leg"] + " Z",
    #             "Ankle, " + cfg["which_leg"] + " Z",
    #             "Knee, " + cfg["which_leg"] + " Z",
    #             # "Ankle, " + cfg["which_leg"] + " Angle",
    #             # "Knee, " + cfg["which_leg"] + " Angle",
    #             # "Hip, " + cfg["which_leg"] + " Angle",
    #             ]

    #         # 2 groups - human
    #         folderinfo["group_names"] = [
    #             "Forwards",
    #             "Backwards"
    #             ]
    #         folderinfo["group_dirs"] = [
    #             "/Users/mahan/sciebo/Research/AutoGaitA/Human/Check Walking Direction/Forwards Subject Results/" + subgroup + "/",
    #             "/Users/mahan/sciebo/Research/AutoGaitA/Human/Check Walking Direction/Backwards Subject Results/" + subgroup + "/",
    #         ]

    #         folderinfo[
    #             "results_dir"
    #             # human
    #         ] = "/Users/mahan/sciebo/Research/AutoGaitA/Human/Check Walking Direction/Forwards v Backwards/" + subgroup + "/" + cfg["which_leg"] + " leg/"

    #         autogaita_group.main(folderinfo, cfg)

# %% what happens if we hit run
if __name__ == "__main__":
    group_simirun()

# %% imports
from autogaita.group.group_utils import write_issues_to_textfile
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns

# %% constants
from autogaita.group.group_constants import (
    ISSUES_TXT_FILENAME,
    STATS_TXT_FILENAME,
    CONFIG_JSON_FILENAME,
    ORIG_SHEET_NAME,
)


# %% .................  workflow step #1 - unpack & prepare vars  ....................


def some_prep(folderinfo, cfg):
    """Add some folderinfo & cfg variables to the dictionaries for further processes"""

    # unpack
    group_names = folderinfo["group_names"]
    group_dirs = folderinfo["group_dirs"]
    results_dir = folderinfo["results_dir"]

    # names & paths to folderinfo
    if not os.path.isdir(results_dir):
        os.makedirs(results_dir)
    folderinfo["contrasts"] = []
    for i in range(len(group_names)):
        for j in range(i + 1, len(group_names)):
            contrast = group_names[i] + " & " + group_names[j]
            folderinfo["contrasts"].append(contrast)

    # check if we previously had saved issues & stats textfiles, if so delete them
    issues_txt_path = os.path.join(results_dir, ISSUES_TXT_FILENAME)
    if os.path.exists(issues_txt_path):
        os.remove(issues_txt_path)
    stats_txt_path = os.path.join(results_dir, STATS_TXT_FILENAME)
    if os.path.exists(stats_txt_path):
        os.remove(stats_txt_path)

    # extracted_cfg_vars: save_to_xls, PCA tests & dont show plots
    cfg = extract_cfg_vars(folderinfo, cfg)

    # see if there's a config json file and add to cfg dict
    for g_idx, group_dir in enumerate(group_dirs):
        with open(
            os.path.join(group_dir, CONFIG_JSON_FILENAME), "r"
        ) as config_json_file:
            config_vars_from_json = json.load(config_json_file)
            for key in config_vars_from_json.keys():
                # assigning like this ensure all keys are in all jsons across groups
                if g_idx == 0:
                    cfg[key] = config_vars_from_json[key]
                else:
                    # sanity check for group-differences in cfg variables!
                    if (key not in cfg.keys()) | (
                        cfg[key] != config_vars_from_json[key]
                    ):
                        error_message = (
                            "config.json variables differ between groups!"
                            + "\nPlease make sure that all cfg variables between "
                            + "groups match & try again!"
                        )
                        raise ValueError(error_message)
                    else:
                        cfg[key] = config_vars_from_json[key]

    # after having checked cfg keys for equivalence, we have to make sure that
    # hind_joints is renamed to joints if DLC
    # => note that cfg will not be updated (and overwritten from input if Universal 3D so it's)
    #    okay that we do this
    if cfg["tracking_software"] == "DLC":
        cfg["joints"] = cfg["hind_joints"]
    joints = cfg["joints"]
    angles = cfg["angles"]

    # prepare some plotting color stuff
    cfg["group_color_cycler"] = plt.cycler(
        "color", sns.color_palette(cfg["color_palette"], len(group_names))
    )
    cfg["group_color_dict"] = dict(
        zip(group_names, cfg["group_color_cycler"].by_key()["color"])
    )
    cfg["joint_color_cycler"] = plt.cycler(
        "color", sns.color_palette(cfg["color_palette"], len(joints))
    )
    cfg["angle_color_cycler"] = plt.cycler(
        "color", sns.color_palette(cfg["color_palette"], len(angles["name"]))
    )

    return folderinfo, cfg


def extract_cfg_vars(folderinfo, cfg):
    """Extract bin_num and save_to_xls from example Normalised dfs and sanity check
    that they match between groups!
    """

    group_names = folderinfo["group_names"]
    group_dirs = folderinfo["group_dirs"]
    results_dir = folderinfo["results_dir"]

    # ................................  save_to_xls  ...................................
    save_to_xls = [None] * len(group_dirs)
    for g, group_dir in enumerate(group_dirs):
        all_results_folders = os.listdir(
            group_dir
        )  # remove no-results valid_results_folders
        valid_results_folders = []
        # => Note if there's ambiguity / mixed filetypes, we set save_to_xls to True!
        sheet_type_mismatch_message = (
            "\n***********\n! WARNING !\n***********\n"
            + "Mismatch in sheet file types for group "
            + group_names[g]
            + "!\nSaving all output sheets to"
            + ".xlsx!\nRe-run first level & only save .csvs if "
            + "you want .csv files of group results!"
        )
        for folder in all_results_folders:
            # create save_to_xls here, there are two cases we have to deal with:
            # case 1: we found a csv file
            if os.path.exists(
                os.path.join(
                    group_dir,
                    folder,
                    folder + " - " + ORIG_SHEET_NAME + ".csv",
                )
            ):
                valid_results_folders.append(folder)
                if save_to_xls[g] is None:
                    save_to_xls[g] = False
                if save_to_xls[g] is True:
                    print(sheet_type_mismatch_message)
                    write_issues_to_textfile(sheet_type_mismatch_message, results_dir)
            # case 2: we found a xlsx file
            elif os.path.exists(
                os.path.join(
                    group_dir,
                    folder,
                    folder + " - " + ORIG_SHEET_NAME + ".xlsx",
                )
            ):
                valid_results_folders.append(folder)
                if save_to_xls[g] is None:
                    save_to_xls[g] = True
                if save_to_xls[g] is False:
                    save_to_xls[g] = True
                    print(sheet_type_mismatch_message)
                    write_issues_to_textfile(sheet_type_mismatch_message, results_dir)
        # test that at least 1 folder has valid results for all groups
        if not valid_results_folders:
            no_valid_results_error = (
                "\n*********\n! ERROR !\n*********\n"
                + "No valid results folder found for "
                + group_names[g]
                + "\nFix & re-run!"
            )
            print(no_valid_results_error)
            write_issues_to_textfile(no_valid_results_error, results_dir)
    # assign to our cfg dict after group loop
    cfg["save_to_xls"] = save_to_xls

    # .........................  test if PCA config is valid  ..........................
    if cfg["PCA_variables"]:  # only test if user wants PCA (ie. selected any features)
        if len(cfg["PCA_variables"]) < cfg["number_of_PCs"]:
            PCA_variable_num = len(cfg["PCA_variables"])
            PCA_variables_str = "\n".join(cfg["PCA_variables"])
            PCA_error_message = (
                "\n*********\n! ERROR !\n*********\n"
                + "\nPCA Configuration invalid, number of input features cannot exceed "
                + "number of principal components to compute!\n"
                + str(PCA_variable_num)
                + " PCA variables: \n"
                + PCA_variables_str
                + "\n & Number of wanted PCs: "
                + str(cfg["number_of_PCs"])
                + "\n Fix & re-run!"
            )
            write_issues_to_textfile(PCA_error_message, results_dir)
            raise ValueError(PCA_error_message)
        if cfg["number_of_PCs"] < 2:
            print(
                "\n***********\n! WARNING !\n***********\n"
                + "Number of principal components of PCA cannot be smaller than 2!"
                + "\nRunning PCA on 2 components - if you do not want to perform PCA, "
                + "just don't choose any variables for it."
            )
            cfg["number_of_PCs"] = 2  # make sure to update in cfg dict

    return cfg

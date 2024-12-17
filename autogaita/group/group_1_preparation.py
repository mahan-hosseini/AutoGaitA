# %% imports
from autogaita.resources.utils import write_issues_to_textfile
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns

# %% constants
from autogaita.resources.constants import ISSUES_TXT_FILENAME, CONFIG_JSON_FILENAME
from autogaita.group.group_constants import (
    GROUP_CONFIG_TXT_FILENAME,
    STATS_TXT_FILENAME,
    MULTCOMP_EXCEL_FILENAME_1,
    MULTCOMP_EXCEL_FILENAME_2,
    ORIG_SHEET_NAME,
    CONTRAST_SPLIT_STR,
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
            contrast = group_names[i] + CONTRAST_SPLIT_STR + group_names[j]
            folderinfo["contrasts"].append(contrast)

    # check if we previously had saved info files, if so delete them
    for info_file_name in [
        GROUP_CONFIG_TXT_FILENAME,
        ISSUES_TXT_FILENAME,
        STATS_TXT_FILENAME,
        MULTCOMP_EXCEL_FILENAME_1,
        MULTCOMP_EXCEL_FILENAME_2,
    ]:
        info_file_path = os.path.join(results_dir, info_file_name)
        if os.path.exists(info_file_path):
            os.remove(info_file_path)

    # extracted_cfg_vars: save_to_xls, PCA stuff & dont show plots
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
    """Extract save_to_xls from example Normalised dfs and sanity check
    that they match between groups. Also some stuff for PCA!
    """

    group_names = folderinfo["group_names"]
    group_dirs = folderinfo["group_dirs"]

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
                    write_issues_to_textfile(sheet_type_mismatch_message, folderinfo)
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
                    write_issues_to_textfile(sheet_type_mismatch_message, folderinfo)
        # test that at least 1 folder has valid results for all groups
        if not valid_results_folders:
            no_valid_results_error = (
                "\n*********\n! ERROR !\n*********\n"
                + "No valid results folder found for "
                + group_names[g]
                + "\nFix & re-run!"
            )
            print(no_valid_results_error)
            write_issues_to_textfile(no_valid_results_error, folderinfo)
    # assign to our cfg dict after group loop
    cfg["save_to_xls"] = save_to_xls

    # .........................  test if PCA config is valid  ..........................
    # only test if user wants PCA (ie. selected any features) and is not using the
    # var-explained appproiach
    if cfg["PCA_variables"] and cfg["PCA_n_components"] > 1:
        if len(cfg["PCA_variables"]) < cfg["PCA_n_components"]:
            PCA_variable_num = len(cfg["PCA_variables"])
            PCA_variables_str = "\n".join(cfg["PCA_variables"])
            PCA_error_message = (
                "\n*********\n! ERROR !\n*********\n"
                + "\nPCA Configuration invalid, number of input features must exceed "
                + "the number of principal components to compute!\n"
                + str(PCA_variable_num)
                + " PCA variables: \n"
                + PCA_variables_str
                + "\n & Number of wanted PCs: "
                + str(cfg["PCA_n_components"])
                + "\n Fix & re-run!"
            )
            write_issues_to_textfile(PCA_error_message, folderinfo)
            raise ValueError(PCA_error_message)
        if cfg["PCA_n_components"] < 2:
            print(
                "\n***********\n! WARNING !\n***********\n"
                + "Number of principal components of PCA cannot be 0 or 1!"
                + "\nRunning PCA on 2 components - if you do not want to perform PCA, "
                + "just don't choose any variables for it."
            )
            cfg["PCA_n_components"] = 2  # make sure to update in cfg dict
    # small fix to ensure that PCA vars don't have duplicates (this would have severe
    # consequences for run_PCA since features of PCA_model output and "my" features var
    # would not match)
    # => it should never happen via GUI really but I did this myself using group_dlcrun #    while not paying attention...
    unique_PCA_vars = list(set(cfg["PCA_variables"]))
    if len(unique_PCA_vars) != len(cfg["PCA_variables"]):
        duplicate_vars = [
            var for var in cfg["PCA_variables"] if cfg["PCA_variables"].count(var) > 1
        ]
        PCA_duplicates_error_message = (
            "\n*********\n! WARNING !\n*********\n"
            + "\nWe found duplicates in your PCA variables list!"
            + "\nWe removed them for you!"
            + "\n\nDuplicate variables were:\n"
            + "\n".join(list(set(duplicate_vars)))
        )
        print(PCA_duplicates_error_message)
        write_issues_to_textfile(PCA_duplicates_error_message, folderinfo)
        cfg["PCA_variables"] = unique_PCA_vars
    # check if PCA bin num is valid, two tests and 1 fix
    # => note there is separate code that transforms this string input into an int-list
    if cfg["PCA_bins"]:
        PCA_bins_error_message = ""
        cfg["PCA_bins"] = cfg["PCA_bins"].replace(" ", "")  # remove spaces
        # test 1: only digits, commas and dashes allowed
        for char in cfg["PCA_bins"]:
            if char.isdigit() or char in ["-", ","]:
                pass
            else:
                PCA_bins_error_message = (
                    "\n*********\n! ERROR !\n*********\n"
                    + "\nPCA Bin Number invalid!"
                    + "\nPlease use only numbers, commas and dashes in your input!"
                    + "\nFix & re-run!"
                )
        # test 2: no comma next to dash
        if ",-" in cfg["PCA_bins"] or "-," in cfg["PCA_bins"]:
            PCA_bins_error_message = (
                "\n*********\n! ERROR !\n*********\n"
                + "\nPCA Bin Number invalid!"
                + "\nCommas cannot be next to dashes in your input!"
                + "\nFix & re-run!"
            )
        # if any test failed we raise an error
        # => note we could continue execution without custom PCA bins but if the user
        #    tried to set them, it's likely important to them to have custom bins
        #    so we just stop everything and help them fix it
        if PCA_bins_error_message:
            print(PCA_bins_error_message)
            write_issues_to_textfile(PCA_bins_error_message, folderinfo)
            raise ValueError(PCA_bins_error_message)
        # fix for users: remove first and last characters if not digits
        while not cfg["PCA_bins"][0].isdigit():
            cfg["PCA_bins"] = cfg["PCA_bins"][1:]
        while not cfg["PCA_bins"][-1].isdigit():
            cfg["PCA_bins"] = cfg["PCA_bins"][:-1]

    return cfg

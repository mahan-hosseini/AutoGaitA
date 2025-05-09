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

    # AN IMPORTANT NOTE ABOUT LOAD_DIR
    # --------------------------------
    # Alright so the group pipeline's cfg (and thus, of course, config.json) is a bit
    # special because it includes:
    # 1) first-level config-keys, such as "joints" or "angles", that reflect what has
    #    been analysed at the first level. Some of these are used in group workflow
    #    (e.g. tracking_software when plotting or sampling_rate for PCA) and all of
    #    these are  checked for equivalence across groups when running this without
    #    load_dir (see the for g_idx loop below) to ensure we are not comparing
    #    different sampling rates or so with a group analysis
    # 2) group-level config-keys, such as "do_permtest" or "PCA_variables" that define
    #    how group analysis should be done
    # Now:
    # When loading previously generated group dfs (i.e., using load_dir), the vars in
    # (2) should naturally be changing so the user can change "PCA_variables" or
    # "do_anova". The config.json is coded to reflect the group-keys of the most
    # recent analysis. The "first-level" config keys are, however, just checked for
    # equivalence once and then never changed by group gaita. So if users should
    # repeatedly run analyses in the same results_dir, the config.json file includes
    # the first-level keys of the first run and the group-level keys of the most recent
    # run. This is not an issue per se but very likely something that I might forget in
    # a year thus here is a note.

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

    # load a couple necessary first-level cfg vars from previous run's group config.json
    if len(folderinfo["load_dir"]) > 0:
        cfg = load_previous_runs_first_level_cfg_vars(folderinfo, cfg)

    # define save_to_xls and test PCA
    cfg = extract_save_to_xls_and_test_PCA_config(folderinfo, cfg)

    # if not loading previous results, ensure cfg-keys are equivalent across groups
    # then add them to cfg dict
    if len(folderinfo["load_dir"]) == 0:
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
                                + f"\nMismatch at {key} in group {group_names[g_idx]}"
                            )
                            raise ValueError(error_message)
                        else:
                            cfg[key] = config_vars_from_json[key]

    # rename hind_joints to joints (if DLC or SLEAP)
    if "hind_joints" in cfg.keys():
        cfg["joints"] = cfg["hind_joints"]

    # update cfg keys in json file in results_dir
    # => i.e. if there's already a config.json @ results_dir (happens if load_dir was
    #    True) the if-condition below updates (only) the group-config keys according to
    #    this run's cfg dict
    # => this also means that first-level cfg keys are never changed (which is intended)
    config_json_path = os.path.join(results_dir, CONFIG_JSON_FILENAME)
    if os.path.exists(config_json_path):
        with open(config_json_path, "r") as config_json_file:
            existing_cfg = json.load(config_json_file)
        existing_cfg.update({key: cfg[key] for key in cfg if key in existing_cfg})
        cfg = existing_cfg  # update cfg with existing keys
    with open(config_json_path, "w") as config_json_file:
        json.dump(cfg, config_json_file)

    # create this plot stuff manually (cycler objects cannot be written to json)
    cfg["group_color_cycler"] = plt.cycler(
        "color", sns.color_palette(cfg["color_palette"], len(group_names))
    )
    cfg["group_color_dict"] = dict(
        zip(group_names, cfg["group_color_cycler"].by_key()["color"])
    )
    cfg["joint_color_cycler"] = plt.cycler(
        "color", sns.color_palette(cfg["color_palette"], len(cfg["joints"]))
    )
    cfg["angle_color_cycler"] = plt.cycler(
        "color", sns.color_palette(cfg["color_palette"], len(cfg["angles"]["name"]))
    )

    # have this key for a unit test - make sure it's never written to json
    if len(folderinfo["load_dir"]) > 0:
        cfg["loaded"] = True

    return folderinfo, cfg


def load_previous_runs_first_level_cfg_vars(folderinfo, cfg):
    """There are a couple "first-level" cfg vars (like "joints") we require for group gaita's workflow - load them here"""
    with open(
        os.path.join(folderinfo["load_dir"], CONFIG_JSON_FILENAME), "r"
    ) as config_json_file:
        old_cfg = json.load(config_json_file)
        cfg["sampling_rate"] = old_cfg["sampling_rate"]
        cfg["save_to_xls"] = old_cfg["save_to_xls"]
        cfg["joints"] = old_cfg["joints"]
        cfg["angles"] = old_cfg["angles"]
        cfg["tracking_software"] = old_cfg["tracking_software"]
        if "analyse_average_x" in old_cfg.keys():
            cfg["analyse_average_x"] = old_cfg["analyse_average_x"]
        if "analyse_average_y" in old_cfg.keys():
            cfg["analyse_average_y"] = old_cfg["analyse_average_y"]
    return cfg


def extract_save_to_xls_and_test_PCA_config(folderinfo, cfg):
    """Extract save_to_xls from example Normalised dfs and sanity check
    that they match between groups. Also some tests for users' PCA config!
    """

    # NOTE
    # ----
    # save_to_xls is a list of bools that is infered from file type of group's sheet
    # files - only when not using load_dir. if we use load_dir, save_to_xls is loaded
    # by load_previous_runs_first_level_cfg_vars

    # ................................  save_to_xls  ...................................
    if len(folderinfo["load_dir"]) == 0:
        # infer save_to_xls from sheet files
        cfg["save_to_xls"] = infer_save_to_xls_from_group_dirs_sheetfiles(folderinfo)

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


def infer_save_to_xls_from_group_dirs_sheetfiles(folderinfo):
    """Generate a list of save_to_xls bools that is automatically inferred from sheet file in group dir"""

    # unpack
    group_names = folderinfo["group_names"]
    group_dirs = folderinfo["group_dirs"]

    save_to_xls = [None] * len(group_dirs)
    for g, group_dir in enumerate(group_dirs):
        all_results_folders = os.listdir(
            group_dir
        )  # remove no-results valid_results_folders
        valid_results_folders = []
        # => Note if there are mixed filetypes, we set save_to_xls to True!
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
    return save_to_xls

import os
import json
import tkinter as tk


# ............................ gui config file operations  ............................
def update_config_file(
    results,
    cfg,
    autogaita_folder_path,
    config_file_name,
    list_vars,
    dict_vars,
    tk_str_vars,
    tk_bool_vars,
):
    """updates the dlc_gui_config file with this runs parameters"""
    # transform tkVars into normal strings and bools
    output_dicts = [{}, {}]
    for i in range(len(output_dicts)):
        if i == 0:
            # in case update_config_file is called before results is defined
            # as in the creation of the exit_button in the dlc_gui() function
            # the results dict of the last run is used and only cfg is updated
            if results == "results dict not defined yet":
                # runwindow = None as we dont need the tk.Vars to refer to a specific window
                input_dict = extract_results_from_json_file(
                    None,
                    autogaita_folder_path,
                    config_file_name,
                    tk_str_vars,
                    tk_bool_vars,
                )
            else:
                input_dict = results
        elif i == 1:
            input_dict = cfg
        for key in input_dict.keys():
            if key in list_vars:
                # if list of strings, initialise output empty list and get & append vals
                output_dicts[i][key] = []
                for list_idx in range(len(input_dict[key])):
                    output_dicts[i][key].append(input_dict[key][list_idx].get())
            elif key in dict_vars:
                # if dict of list of strings, initialise as empty dict and assign stuff
                # key = "angles" or other DICT_VAR
                # inner_key = "name" & "lower_ / upper_joint"
                # list_idx = idx of list of strings of inner_key
                output_dicts[i][key] = {}
                for inner_key in input_dict[key]:
                    output_dicts[i][key][inner_key] = []
                    for list_idx in range(len(input_dict[key][inner_key])):
                        output_dicts[i][key][inner_key].append(
                            input_dict[key][inner_key][list_idx].get()
                        )
            else:
                output_dicts[i][key] = input_dict[key].get()

    # merge the two configuration dictionaries
    configs_list = [output_dicts[0], output_dicts[1]]  # 0 = results, 1 = cfg, see above
    # write the configuration file
    with open(
        os.path.join(autogaita_folder_path, config_file_name), "w"
    ) as config_json_file:
        json.dump(configs_list, config_json_file, indent=4)


def extract_cfg_from_json_file(
    window,
    autogaita_folder_path,
    config_file_name,
    list_vars,
    dict_vars,
    tk_str_vars,
    tk_bool_vars,
):
    """loads the cfg dictionary from the config file"""
    # load the configuration file
    with open(
        os.path.join(autogaita_folder_path, config_file_name), "r"
    ) as config_json_file:
        # config_json contains list with 0 -> result and 1 -> cfg data
        last_runs_cfg = json.load(config_json_file)[1]

    cfg = {}
    # assign values to the cfg dict
    for key in last_runs_cfg.keys():
        if key in tk_bool_vars:
            cfg[key] = tk.BooleanVar(window, last_runs_cfg[key])
        elif key in list_vars:
            cfg[key] = []
            for entry in last_runs_cfg[key]:
                cfg[key].append(tk.StringVar(window, entry))
        elif key in dict_vars:
            cfg[key] = {}
            for subkey in last_runs_cfg[key]:
                cfg[key][subkey] = []
                for entry in last_runs_cfg[key][subkey]:
                    cfg[key][subkey].append(tk.StringVar(window, entry))
        elif key in tk_str_vars:  # Integers are also saved as strings
            cfg[key] = tk.StringVar(window, last_runs_cfg[key])
    return cfg


def extract_results_from_json_file(
    window, autogaita_folder_path, config_file_name, tk_str_vars, tk_bool_vars
):
    """loads the results dictionary from the config file"""

    # load the configuration file
    with open(
        os.path.join(autogaita_folder_path, config_file_name), "r"
    ) as config_json_file:
        # config_json contains list with 0 -> result and 1 -> cfg data
        last_runs_results = json.load(config_json_file)[0]

    results = {}
    for key in last_runs_results.keys():
        if key in tk_str_vars:
            results[key] = tk.StringVar(window, last_runs_results[key])
        elif key in tk_bool_vars:
            results[key] = tk.BooleanVar(window, last_runs_results[key])

    return results

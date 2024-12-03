from autogaita.dlc.dlc_utils import prepare_DLC_df
import os
import pandas as pd
import pdb

# user inputs
TASK = "DLC"  # can be DLC, clean or rename
ROOT_DIR = "/Users/mahan/sciebo/Research/AutoGaitA/Fly/3D Data"  # path to the folder with the files to have columns cleaned/renamed
FILE_TYPE = "csv"  # can be csv, xls or xlsx
POSTNAME_STRING = "_dlc"  # string that must be included in loading files
RESULTS_DIR = ""
SEPARATOR = "_"
STRING_TO_REMOVE = "_xyz"  # string to remove from colnames before renaming


# global constants
CANDIDATE_SIDE_IDENTIFIER = ["l", "r", "left", "right"]  # user-strings forced lowercase
CANDIDATE_COORD_IDENTIFIER = ["x", "y", "z"]
SIDE_KEY = "side"
COORD_KEY = "coordinate"
JOINT_KEY = "joint"
COMMA_SEP = ", "
SPACE_SEP = " "


# NU
# => could add an option to either remove or keep the cols that are not renamed


# .............................  main 3D preparation  ..................................
def prepare_3D(task, cfg, **kwargs):
    """
    Main renaming function in preparation for 3D universal gaita

    Workflow
    --------
    1) Scan through folder and load based on file type
    2) Run the main function saving to excel
    3) Print a message about how many files were renamed successfully
    """

    # unpack
    root_dir = cfg["root_dir"]
    results_dir = cfg["results_dir"]
    file_type = cfg["file_type"]
    postname_string = cfg["postname_string"]
    if task == "clean":
        string_to_remove = kwargs["string_to_remove"]
    elif task in ["rename", "DLC"]:
        separator = kwargs["separator"]
    if task == "DLC":  # DLC hard-coding file type
        file_type = "csv"

    # loop over files in root dir
    counter = 0
    for input_file in os.listdir(root_dir):
        if postname_string in input_file and input_file.endswith(f".{file_type}"):
            # load
            full_input_file = os.path.join(root_dir, input_file)
            df = load_input_file(full_input_file, file_type)
            # run
            if task == "clean":
                # cleaning function
                df = clean_a_file(df, string_to_remove)  # note string_to_remove var
            elif task == "rename":
                # main renaming function
                df = rename_a_file(df, separator)  # note separator var
            elif task == "DLC":
                df = rename_DLC_file(df, separator)
            # save
            save_output_file(task, df, root_dir, results_dir, input_file, file_type)
            counter += 1
    if task == "clean":
        return f"\nCleaned {counter} file successfully!"
    elif task in ["rename", "DLC"]:
        return f"\nRenamed {counter} file successfully!"


def rename_DLC_file(df, separator):
    """Rename 3D DeepLabCut files to Universal 3D GaitA.
    This takes the same function we use in gaita dlc's some_prep

    Note
    ----
    Separator in this case means the string that is used to differentiate left/right side identifier from key point identifier in (!) the BODYPARTS row of original 3D DLC files only!
    """

    df = prepare_DLC_df(df, separator)
    # at this point df has columns of the form "joint_side_coord" or "joint_coord" or
    # any perturbation of this. Important is again the separator that has to be
    # "constant" & "unique" in the columns we can use it as we do with the other
    # datasets.
    df = rename_a_file(df, separator)
    return df


# ..............................  cleaning function  ...................................
def clean_a_file(df, string_to_remove):
    """
    Function to remove unnecessary sub-strings in colnames prior to batch renaming
    colnames according to Universal 3D GaitA
    """
    new_col_dict = {}
    for col in df.columns:
        if string_to_remove in col:
            new_col = col.replace(string_to_remove, "")
            new_col_dict[col] = new_col
    df.rename(columns=new_col_dict, inplace=True)
    return df


# ..............................  renaming function  ...................................
def rename_a_file(df, separator):
    """
    Loop over all cols in df, rename function renames cols only if needed and, if so, based on side-specificity or not

    Note
    ----
    Separator must be unique in string, e.g. cannot be in key joint name
    """
    new_col_strings = []
    for col_string in df.columns:
        new_col_strings.append(rename_a_column(col_string, separator))
    # rename the cols in the df
    df.columns = new_col_strings
    return df


# ..............................  helper functions  ...................................
def rename_a_column(col_string, separator):
    """
    Renames a column string based on specific identifiers separated by a given separator.

    Workflow
    --------
    1) Extracts the identifiers based on the separators (check capitsalisation comments)
    2) Returns the new column name based on whether this column is side-specific, central, or not a coordinate column at all
    """
    id_dict = {}  # just used locally in this func to get (new) col names
    # first, extract identifiers based on separators
    # => lower case candidate_ids for comparison to side & coord identifiers
    # => note we store original candidate id for JOINT_KEY!
    # => note in COORD_KEY the OUTPUT (!) should be capitalised!
    for candidate_id in col_string.split(separator):
        original_candidate_id = candidate_id
        candidate_id = candidate_id.lower()
        # 1: sides are set to pre-set values
        if candidate_id in CANDIDATE_SIDE_IDENTIFIER:
            if candidate_id in ["l", "left"]:
                id_dict[SIDE_KEY] = "left"
            if candidate_id in ["r", "right"]:
                id_dict[SIDE_KEY] = "right"
        # 2: coords are set to what they were but capitalised
        elif candidate_id in CANDIDATE_COORD_IDENTIFIER:
            id_dict[COORD_KEY] = candidate_id.capitalize()
        # 3: joint is set to what it was (before lower-casing!)
        else:
            id_dict[JOINT_KEY] = original_candidate_id
    # then, return the new col name based on whether this col is side-specific,
    # central, or not a coordinate column at all
    if id_dict.keys() == {COORD_KEY, JOINT_KEY}:
        return f"{id_dict[JOINT_KEY]}{SPACE_SEP}{id_dict[COORD_KEY]}"
    elif id_dict.keys() == {SIDE_KEY, COORD_KEY, JOINT_KEY}:
        return f"{id_dict[JOINT_KEY]}{COMMA_SEP}{id_dict[SIDE_KEY]}{SPACE_SEP}{id_dict[COORD_KEY]}"
    else:
        return col_string


def load_input_file(full_input_file, file_type):
    """Load & return the given input file based on its type."""
    if file_type == "csv":
        return pd.read_csv(full_input_file)
    elif file_type == "xls":
        return pd.read_excel(full_input_file, engine="xlrd")
    elif file_type == "xlsx":
        return pd.read_excel(full_input_file, engine="openpyxl")


def save_output_file(task, df, root_dir, results_dir, input_file, file_type):
    """Save the generated output file according to task and configuration."""
    if task in ["rename", "DLC"]:
        output_file = input_file.split("." + file_type)[0] + "_renamed.xlsx"
    elif task == "clean":
        output_file = (
            input_file.split("." + file_type)[0] + "_cleaned" + "." + file_type
        )
    if results_dir:
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        full_output_file = os.path.join(results_dir, output_file)
    else:
        full_output_file = os.path.join(root_dir, output_file)
    # note we hard-coded output-file ending to xlsx if we are renaming
    # => since gaita needs xlsx.
    # => index=False is set to avoid unnamed col
    if output_file.endswith(".xlsx"):
        df.to_excel(full_output_file, index=False)
    elif output_file.endswith(".xls"):  # transform xls to xlsx
        df.to_excel(full_output_file + "x", index=False)
    elif output_file.endswith(".csv"):
        df.to_csv(full_output_file, index=False)


# what if we hit run
if __name__ == "__main__":
    cfg = {}
    cfg["root_dir"] = ROOT_DIR
    cfg["file_type"] = FILE_TYPE
    cfg["postname_string"] = POSTNAME_STRING
    cfg["results_dir"] = RESULTS_DIR
    if TASK == "clean":
        prepare_3D(TASK, cfg, string_to_remove=STRING_TO_REMOVE)
    elif TASK == "rename":
        prepare_3D(TASK, cfg, separator=SEPARATOR)
    elif TASK == "DLC":
        prepare_3D(TASK, cfg, separator=SEPARATOR)

import os
import pandas as pd

# user inputs
TASK = "clean"  # can be clean or rename
ROOT_DIR = "/Users/mahan/sciebo/Research/AutoGaitA/Human/Sebastian/renaming/"
SEPARATOR = "_"
RESULTS_DIR = ""
FILE_TYPE = "csv"  # can be csv, xls or xlsx
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
# => add Time column (probably in _simi though)
# => tidy it up and check if the generated xls works with gaita_simi for the renamed cols
# => if my first manual tests seem to work, then write proper unit & property tests for this
# => finally add to GUI


# .............................  main 3D preparation  ..................................
def prepare_3D(task, cfg, *args):
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
    separator = cfg["separator"]
    file_type = cfg["file_type"]
    results_dir = cfg["results_dir"]

    # loop over files in root dir
    counter = 0
    for input_file in os.listdir(root_dir):
        if input_file.endswith(f".{file_type}"):
            # load
            full_input_file = os.path.join(root_dir, input_file)
            df = load_input_file(full_input_file, file_type)
            # run
            if task == "clean":
                # cleaning function
                df = clean_a_file(df, args[0])  # args[0] = string to remove
            elif task == "rename":
                # main renaming function
                df = rename_a_file(df, separator)
            # save
            save_output_file(task, df, root_dir, results_dir, input_file, file_type)
            counter += 1
    print(f"\nRenamed {counter} file successfully!")


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
    if task == "rename":
        output_file = input_file.split("." + file_type)[0] + "_renamed.xlsx"
    elif task == "clean":
        output_file = (
            input_file.split("." + file_type)[0] + "_cleaned" + "." + file_type
        )
    if results_dir:
        full_output_file = os.path.join(results_dir, output_file)
    else:
        full_output_file = os.path.join(root_dir, output_file)
    if output_file.endswith(".xlsx"):
        df.to_excel(full_output_file)
    elif output_file.endswith(".xls"):  # transform xls to xlsx
        df.to_excel(full_output_file + "x")
    elif output_file.endswith(".csv"):
        df.to_csv(full_output_file)


# what if we hit run
if __name__ == "__main__":
    cfg = {}
    cfg["root_dir"] = ROOT_DIR
    cfg["separator"] = SEPARATOR
    cfg["file_type"] = FILE_TYPE
    cfg["results_dir"] = RESULTS_DIR
    prepare_3D(TASK, cfg, STRING_TO_REMOVE)

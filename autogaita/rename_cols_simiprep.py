import pandas as pd
import pdb

CANDIDATE_SIDE_IDENTIFIER = ["l", "r", "left", "right"]  # user-string forced lowercase
CANDIDATE_COORD_IDENTIFIER = ["x", "y", "z"]
SIDE_KEY = "side"
COORD_KEY = "coordinate"
JOINT_KEY = "joint"
COMMA_SEP = ", "
SPACE_SEP = " "

# NU
# => could add an option to either remove or keep the cols that are not renamed
# => save to xls!
# => tidy it up and check if the generated xls works with gaita_simi for the renamed cols
# => if my first manual tests seem to work, then write proper unit & property tests for this
# => finally add to GUI


def main():
    rename_master(
        "/Users/mahan/sciebo/Research/AutoGaitA/Human/Sebastian/Sebastians_Data_combined_xyz.csv",
        "_",
    )


def rename_master(root_dir, separator):
    """Note - separator must be unique in string, e.g. cannot be in key point name"""
    original_df = pd.read_csv(root_dir)
    # replace unwanted strings
    df = replace_strings_in_colnames(original_df, "_xyz")
    # loop over all cols in df, rename func renames cols only if needed
    # => and if so, based on side-specificity or not
    new_col_strings = []
    for col_string in df.columns:
        new_col_strings.append(rename_a_column(col_string, separator))
    # rename the cols in the df
    df.columns = new_col_strings
    # store df
    pdb.set_trace()
    df.to_csv(
        "/Users/mahan/sciebo/Research/AutoGaitA/Human/Sebastian/Sebastians_Data_combined_xyz_renamed.csv"
    )


def rename_a_column(col_string, separator):
    """
    Renames a column string based on specific identifiers separated by a given separator.
    1) Extracts the identifiers based on the separators (check capitsalisation comments)
    2) Returns the new column name based on whether this column is side-specific, central, or not a coordinate column at all
    """
    id_dict = {}  # just used locally in this func to get (new) col names
    # first, extract identifiers based on separators
    # => if statement with .lower() to make our life easy
    # => note in coord_key the OUTPUT (!) should be capitalised!
    for candidate_id in col_string.split(separator):
        if candidate_id.lower() in CANDIDATE_SIDE_IDENTIFIER:
            if candidate_id in ["l", "left"]:
                id_dict[SIDE_KEY] = "left"
            if candidate_id in ["r", "right"]:
                id_dict[SIDE_KEY] = "right"
        elif candidate_id.lower() in CANDIDATE_COORD_IDENTIFIER:
            id_dict[COORD_KEY] = candidate_id.capitalize()  # capitalise!
        else:
            id_dict[JOINT_KEY] = candidate_id
    # then, return the new col name based on whether this col is side-specific,
    # central, or not a coordinate column at all
    if id_dict.keys() == {COORD_KEY, JOINT_KEY}:
        return f"{id_dict[JOINT_KEY]}{SPACE_SEP}{id_dict[COORD_KEY]}"
    elif id_dict.keys() == {SIDE_KEY, COORD_KEY, JOINT_KEY}:
        return f"{id_dict[JOINT_KEY]}{COMMA_SEP}{id_dict[SIDE_KEY]}{SPACE_SEP}{id_dict[COORD_KEY]}"
    else:
        return col_string


# NU - add property test for this
# This function is done. Have it be a separate function that users can use to clean their cols before running the main function (so if there should be 3 parts that are unnecessary, people call this function 3 times before running the main function)
# => make this be a separate button in GUI
df = pd.DataFrame(data=None, columns=["a", "a_xyz"])
replace_string = "_xyz"


def replace_strings_in_colnames(df, replace_string):
    """
    Function to remove unnecessary sub-strings in colnames prior to  batch renaming
    colnames according to Universal 3D GaitA
    """
    new_col_dict = {}
    for col in df.columns:
        if replace_string in col:
            new_col = col.replace(replace_string, "")
            new_col_dict[col] = new_col
    df.rename(columns=new_col_dict, inplace=True)
    return df


if __name__ == "__main__":
    main()

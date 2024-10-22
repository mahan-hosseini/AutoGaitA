import pandas as pd




### IMPORTANT NOTE ###
# Make sure to account for cols that do not have a side (e.g. Pelvis X) etc.




"""
Input is 3 identifiers and 2 separators which together make the full string of the original column name. Use these to rename all columns containing 3D coordinates to the naming convention required by AutoGaitA Universal 3. For that:
1. (Optional) - remove cols that have unnecessary identifier
2. Extract and store the three identifiers based on the separators.
3. Rename the columns to the new naming convention using the three identifiers
"""

# ONE COL NAME AT A TIME FOR RENAMING
# THEN GIVE NEW COL NAME TO DF
def rename_columns(root_dir, id1, id2, id3, sep1, sep2):
    new_columns = {}
    try:
        df = pd.load_excel(root_dir)
    except:
        # df = pd.read_csv(root_dir + "/Users/mahan/sciebo/Research/AutoGaitA/Human/Sebastian/Sebastians_Data_combined_xyz.csv")
        df = pd.read_csv(
            "/Users/mahan/sciebo/Research/AutoGaitA/Human/Sebastian/Sebastians_Data_combined_xyz.csv"
        )
    id_1 = "side"
    id_2 = "key_point"
    id_3 = "coordinate"
    separator = "_"


def check_if_col_needs_renaming(col_string, separator):
    if col_string.count(separator) == 2:
        return True
    return False

from typing import Dict
def extract_user_identifiers(col_string:str, separator:str): -> Dict[str, str]:
    # input and output types with : syntax und Dict[str, str]
    candidate_side_identifier = ["l", "r", "left", "right"]
    candidate_coord_identifier = ["x", "y", "z"]
    id_dict = {}
    for candidate_id in col_string.split(separator):
        if candidate_id.lower() in candidate_side_identifier:
            id_dict["side"] = candidate_id
        elif candidate_id.lower() in candidate_coord_identifier:
            id_dict["coordinate"] = candidate_id
        else:
            id_dict["key_point"] = candidate_id
    
    new_col_string = f"{id_dict["key_point"]}, {id_dict["side"]} {id_dict["coordinate"]}"

extract_user_identifiers()
def rename_one_column_string(old_string)


first make it lowercase for l/r left/right before comparing to list of valid names
valid coords
separators should be "unique", just start with underscore, in any case seperators cannot be in key point name

also use " if side identifier " in col_string to check whether we have to use rename_side_specific_col or rename_central_col (e.g. Pelvis)

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
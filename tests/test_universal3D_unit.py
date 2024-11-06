from autogaita.universal3D.universal3D_preparation import clean_a_file, rename_a_column
from hypothesis import given, strategies as st
import pandas as pd

# global constants from group gaita
ID_COL = "ID"
SC_PERCENTAGE_COL = "SC Percentage"
GROUP_COL = "Group"

# import pytest
# import pandas as pd
# from hypothesis import given, strategies as st
# from autogaita_3D_preparation import clean_a_file


# %%..............................  preparation  .......................................


# property test for removing a string from column names via clean a file
column_names = st.lists(st.text(min_size=1), min_size=1, max_size=10, unique=True)
strings_to_remove = st.text(min_size=1)


@given(df_columns=column_names, string_to_remove=strings_to_remove)
def test_clean_a_file(df_columns, string_to_remove):
    df = pd.DataFrame(columns=df_columns)
    cleaned_df = clean_a_file(df, string_to_remove)
    for col in df_columns:
        if string_to_remove in col:
            assert col.replace(string_to_remove, "") in cleaned_df.columns
        else:
            assert col in cleaned_df.columns


# Property test for renaming a given column according to 3 possible cases
candidate_side_ids = st.sampled_from(
    ["l", "L", "left", "LEFT", "Left", "r", "R", "right", "RIGHT", "Right"]
)
candidate_coord_ids = st.sampled_from(["x", "y", "z", "X", "Y", "Z"])
candidate_joint_ids = st.text(min_size=1)
separators = st.sampled_from(["_", "-", ":", "."])


@given(
    candidate_side_id=candidate_side_ids,
    candidate_coord_id=candidate_coord_ids,
    candidate_joint_id=candidate_joint_ids,
    separator=separators,
)
def test_rename_a_column(
    candidate_side_id, candidate_coord_id, candidate_joint_id, separator
):
    # only run main test below if separator is not the joint id anywhere
    # => we require separators to be unique in column strings
    if separator in candidate_joint_id:
        return
    # preparation - what output we are expecting
    expected_side = "left" if candidate_side_id.lower() in ["l", "left"] else "right"
    expected_coord = candidate_coord_id.capitalize()
    # test 1 - column is side-specific
    col_string = separator.join(
        [candidate_side_id, candidate_coord_id, candidate_joint_id]
    )
    result = rename_a_column(col_string, separator)
    assert isinstance(result, str)
    assert (
        result == f"{candidate_joint_id}, {expected_side} {expected_coord.capitalize()}"
    )
    # test 2 - column is central
    col_string = separator.join([candidate_coord_id, candidate_joint_id])
    result = rename_a_column(col_string, separator)
    assert result == f"{candidate_joint_id} {expected_coord.capitalize()}"
    # test 3 - column is not a coordinate column
    col_string = separator.join([candidate_joint_id])
    result = rename_a_column(col_string, separator)
    assert result == col_string

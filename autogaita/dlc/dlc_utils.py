from autogaita.resources.utils import try_to_run_gaita
import os
import tkinter as tk


def prepare_DLC_df(df, separator=" "):
    """Prepare the DLC dataframe after loading w.r.t. column names & df-index
    Note
    ----
    separator is used in universal3D_datafile_preparation
    """
    new_column_strings = list()  # data df
    for j in range(df.shape[1]):
        new_column_strings.append(df.iloc[0, j] + separator + df.iloc[1, j])
    df.columns = new_column_strings
    # next lines indices are because: scorer row becomes the column, bodypart row is row
    # 0, coords row is row 1 and we thus include row 2 onwards. col 1 onwards is obvious
    df = df.iloc[2:, 1:]
    df.index = range(len(df))
    df = df.astype(float)
    return df


def find_number(fullstring, prestring, poststring):
    """Find (mouse/run) number based on user-defined strings in filenames"""
    start_idx = fullstring.find(prestring) + len(prestring)
    end_idx = fullstring.find(poststring)
    return int(fullstring[start_idx:end_idx])

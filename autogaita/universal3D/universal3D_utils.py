def transform_joint_and_leg_to_colname(joint, legname, feature):
    """For Human Data: Transform a joint and leg name to Universal 3D-column name"""
    return joint + ", " + legname + " " + feature


def extract_feature_column(df, joint, legname, feature):
    """Extract the column of a given joint (or angle) x legname (or not) x feature combo

    Note
    ----
    Only use this when using .iloc, not .loc!
    ==> the return statement gives the column-index to be used with .iloc!
    """
    if joint + feature in df.columns:
        string = joint + feature
    else:
        string = transform_joint_and_leg_to_colname(joint, legname, feature)
    return df.columns.get_loc(string)

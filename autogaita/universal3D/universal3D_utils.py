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


def interpolate_xyz_nans(data):
    """Linearly interpolate NaNs in all X/Y/Z coordinate columns

    Note
    ----
    Done for all joints, not just analysed ones, because group PCA breaks on any NaN
    and users can pick any joint's coordinates as a PCA feature.
    => check_tracking_nans (stage 2) has already excluded SCs with too many NaNs
    => limit_direction="both" also fills leading/trailing NaNs - note that these are
       filled with the nearest valid value (i.e. constant), not interpolated
    """
    xyz_cols = [col for col in data.columns if col.endswith((" X", " Y", " Z"))]
    data[xyz_cols] = data[xyz_cols].interpolate(method="linear", limit_direction="both")
    return data

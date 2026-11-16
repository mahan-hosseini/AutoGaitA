# %% imports
import os
import copy
import json
import shutil
import pandas as pd

# %% constants
from autogaita.resources.constants import CONFIG_JSON_FILENAME
from autogaita.group.group_constants import (
    ORIG_SHEET_NAME,
    SPLIT_STRING,
    TRACKING_SOFTWARE_3D,
    CROSS_SPECIES_DIR_NAME,
    CROSS_SPECIES_SHEET_NAMES,
    CROSS_SPECIES_JOINT_PREFIX,
    CROSS_SPECIES_2D_COORD_SUFFIXES,
    CROSS_SPECIES_3D_COORD_SUFFIXES,
    CROSS_SPECIES_JOINT_SUFFIXES,
    CROSS_SPECIES_ANGLE_SUFFIXES,
    CROSS_SPECIES_3D_SIDES,
    CROSS_SPECIES_CFG_JOINT_LIST_KEYS,
    CROSS_SPECIES_CFG_JOINT_STRING_KEYS,
)

SHEET_FILE_EXTENSIONS = [".xlsx", ".csv"]

# %% ..........................  cross species preparation  ............................

# WHAT THIS DOES
# --------------
# Cross-species comparisons require all groups to share joint names. Users define
# species_joints = {species: [joint names]}, where list idx 0 is the most distal joint
# and all lists have the same length. For each group dir we:
# 1) identify which species the group is (all its joints have to be in the data)
# 2) rename each species joint (and angles at it) to Joint1, Joint2, ... & drop columns
#    of unmapped joints so that all groups have identical columns
# 3) save renamed sheet files and a translated config.json copy to
#    <group_dir>/Cross Species Columns/, which users then use as group dirs
# => The config.json copy is required because group analysis reads joints (and checks
#    first-level cfg vars for equivalence) from <group_dir>/config.json.
# => Nothing is written before all groups were identified successfully.


def prepare_cross_species_columns(group_names, group_dirs, species_joints):
    """Rename species-specific joint columns of all groups to Joint1, Joint2, ...

    Parameters
    ----------
    group_names : list of str
    group_dirs : list of str
        First-level Results folders (the ones that contain config.json)
    species_joints : dict
        {species: [joint names]} - idx 0 is the most distal joint. All lists must have
        the same length.

    Returns
    -------
    report : list of dict
        One dict per group with keys "group_name", "species", "ID_count" & "output_dir"

    Raises
    ------
    ValueError
        If species_joints is invalid or any group could not be identified as exactly
        one species. Nothing is written in that case.
    """
    species_joints = validate_species_joints(species_joints)

    # ..........  1 - load configs & identify species of all groups (no writing)  ......
    first_level_cfgs = [
        load_first_level_cfg(group_name, group_dir)
        for group_name, group_dir in zip(group_names, group_dirs)
    ]
    is_3D = check_tracking_software_dimensions(group_names, first_level_cfgs)
    group_species = []
    group_ID_folders = []
    for group_name, group_dir in zip(group_names, group_dirs):
        ID_folders = find_ID_folders(group_dir)
        if not ID_folders:
            raise ValueError(
                f"No valid first-level results found for group {group_name} at:\n"
                + group_dir
            )
        species_of_IDs = {}
        for ID_folder in ID_folders:
            columns = load_original_sheet_columns(group_dir, ID_folder)
            species_of_IDs[ID_folder] = identify_species(
                columns,
                species_joints,
                is_3D,
                data_label=f"Group {group_name} - {ID_folder}",
            )
        if len(set(species_of_IDs.values())) > 1:
            species_listing = "\n".join(
                f"{ID_folder}: {species}"
                for ID_folder, species in species_of_IDs.items()
            )
            raise ValueError(
                f"IDs of group {group_name} were identified as different species!\n"
                + "All IDs of a group must be the same species.\n\n"
                + species_listing
            )
        group_species.append(next(iter(species_of_IDs.values())))
        group_ID_folders.append(ID_folders)

    # ..................  2 - write renamed sheets & translated config  ................
    report = []
    for g, (group_name, group_dir) in enumerate(zip(group_names, group_dirs)):
        joints = species_joints[group_species[g]]
        angles = first_level_cfgs[g].get("angles")
        output_dir = os.path.join(group_dir, CROSS_SPECIES_DIR_NAME)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)  # our own output - replace it
        os.makedirs(output_dir)
        for ID_folder in group_ID_folders[g]:
            os.makedirs(os.path.join(output_dir, ID_folder))
            for sheet_name in CROSS_SPECIES_SHEET_NAMES:
                for extension in SHEET_FILE_EXTENSIONS:
                    file_name = ID_folder + SPLIT_STRING + sheet_name + extension
                    input_path = os.path.join(group_dir, ID_folder, file_name)
                    if os.path.exists(input_path):
                        rename_sheet_file(
                            input_path,
                            os.path.join(output_dir, ID_folder, file_name),
                            joints,
                            angles,
                            is_3D,
                        )
        translated_cfg = translate_first_level_cfg(first_level_cfgs[g], joints)
        with open(os.path.join(output_dir, CONFIG_JSON_FILENAME), "w") as config_file:
            json.dump(translated_cfg, config_file, indent=4)
        report.append(
            {
                "group_name": group_name,
                "species": group_species[g],
                "ID_count": len(group_ID_folders[g]),
                "output_dir": output_dir,
            }
        )
    print(cross_species_report_to_string(report))
    return report


def cross_species_report_to_string(report):
    """Human-readable summary of prepare_cross_species_columns' report"""
    lines = []
    for entry in report:
        lines.append(
            f"Group {entry['group_name']} - identified as {entry['species']} "
            + f"({entry['ID_count']} files)"  # files not necessarily (diff.) animals!
        )
        lines.append(f"    Saved to: {entry['output_dir']}")
    return "\n".join(lines)


# %% ...............................  pure functions  ..................................


def validate_species_joints(species_joints):
    """Strip whitespace, skip blank species & check that the joint lists are valid"""
    clean_species_joints = {}
    for species, joints in species_joints.items():
        species = str(species).strip()
        joints = [str(joint).strip() for joint in joints]
        if not species and not any(joints):
            continue  # blank row
        if not species:
            raise ValueError(
                "A species name is empty! Joints were: " + ", ".join(joints)
            )
        if not joints or not all(joints):
            raise ValueError(f"Species {species} has empty joint names!")
        duplicate_joints = sorted(
            {joint for joint in joints if joints.count(joint) > 1}
        )
        if duplicate_joints:
            raise ValueError(
                f"Species {species} lists these joints more than once: "
                + ", ".join(duplicate_joints)
            )
        clean_species_joints[species] = joints
    joint_counts = {species: len(j) for species, j in clean_species_joints.items()}
    if len(set(joint_counts.values())) > 1:
        raise ValueError(
            "All species need the same number of joints!\n"
            + "\n".join(f"{species}: {n}" for species, n in joint_counts.items())
        )
    return clean_species_joints


def build_column_map(columns, joints, angles, is_3D):
    """Return a rename dict & a list of columns to drop

    Notes
    -----
    => Columns are renamed only on exact matches of joint + side + " " + suffix, so a
       joint "Tail" never touches "Tail base x".
    => Angle columns are renamed if the angle's name, lower & upper joints are mapped.
    => All other joint/angle columns (unmapped joints) are dropped so all groups have
       identical columns. Columns without a joint suffix (e.g. Time) are kept.
    """
    new_names = new_joint_names(joints)
    mapped_angles = mapped_angle_names(angles, new_names)
    if is_3D:
        sides = CROSS_SPECIES_3D_SIDES
        coord_suffixes = CROSS_SPECIES_3D_COORD_SUFFIXES
    else:
        sides = [""]
        coord_suffixes = CROSS_SPECIES_2D_COORD_SUFFIXES
    joint_suffixes = coord_suffixes + CROSS_SPECIES_JOINT_SUFFIXES
    candidates = {}
    for joint, new_name in new_names.items():
        suffixes = joint_suffixes
        if joint in mapped_angles:
            suffixes = joint_suffixes + CROSS_SPECIES_ANGLE_SUFFIXES
        for side in sides:
            for suffix in suffixes:
                candidates[f"{joint}{side} {suffix}"] = f"{new_name}{side} {suffix}"
    all_suffixes = joint_suffixes + CROSS_SPECIES_ANGLE_SUFFIXES
    rename_dict = {}
    drop_list = []
    for column in columns:
        if column in candidates:
            rename_dict[column] = candidates[column]
        elif any(column.endswith(" " + suffix) for suffix in all_suffixes):
            drop_list.append(column)
    return rename_dict, drop_list


def identify_species(columns, species_joints, is_3D, data_label=""):
    """Return the one species whose joints all have coordinate columns in columns"""
    if not species_joints:
        raise ValueError("You did not define any species & joints!")
    columns = set(columns)
    if is_3D:
        sides = CROSS_SPECIES_3D_SIDES
        coord_suffixes = CROSS_SPECIES_3D_COORD_SUFFIXES
    else:
        sides = [""]
        coord_suffixes = CROSS_SPECIES_2D_COORD_SUFFIXES
    matches = []
    missing_joints = {}
    for species, joints in species_joints.items():
        missing_joints[species] = [
            joint
            for joint in joints
            if not any(
                f"{joint}{side} {suffix}" in columns
                for side in sides
                for suffix in coord_suffixes
            )
        ]
        if not missing_joints[species]:
            matches.append(species)
    if len(matches) == 1:
        return matches[0]
    if not matches:
        missing_listing = "\n".join(
            f"{species} - missing: {', '.join(missing)}"
            for species, missing in missing_joints.items()
        )
        raise ValueError(
            f"{data_label}\nCould not be identified as any species - not all joints "
            + "of any species were found in the data.\n\n"
            + missing_listing
        )
    raise ValueError(
        f"{data_label}\nMatches more than one species: {', '.join(matches)}\n"
        + "Make sure each species' joint list contains at least one joint that is "
        + "unique to it."
    )


def translate_first_level_cfg(first_level_cfg, joints):
    """Copy of a first-level config.json dict with joint names replaced by Joint1, ...

    Notes
    -----
    => Joint lists & angles keep only mapped entries & are sorted by Joint index so the
       equivalence check of group analysis does not fail due to ordering.
    => The trailing-space convention of joint names is kept ("Ankle " -> "Joint2 ").
    => Unmapped standardisation joints are left unchanged.
    """
    new_names = new_joint_names(joints)
    translated_cfg = copy.deepcopy(first_level_cfg)
    for key in CROSS_SPECIES_CFG_JOINT_LIST_KEYS:
        if key in translated_cfg:
            mapped = [j for j in translated_cfg[key] if j.strip() in new_names]
            mapped.sort(key=lambda joint: joints.index(joint.strip()))
            translated_cfg[key] = [translate_joint_name(j, new_names) for j in mapped]
    for key in CROSS_SPECIES_CFG_JOINT_STRING_KEYS:
        value = translated_cfg.get(key)
        if isinstance(value, str) and value.strip() in new_names:
            translated_cfg[key] = translate_joint_name(translated_cfg[key], new_names)
    if translated_cfg.get("angles"):
        angles = translated_cfg["angles"]
        mapped_idxs = [
            i
            for i in range(len(angles["name"]))
            if all(angles[key][i].strip() in new_names for key in angles)
        ]
        mapped_idxs.sort(key=lambda i: joints.index(angles["name"][i].strip()))
        translated_cfg["angles"] = {
            key: [translate_joint_name(angles[key][i], new_names) for i in mapped_idxs]
            for key in angles
        }
    return translated_cfg


def new_joint_names(joints):
    """{species joint: Joint1, ...} - idx 0 is the most distal joint"""
    return {
        joint: CROSS_SPECIES_JOINT_PREFIX + str(i + 1) for i, joint in enumerate(joints)
    }


def mapped_angle_names(angles, new_names):
    """Names (stripped) of angles whose name, lower & upper joints are all mapped"""
    if not angles:
        return set()
    return {
        angles["name"][i].strip()
        for i in range(len(angles["name"]))
        if all(angles[key][i].strip() in new_names for key in angles)
    }


def translate_joint_name(joint, new_names):
    """Translate one joint name, keeping a trailing space if there was one"""
    new_name = new_names[joint.strip()]
    if joint.endswith(" "):
        return new_name + " "
    return new_name


# %% ................................  file helpers  ...................................


def load_first_level_cfg(group_name, group_dir):
    """Load a group dir's first-level config.json"""
    if os.path.basename(os.path.normpath(group_dir)) == CROSS_SPECIES_DIR_NAME:
        raise ValueError(
            f"The directory of group {group_name} already is a {CROSS_SPECIES_DIR_NAME}"
            + " folder!\nChoose the first-level Results folder instead:\n"
            + group_dir
        )
    config_path = os.path.join(group_dir, CONFIG_JSON_FILENAME)
    if not os.path.isfile(config_path):
        raise ValueError(
            f"No {CONFIG_JSON_FILENAME} found for group {group_name} at:\n" + group_dir
        )
    with open(config_path, "r") as config_file:
        return json.load(config_file)


def check_tracking_software_dimensions(group_names, first_level_cfgs):
    """Return is_3D & raise if 2D (DLC/SLEAP) & Universal 3D groups are mixed"""
    is_3D = [
        first_level_cfg["tracking_software"] in TRACKING_SOFTWARE_3D
        for first_level_cfg in first_level_cfgs
    ]
    if len(set(is_3D)) > 1:
        software_listing = "\n".join(
            f"{group_name}: {first_level_cfg['tracking_software']}"
            for group_name, first_level_cfg in zip(group_names, first_level_cfgs)
        )
        raise ValueError(
            "Universal 3D results cannot be compared with DLC or SLEAP results!\n\n"
            + software_listing
        )
    return is_3D[0]


def find_ID_folders(group_dir):
    """ID folders are those containing an Original Stepcycles sheet file"""
    ID_folders = []
    for folder in sorted(os.listdir(group_dir)):
        if folder == CROSS_SPECIES_DIR_NAME:
            continue
        if any(
            os.path.exists(
                os.path.join(
                    group_dir, folder, folder + SPLIT_STRING + ORIG_SHEET_NAME + ext
                )
            )
            for ext in SHEET_FILE_EXTENSIONS
        ):
            ID_folders.append(folder)
    return ID_folders


def load_original_sheet_columns(group_dir, ID_folder):
    """Column names of an ID's Original Stepcycles sheet file (all xlsx sheets)"""
    base_path = os.path.join(
        group_dir, ID_folder, ID_folder + SPLIT_STRING + ORIG_SHEET_NAME
    )
    if os.path.exists(base_path + ".xlsx"):
        sheets = pd.read_excel(base_path + ".xlsx", sheet_name=None, nrows=0)
        columns = []
        for sheet in sheets.values():
            columns.extend(sheet.columns)
        return columns
    return list(pd.read_csv(base_path + ".csv", nrows=0).columns)


def rename_sheet_file(input_path, output_path, joints, angles, is_3D):
    """Load a sheet file, rename & drop its columns and save it in the same format"""
    if input_path.endswith(".csv"):
        df = pd.read_csv(input_path)
        rename_df_columns(df, joints, angles, is_3D).to_csv(output_path, index=False)
    else:  # xlsx - keep all sheets (Universal 3D has left/right/both)
        sheets = pd.read_excel(input_path, sheet_name=None)
        with pd.ExcelWriter(output_path) as writer:
            for sheet_name, df in sheets.items():
                rename_df_columns(df, joints, angles, is_3D).to_excel(
                    writer, sheet_name=sheet_name, index=False
                )


def rename_df_columns(df, joints, angles, is_3D):
    """Apply build_column_map to a df"""
    rename_dict, drop_list = build_column_map(df.columns, joints, angles, is_3D)
    return df.drop(columns=drop_list).rename(columns=rename_dict)

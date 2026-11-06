from autogaita.gui.gaita_widgets import find_browse_start_dir

DEFAULT_DIR = "/default/dir"


def test_existing_folder_is_returned(tmp_path):
    assert find_browse_start_dir([str(tmp_path)], DEFAULT_DIR) == str(tmp_path)


def test_existing_file_returns_its_folder(tmp_path):
    excel_file = tmp_path / "annotation_table.xlsx"
    excel_file.touch()
    assert find_browse_start_dir([str(excel_file)], DEFAULT_DIR) == str(tmp_path)


def test_missing_file_in_existing_folder_returns_that_folder(tmp_path):
    missing_file = tmp_path / "annotation_table.xlsx"
    assert find_browse_start_dir([str(missing_file)], DEFAULT_DIR) == str(tmp_path)


def test_empty_path_returns_default():
    assert find_browse_start_dir([""], DEFAULT_DIR) == DEFAULT_DIR


def test_bare_filename_returns_default():
    assert find_browse_start_dir(["annotation_table.xlsx"], DEFAULT_DIR) == DEFAULT_DIR


def test_path_without_existing_parent_returns_default(tmp_path):
    missing_path = tmp_path / "missing_folder" / "annotation_table.xlsx"
    assert find_browse_start_dir([str(missing_path)], DEFAULT_DIR) == DEFAULT_DIR


def test_surrounding_spaces_are_ignored(tmp_path):
    assert find_browse_start_dir([f"  {tmp_path} "], DEFAULT_DIR) == str(tmp_path)


def test_first_valid_candidate_wins(tmp_path):
    """The annotation table button lists root_dir first, so root_dir must win."""
    root_dir = tmp_path / "root_dir"
    entry_dir = tmp_path / "entry_dir"
    root_dir.mkdir()
    entry_dir.mkdir()
    candidate_paths = [str(root_dir), str(entry_dir)]
    assert find_browse_start_dir(candidate_paths, DEFAULT_DIR) == str(root_dir)


def test_empty_first_candidate_falls_through_to_second(tmp_path):
    assert find_browse_start_dir(["", str(tmp_path)], DEFAULT_DIR) == str(tmp_path)

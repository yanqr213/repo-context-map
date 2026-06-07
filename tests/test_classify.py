from repo_context_map.classify import detect_language, infer_directory_role, infer_file_role, is_entry_point


def test_detect_language_from_suffix_and_name():
    assert detect_language("src/app.py") == "Python"
    assert detect_language("package.json") == "JavaScript"
    assert detect_language("unknown.asset") == "Other"


def test_infer_file_roles():
    assert infer_file_role("tests/test_app.py") == "tests"
    assert infer_file_role("docs/guide.md") == "docs"
    assert infer_file_role("src/app.py") == "source"


def test_infer_directory_roles():
    assert infer_directory_role("src") == "source"
    assert infer_directory_role(".github/workflows") == "project"
    assert infer_directory_role("tests") == "tests"


def test_entry_point_detection():
    assert is_entry_point("src/demo/cli.py")
    assert is_entry_point("src/main.rs")

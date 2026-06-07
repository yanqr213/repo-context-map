from repo_context_map.ignore import IgnoreMatcher


def test_ignore_matches_directory_patterns():
    matcher = IgnoreMatcher(["build/", "*.log"])
    assert matcher.ignores("build/app.js", is_dir=False)
    assert matcher.ignores("debug.log", is_dir=False)
    assert not matcher.ignores("src/app.py", is_dir=False)


def test_ignore_negation_restores_file():
    matcher = IgnoreMatcher(["*.md", "!README.md"])
    assert not matcher.ignores("README.md", is_dir=False)
    assert matcher.ignores("docs/notes.md", is_dir=False)

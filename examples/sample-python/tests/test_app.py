from sample_service import greet


def test_greet_name():
    assert greet("Ada") == "hello, Ada"

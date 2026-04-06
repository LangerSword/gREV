from parser import get_user_data


def test_get_user_data_returns_string():
    assert type(get_user_data()) is str

# test_fetcher.py
import pytest

# BUG: Import mismatch! The function was renamed to fetch_api_data in fetcher.py
from fetcher import get_data

def test_valid_endpoint():
    # The test is also calling the old, incorrect function name
    result = get_data("/users/list")
    assert result == "Successfully fetched data from /users/list"

def test_empty_endpoint():
    with pytest.raises(ValueError):
        get_data("")

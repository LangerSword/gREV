from fetcher import fetch_data


def test_fetch_data_runs():
    status_code = fetch_data()
    assert status_code == 200

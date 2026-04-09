import pytest
from data_processor import (
    parse_csv,
    calculate_average,
    filter_above_threshold,
    get_column,
    summarize_data,
)


# ── parse_csv tests ──────────────────────────────────────────

def test_parse_csv_single_row():
    assert parse_csv("a,b,c") == [["a", "b", "c"]]

def test_parse_csv_multiple_rows():
    raw = "1,2,3\n4,5,6"
    result = parse_csv(raw)
    assert result == [["1", "2", "3"], ["4", "5", "6"]]

def test_parse_csv_handles_whitespace():
    raw = "  x,y,z  "
    result = parse_csv(raw)
    assert len(result) == 1
    assert len(result[0]) == 3


# ── calculate_average tests ──────────────────────────────────

def test_average_basic():
    assert calculate_average([10.0, 20.0, 30.0]) == 20.0

def test_average_single():
    assert calculate_average([42.0]) == 42.0

def test_average_empty():
    assert calculate_average([]) == 0.0


# ── filter_above_threshold tests ─────────────────────────────

def test_filter_above_basic():
    result = filter_above_threshold([1.0, 5.0, 10.0, 15.0], 7.0)
    assert result == [10.0, 15.0]

def test_filter_above_none_qualify():
    result = filter_above_threshold([1.0, 2.0, 3.0], 100.0)
    assert result == []

def test_filter_above_all_qualify():
    result = filter_above_threshold([50.0, 60.0, 70.0], 10.0)
    assert result == [50.0, 60.0, 70.0]


# ── get_column tests ─────────────────────────────────────────

def test_get_column_first():
    rows = [["a", "b", "c"], ["d", "e", "f"]]
    assert get_column(rows, 0) == ["a", "d"]

def test_get_column_out_of_range():
    rows = [["a", "b"], ["c"]]
    # column index 1 is out of range for second row
    assert get_column(rows, 1) == ["b"]


# ── summarize_data integration tests ─────────────────────────

def test_summarize_basic():
    raw = "10,20,30\n40,50,60"
    result = summarize_data(raw, 1, 25.0)
    assert result["count"] == 2
    assert result["average"] == 35.0
    assert result["above_threshold"] == 1

def test_summarize_no_above_threshold():
    raw = "1,2,3\n4,5,6"
    result = summarize_data(raw, 0, 100.0)
    assert result["count"] == 2
    assert result["above_threshold"] == 0

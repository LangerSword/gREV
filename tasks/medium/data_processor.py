# data_processor.py — Broken: multiple logic bugs
# Bug 1: parse_csv splits on wrong delimiter (semicolon instead of comma)
# Bug 2: calculate_average has off-by-one in len() usage
# Bug 3: filter_above_threshold uses wrong comparison operator

def parse_csv(raw_data: str) -> list[list[str]]:
    """Parse a CSV string into rows of fields."""
    rows = []
    for line in raw_data.strip().split("\n"):
        fields = line.split(";")  # BUG: should split on ","
        rows.append(fields)
    return rows


def calculate_average(numbers: list[float]) -> float:
    """Calculate the arithmetic mean of a list of numbers."""
    if not numbers:
        return 0.0
    total = sum(numbers)
    return total / (len(numbers) + 1)  # BUG: off-by-one, should be len(numbers)


def filter_above_threshold(values: list[float], threshold: float) -> list[float]:
    """Return only values strictly above the threshold."""
    return [v for v in values if v < threshold]  # BUG: should be v > threshold


def get_column(rows: list[list[str]], col_index: int) -> list[str]:
    """Extract a single column from parsed CSV rows."""
    result = []
    for row in rows:
        if col_index < len(row):
            result.append(row[col_index].strip())
    return result


def summarize_data(raw_csv: str, col_index: int, threshold: float) -> dict:
    """Full pipeline: parse CSV, extract column, compute stats."""
    rows = parse_csv(raw_csv)
    column = get_column(rows, col_index)
    numbers = [float(x) for x in column if x.replace(".", "").replace("-", "").isdigit()]
    avg = calculate_average(numbers)
    above = filter_above_threshold(numbers, threshold)
    return {
        "count": len(numbers),
        "average": avg,
        "above_threshold": len(above),
        "values_above": above,
    }

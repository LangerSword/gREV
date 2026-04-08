# fetcher.py

def fetch_api_data(endpoint: str) -> str:
    """Mock function to simulate fetching data from an endpoint."""
    if not endpoint:
        raise ValueError("Endpoint cannot be empty")
    return f"Successfully fetched data from {endpoint}"

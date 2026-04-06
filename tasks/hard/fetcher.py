import requests


def fetch_data():
    response = requests.get("https://httpbin.org/get", timeout=10)
    return response.status_code

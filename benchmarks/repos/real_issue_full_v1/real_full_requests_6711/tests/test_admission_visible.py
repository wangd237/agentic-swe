import requests


def test_signed_https_path_keeps_leading_double_slash():
    prepared = requests.Request("GET", "https://bucket.example//object.txt").prepare()
    adapter = requests.adapters.HTTPAdapter()
    assert adapter.request_url(prepared, {}) == "//object.txt"

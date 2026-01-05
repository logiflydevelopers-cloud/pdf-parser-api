import requests

def download_pdf(source: dict) -> bytes:
    if source["type"] == "url":
        r = requests.get(source["url"], timeout=30)
        r.raise_for_status()
        return r.content
    raise ValueError("Unsupported source type")

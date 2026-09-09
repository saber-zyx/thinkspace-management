import re
import urllib.error
import urllib.request
from typing import Optional


def extract_sheet_id_and_gid(url: str) -> tuple[Optional[str], str]:
    match_id = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    sheet_id = match_id.group(1) if match_id else None

    match_gid = re.search(r"gid=([0-9]+)", url)
    gid = match_gid.group(1) if match_gid else "0"

    return sheet_id, gid


def _download_csv(url: str) -> str:
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

    with urllib.request.urlopen(req, timeout=20) as response:
        if response.status == 200:
            return response.read().decode("utf-8")
        raise Exception(f"Khong the tai Sheet. HTTP Status: {response.status}")


def fetch_public_sheet_as_csv(url: str) -> str:
    """
    Download a public Google Sheet as CSV.

    Some shared Sheets, especially Excel-origin links with rtpof/sd query
    params, return HTTP 400 from /export but still work through gviz CSV.
    """
    sheet_id, gid = extract_sheet_id_and_gid(url)
    if not sheet_id:
        raise ValueError("URL Google Sheet khong hop le hoac khong tim thay ID.")

    csv_export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    csv_gviz_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"

    first_error: Exception | None = None
    for csv_url in (csv_export_url, csv_gviz_url):
        try:
            return _download_csv(csv_url)
        except urllib.error.HTTPError as error:
            first_error = error
            if error.code in {401, 403}:
                continue
        except Exception as error:
            first_error = error

    if isinstance(first_error, urllib.error.HTTPError) and first_error.code in {401, 403}:
        raise PermissionError(
            "Khong co quyen truy cap Google Sheet. Hay bat quyen Anyone with the link can view."
        )

    raise Exception(f"Loi khi ket noi Google Sheet: {str(first_error)}")

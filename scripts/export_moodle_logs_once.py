from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urljoin


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INCOMING_DIR = PROJECT_ROOT / "data" / "incoming" / "moodle_logs"
ARCHIVE_DIR = PROJECT_ROOT / "data" / "archive" / "moodle_logs"
FAILED_DIR = PROJECT_ROOT / "data" / "failed" / "moodle_logs"
DEBUG_DIR = PROJECT_ROOT / "data" / "debug" / "moodle_logs"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Thiếu biến môi trường {name}. Hãy điền trong file .env.")
    return value


def bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "y"}


def build_logs_url(base_url: str, logs_path: str, course_id: str) -> str:
    query = urlencode({"id": course_id})
    return f"{urljoin(base_url.rstrip('/') + '/', logs_path.lstrip('/'))}?{query}"


def build_import_url(base_url: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", "api/v1/moodle-logs/import-csv")


def click_first_download_link(page, export_format: str) -> None:
    candidates = [
        "button:has-text('Download')",
        "button:has-text('Tải xuống')",
        "input[type='submit'][value*='Download']",
        "input[type='submit'][value*='Tải']",
        f"a:has-text('{export_format.upper()}')",
        f"a:has-text('{export_format.lower()}')",
        "a:has-text('Download')",
        "a:has-text('Tải xuống')",
    ]
    for selector in candidates:
        locator = page.locator(selector)
        if locator.count() > 0:
            locator.first.click()
            return
    raise RuntimeError("Không tìm thấy nút/link download log trên trang Moodle.")


def submit_log_filter(page) -> None:
    candidates = [
        "input[type='submit'][value='Get these logs']",
        "input[type='submit'][value*='Get these logs']",
        "button:has-text('Get these logs')",
        "input[type='submit'][value*='Lấy']",
        "button:has-text('Lấy')",
        "input[type='submit'][value*='Xem']",
        "button:has-text('Xem')",
    ]
    for selector in candidates:
        locator = page.locator(selector)
        if locator.count() > 0:
            locator.first.click()
            page.wait_for_load_state("networkidle", timeout=60_000)
            return
    raise RuntimeError("Không tìm thấy nút lấy logs trên trang filter Moodle.")


def run_export() -> Path:
    load_dotenv(PROJECT_ROOT / ".env")

    base_url = require_env("MOODLE_UI_BASE_URL")
    username = require_env("MOODLE_UI_USERNAME")
    password = require_env("MOODLE_UI_PASSWORD")
    course_id = require_env("MOODLE_LOG_COURSE_ID")
    login_path = os.getenv("MOODLE_UI_LOGIN_PATH", "/login/index.php").strip()
    logs_path = os.getenv("MOODLE_LOGS_PATH", "/report/log/index.php").strip()
    export_format = os.getenv("MOODLE_LOG_EXPORT_FORMAT", "csv").strip().lower()
    headless = bool_env("MOODLE_LOG_EXPORT_HEADLESS", True)

    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Chưa cài Playwright. Hãy chạy: pip install -r requirements-data.txt; python -m playwright install chromium"
        ) from exc

    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    FAILED_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    logs_url = build_logs_url(base_url, logs_path, course_id)
    login_url = urljoin(base_url.rstrip("/") + "/", login_path.lstrip("/"))

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        try:
            page.goto(login_url, wait_until="domcontentloaded", timeout=60_000)
            page.locator("input[name='username']").fill(username)
            page.locator("input[name='password']").fill(password)
            page.locator("button[type='submit'], input[type='submit']").first.click()
            page.wait_for_load_state("networkidle", timeout=60_000)

            page.goto(logs_url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_load_state("networkidle", timeout=60_000)
            submit_log_filter(page)

            with page.expect_download(timeout=60_000) as download_info:
                click_first_download_link(page, export_format)

            download = download_info.value
            suggested_name = download.suggested_filename or f"moodle_logs_{timestamp}.{export_format}"
            suffix = Path(suggested_name).suffix or f".{export_format}"
            target_path = INCOMING_DIR / f"moodle_logs_course_{course_id}_{timestamp}{suffix}"
            download.save_as(target_path)
            return target_path
        except PlaywrightTimeoutError as exc:
            screenshot_path = DEBUG_DIR / f"export_timeout_{timestamp}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            raise RuntimeError(f"Timeout khi thao tác Moodle UI. Đã lưu screenshot debug: {screenshot_path}") from exc
        except Exception:
            screenshot_path = DEBUG_DIR / f"export_error_{timestamp}.png"
            html_path = DEBUG_DIR / f"export_error_{timestamp}.html"
            try:
                page.screenshot(path=screenshot_path, full_page=True)
                html_path.write_text(page.content(), encoding="utf-8")
            except Exception:
                pass
            raise
        finally:
            context.close()
            browser.close()


def import_exported_file(file_path: Path) -> dict:
    try:
        import requests
    except ModuleNotFoundError as exc:
        raise RuntimeError("Chưa cài requests. Hãy chạy: pip install -r requirements-data.txt") from exc

    app_base_url = os.getenv("THINKSPACE_APP_BASE_URL", "http://localhost:8080").strip()
    import_url = build_import_url(app_base_url)

    with file_path.open("rb") as file_handle:
        response = requests.post(
            import_url,
            files={"file": (file_path.name, file_handle, "text/csv")},
            timeout=120,
        )

    if response.status_code >= 400:
        raise RuntimeError(f"API import trả lỗi HTTP {response.status_code}: {response.text[:500]}")

    payload = response.json()
    if payload.get("status") != "success":
        raise RuntimeError(f"API import không thành công: {payload}")
    return payload.get("data", {})


def move_to_directory(file_path: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / file_path.name
    if target_path.exists():
        stem = file_path.stem
        suffix = file_path.suffix
        target_path = target_dir / f"{stem}_{datetime.now().strftime('%H%M%S')}{suffix}"
    shutil.move(str(file_path), str(target_path))
    return target_path


def main() -> int:
    try:
        load_dotenv(PROJECT_ROOT / ".env")
        exported_path = run_export()
    except Exception as exc:
        print(f"Export that bai: {exc}", file=sys.stderr)
        return 1

    print(f"Đã tải Moodle logs về: {exported_path}")

    if not bool_env("MOODLE_LOG_AUTO_IMPORT", True):
        print("Bỏ qua bước import vì MOODLE_LOG_AUTO_IMPORT=false.")
        return 0

    try:
        report = import_exported_file(exported_path)
        archived_path = move_to_directory(exported_path, ARCHIVE_DIR)
    except Exception as exc:
        failed_path = move_to_directory(exported_path, FAILED_DIR)
        print(f"Import thất bại: {exc}", file=sys.stderr)
        print(f"Đã chuyển file lỗi sang: {failed_path}", file=sys.stderr)
        return 1

    print(f"Import thành công. Đã chuyển file sang: {archived_path}")
    print(
        "Report: "
        f"row_count={report.get('row_count')}, "
        f"inserted_count={report.get('inserted_count')}, "
        f"duplicate_count={report.get('duplicate_count')}, "
        f"failed_count={report.get('failed_count')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

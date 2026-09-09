import csv
import io
import re
import unicodedata
from typing import List, Tuple

from pydantic import ValidationError

from src.app.integrations.google_sheets import fetch_public_sheet_as_csv
from src.app.models.member import Member


def normalize_header(value: object) -> str:
    text = str(value or "").replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text).lower()
    return " ".join(text.split())


def clean_optional(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    if normalize_header(cleaned) in {"x", "na", "n a", "none", "khong", "khong co"}:
        return None

    return cleaned


def looks_like_member_header(value: str) -> bool:
    normalized = normalize_header(value)
    header_tokens = (
        "full name",
        "ho va ten",
        "first name",
        "email",
        "phone",
        "so dien thoai",
        "ngay sinh",
        "gioi tinh",
        "dia chi",
        "thuong tru",
        "ten truong",
        "role",
        "mssv",
        "khoa lop",
        "nganh hoc",
        "ghi chu",
    )
    return any(token in normalized for token in header_tokens)


def split_full_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[-1], " ".join(parts[:-1])


def get_col(row: list[str], idx: int | None) -> str | None:
    if idx is None or len(row) <= idx:
        return None
    value = row[idx].strip()
    return value if value else None


def find_first_matching_header(rows: list[list[str]], *needles: str) -> int | None:
    normalized_needles = [normalize_header(needle) for needle in needles]
    for row in rows:
        for idx, value in enumerate(row):
            header = normalize_header(value)
            if header and all(needle in header for needle in normalized_needles):
                return idx
    return None


def find_header_row_index(rows: list[list[str]]) -> int | None:
    for row_idx, row in enumerate(rows[:6]):
        normalized_cells = [normalize_header(value) for value in row]
        has_email = any("email" in cell for cell in normalized_cells)
        has_full_name = any("full name" in cell or cell.startswith("ho va ten") for cell in normalized_cells)
        has_first_name = any("first name" in cell for cell in normalized_cells)
        if has_email and (has_full_name or has_first_name):
            return row_idx
    return None


def find_member_columns(rows: list[list[str]], header_row_index: int) -> dict[str, int | None]:
    header_rows = rows[header_row_index:header_row_index + 2]

    full_name_idx = find_first_matching_header(header_rows, "full name")
    if full_name_idx is None:
        full_name_idx = find_first_matching_header(header_rows, "ho va ten")
        last_middle_idx = find_first_matching_header(header_rows, "ho va ten dem")
        if full_name_idx == last_middle_idx:
            full_name_idx = None

    return {
        "full_name": full_name_idx,
        "first_name": find_first_matching_header(header_rows, "first name"),
        "last_name": find_first_matching_header(header_rows, "last middle name")
        or find_first_matching_header(header_rows, "ho va ten dem"),
        "phone": find_first_matching_header(header_rows, "phone")
        or find_first_matching_header(header_rows, "so dien thoai"),
        "email": find_first_matching_header(header_rows, "email"),
        "school": find_first_matching_header(header_rows, "ten truong")
        or find_first_matching_header(header_rows, "school"),
        "role": find_first_matching_header(header_rows, "role"),
        "student_id": find_first_matching_header(header_rows, "mssv"),
        "class_name": find_first_matching_header(header_rows, "khoa lop"),
        "major": find_first_matching_header(header_rows, "nganh hoc"),
    }


def extract_team_name(rows: list[list[str]]) -> str:
    for row in rows[:3]:
        for value in row:
            normalized = normalize_header(value)
            if normalized.endswith(" email") and normalized != "email":
                candidate = re.sub(r"\s+email\s*$", "", str(value).strip(), flags=re.IGNORECASE)
                candidate = clean_optional(candidate)
                if candidate and not looks_like_member_header(candidate):
                    return candidate

    for row in rows[:4]:
        for idx, value in enumerate(row):
            header = normalize_header(value)
            if "ten du an" in header or "project name" in header:
                for candidate in row[idx + 1:]:
                    team_name = clean_optional(candidate)
                    if team_name and not looks_like_member_header(team_name):
                        return team_name

    return "Team Khong Ten"


def parse_member_list_from_csv(csv_content: str) -> Tuple[str, List[Member], List[str]]:
    """
    Parse a team member Google Sheet exported as CSV.

    Supported member-sheet layouts:
    - Split-name template: first name, last/middle name, phone, email.
    - Full-name template: full name, email, phone.
    """
    members: list[Member] = []
    errors: list[str] = []

    reader = list(csv.reader(io.StringIO(csv_content)))
    team_name = extract_team_name(reader)

    if not reader:
        return team_name, [], ["File Sheet khong co du lieu thanh vien."]

    header_row_index = find_header_row_index(reader)
    if header_row_index is None:
        return team_name, [], ["File Sheet khong tim thay dong header thanh vien."]

    columns = find_member_columns(reader, header_row_index)
    email_idx = columns["email"]

    if email_idx is None:
        return team_name, [], ["File Sheet khong tim thay cot Email."]

    start_row_index = header_row_index + 1

    for row_idx in range(start_row_index, len(reader)):
        row = reader[row_idx]

        if not row or all(not cell.strip() for cell in row):
            continue

        full_name = get_col(row, columns["full_name"])
        if full_name:
            first_name, last_name = split_full_name(full_name)
        else:
            first_name = get_col(row, columns["first_name"]) or ""
            last_name = get_col(row, columns["last_name"]) or ""

        email = get_col(row, email_idx) or ""

        if not first_name and not last_name and not email:
            continue

        try:
            member = Member(
                first_name=first_name,
                last_name=last_name,
                phone=clean_optional(get_col(row, columns["phone"])),
                email=email,
                school=clean_optional(get_col(row, columns["school"])),
                role=clean_optional(get_col(row, columns["role"])),
                student_id=clean_optional(get_col(row, columns["student_id"])),
                class_name=clean_optional(get_col(row, columns["class_name"])),
                major=clean_optional(get_col(row, columns["major"])),
            )
            members.append(member)

        except ValidationError as e:
            errors.append(f"Dong {row_idx + 1}: Loi du lieu - {e.errors()[0]['msg']}")
        except Exception as e:
            errors.append(f"Dong {row_idx + 1}: Loi khong xac dinh - {str(e)}")

    return team_name, members, errors


def process_sheet_url(url: str) -> Tuple[str, List[Member], List[str]]:
    csv_content = fetch_public_sheet_as_csv(url)
    return parse_member_list_from_csv(csv_content)

import csv
import hashlib
import io
import re
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from src.app.models.schema import (
    BronzeMoodleLogEvent,
    MoodleLogUserExclusion,
    RawMoodleLogFile,
    RawUehLmsCourseEnrollment,
)


REQUIRED_LOG_HEADERS = {
    "Time",
    "User full name",
    "Affected user",
    "Event context",
    "Component",
    "Event name",
    "Description",
    "Origin",
    "IP address",
}

HEADER_ALIASES = {
    "Thời gian": "Time",
    "Tên đầy đủ": "User full name",
    "người dùng bị ảnh hưởng": "Affected user",
    "Bối cảnh của sự kiện": "Event context",
    "thành phần": "Component",
    "Tên sự kiện": "Event name",
    "Mô tả": "Description",
    "Nguyên thủy": "Origin",
    "Địa chỉ giao thức mạng(IP)": "IP address",
}

COMPONENT_ALIASES = {
    "Hệ thống": "System",
    "Các file logs": "Logs",
    "Gói SCORM": "SCORM",
    "Bài trắc nghiệm": "Quiz",
    "Trang": "Page",
    "Diễn đàn": "Forum",
    "Báo cáo người dùng": "User report",
    "Báo cáo tổng quan": "Overview report",
    "Báo cáo của người chấm điểm": "Grader report",
}

EVENT_NAME_ALIASES = {
    "Đã xem báo cáo log": "Log report viewed",
    "Danh sách người dùng đã được xem": "User list viewed",
    "Mô-đun khóa học đã xem": "Course module viewed",
    "Đã xem khóa học": "Course viewed",
    "Người dùng đã ghi danh khóa học": "User enrolled in course",
    "Vai trò đã được bổ nhiệm": "Role assigned",
    "Đã cập nhật mô đun khóa học": "Course module updated",
    "Đã tạo mô đun khóa học": "Course module created",
    "Một phần khóa học đã được khởi tạo": "Course section created",
    "Phân mục khóa học đã được cập nhật": "Course section updated",
    "Sco đã được ra mắt": "SCO launched",
    "Đã gửi trạng thái SCORM": "SCORM status submitted",
    "Đã gửi điểm SCORM trần": "SCORM raw score submitted",
    "Bài làm trắc nghiệm đã được xem": "Quiz attempt viewed",
    "Bài làm trắc nghiệm đã được xem lại": "Quiz attempt reviewed",
    "Bài làm trắc nghiệm đã bắt đầu": "Quiz attempt started",
    "Đã nộp bài làm trắc nghiệm": "Quiz attempt submitted",
    "Tổng quan bài làm trắc nghiệm đã được xem": "Quiz attempt summary viewed",
    "Trang chỉnh sửa bài trắc nghiệm đã được xem": "Quiz editing page viewed",
    "Hoàn thành mô-đun khóa học được cập nhật": "Course module completion updated",
    "Điểm người dùng được chỉnh sửa trong sổ điểm": "Grade user report edited",
}

CONTEXT_TYPE_ALIASES = {
    "Khoá học": "Course",
    "Gói SCORM": "SCORM",
    "Bài trắc nghiệm": "Quiz",
    "Trang": "Page",
    "Diễn đàn": "Forum",
    "Khác": "Other",
    "H5P": "H5P",
}

LEARNING_EVENT_NAMES = {
    "Course viewed",
    "Course module viewed",
    "Section viewed",
    "H5P content viewed",
    "xAPI statement received",
    "The status of the submission has been viewed.",
    "Submission form viewed.",
    "Submission created.",
    "Submission updated.",
    "A file has been uploaded.",
    "An online text has been uploaded.",
    "A submission has been submitted.",
    "The status of the submission has been updated.",
    "SCO launched",
    "SCORM status submitted",
    "SCORM raw score submitted",
    "Quiz attempt viewed",
    "Quiz attempt reviewed",
    "Quiz attempt started",
    "Quiz attempt submitted",
    "Quiz attempt summary viewed",
    "Course module completion updated",
}

VIEW_EVENT_NAMES = {
    "Course viewed",
    "Course module viewed",
    "Section viewed",
    "H5P content viewed",
    "xAPI statement received",
    "The status of the submission has been viewed.",
    "Submission form viewed.",
    "SCO launched",
    "SCORM status submitted",
    "SCORM raw score submitted",
    "Quiz attempt viewed",
    "Quiz attempt reviewed",
    "Quiz attempt started",
    "Quiz attempt summary viewed",
}

SUBMISSION_WORK_EVENT_NAMES = {
    "Submission created.",
    "Submission updated.",
    "A file has been uploaded.",
    "An online text has been uploaded.",
    "The status of the submission has been updated.",
}

SUBMISSION_FINAL_EVENT_NAMES = {
    "A submission has been submitted.",
}

REPORT_COMPONENTS = {
    "Logs",
    "Live logs",
    "User report",
    "Overview report",
    "Grader report",
    "Single view",
}

ADMIN_EVENT_NAMES = {
    "Grade item updated",
    "Role assigned",
    "Role unassigned",
    "User enrolled in course",
    "User unenrolled from course",
    "Group member added",
    "Group deleted",
    "Grade deleted",
    "Course module updated",
    "Course module created",
    "Course section created",
    "Course section updated",
    "Grade user report edited",
}

UEH_LMS_ENTREPRENEURSHIP_COURSE_ID = 42246
UEH_LMS_ENTREPRENEURSHIP_KEY = "fmc3_entrepreneurship"
UEH_LMS_ENTREPRENEURSHIP_NAME = "Nền tảng Khởi nghiệp Kỹ thuật số"
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

USER_ID_PATTERN = re.compile(r"user with (?:the )?id '(-?\d+)'", re.IGNORECASE)
COURSE_ID_PATTERN = re.compile(r"course with (?:the )?id '(\d+)'", re.IGNORECASE)
COURSE_MODULE_ID_PATTERN = re.compile(r"(?:the )?course module id '(\d+)'", re.IGNORECASE)
GROUP_ID_PATTERN = re.compile(r"group with (?:the )?id '(\d+)'", re.IGNORECASE)


def import_moodle_log_csv(
    db: Session,
    content: bytes,
    source_file_name: str,
    source_type: str = "manual_upload",
) -> dict[str, Any]:
    text = content.decode("utf-8-sig")
    rows = [normalize_log_row(row) for row in csv.DictReader(io.StringIO(text))]
    headers = set(rows[0].keys()) if rows else set()
    missing_headers = sorted(REQUIRED_LOG_HEADERS - headers)

    raw_file = RawMoodleLogFile(
        source_file_name=source_file_name,
        source_type=source_type,
        row_count=len(rows),
        load_status="processing",
    )
    db.add(raw_file)
    db.flush()

    if missing_headers:
        raw_file.load_status = "failed"
        raw_file.failed_count = len(rows)
        raw_file.error_message = "Thiếu cột bắt buộc: " + ", ".join(missing_headers)
        db.commit()
        return build_import_report(raw_file, [])

    parsed_events = []
    errors = []
    event_times = []
    course_ids = []

    excluded_count = 0
    entrepreneurship_enrollment_emails = set()
    excluded_user_ids = get_active_excluded_moodle_user_ids(db)
    seen_logical_keys: dict[tuple[str, ...], int] = {}

    for row_number, row in enumerate(rows, start=2):
        try:
            logical_key = build_logical_event_key(row)
            occurrence_number = seen_logical_keys.get(logical_key, 0) + 1
            seen_logical_keys[logical_key] = occurrence_number
            parsed_event = parse_moodle_log_row(
                row=row,
                raw_file_id=raw_file.id,
                source_file_name=source_file_name,
                source_row_number=row_number,
                occurrence_number=occurrence_number,
            )
            if (
                parsed_event.moodle_user_id in excluded_user_ids
                or parsed_event.moodle_affected_user_id in excluded_user_ids
            ):
                excluded_count += 1
                continue
            if is_ueh_lms_entrepreneurship_enrollment(parsed_event):
                email = extract_enrollment_email(row)
                if email:
                    entrepreneurship_enrollment_emails.add(email)
            parsed_events.append(parsed_event)
            event_times.append(parsed_event.event_time)
            if parsed_event.moodle_course_id is not None:
                course_ids.append(parsed_event.moodle_course_id)
        except ValueError as exc:
            errors.append(f"Dòng {row_number}: {exc}")

    incoming_hashes = [event.event_hash for event in parsed_events]
    existing_hashes = set()
    if incoming_hashes:
        existing_hashes = {
            value
            for (value,) in db.query(BronzeMoodleLogEvent.event_hash)
            .filter(BronzeMoodleLogEvent.event_hash.in_(incoming_hashes))
            .all()
        }

    seen_hashes = set()
    new_events = []
    duplicate_count = 0
    for event in parsed_events:
        if event.event_hash in existing_hashes or event.event_hash in seen_hashes:
            duplicate_count += 1
            continue
        seen_hashes.add(event.event_hash)
        new_events.append(event)

    db.add_all(new_events)
    insert_ueh_lms_entrepreneurship_enrollments(
        db=db,
        emails=entrepreneurship_enrollment_emails,
    )
    raw_file.inserted_count = len(new_events)
    raw_file.duplicate_count = duplicate_count
    raw_file.failed_count = len(errors)
    raw_file.time_min = min(event_times) if event_times else None
    raw_file.time_max = max(event_times) if event_times else None
    raw_file.course_id = most_common_value(course_ids)
    raw_file.load_status = "completed" if not errors else "completed_with_errors"
    raw_file.error_message = "\n".join(errors[:20]) if errors else None
    db.commit()
    db.refresh(raw_file)

    return build_import_report(raw_file, errors, excluded_count)


def parse_moodle_log_row(
    row: dict[str, str],
    raw_file_id: int,
    source_file_name: str = "unknown.csv",
    source_row_number: int | None = None,
    occurrence_number: int | None = None,
) -> BronzeMoodleLogEvent:
    event_time = parse_moodle_time(row.get("Time", ""))
    description = clean_value(row.get("Description"))
    event_context = clean_value(row.get("Event context"))
    component = clean_value(row.get("Component"))
    event_name = clean_value(row.get("Event name"))
    user_full_name = clean_value(row.get("User full name"))
    user_ids = [int(value) for value in USER_ID_PATTERN.findall(description or "")]
    context_type, context_name = split_event_context(event_context)
    event_category = classify_event(component, event_name, user_full_name)

    return BronzeMoodleLogEvent(
        raw_file_id=raw_file_id,
        source_row_number=source_row_number,
        event_time=event_time,
        user_full_name_raw=user_full_name,
        affected_user_raw=clean_value(row.get("Affected user")),
        event_context_raw=event_context,
        component_raw=component,
        event_name_raw=event_name,
        description_raw=description,
        origin_raw=clean_value(row.get("Origin")),
        ip_address_raw=clean_value(row.get("IP address")),
        moodle_user_id=user_ids[0] if user_ids else None,
        moodle_affected_user_id=user_ids[1] if len(user_ids) > 1 else None,
        moodle_course_id=extract_first_int(COURSE_ID_PATTERN, description),
        moodle_course_module_id=extract_first_int(COURSE_MODULE_ID_PATTERN, description),
        moodle_group_id=extract_first_int(GROUP_ID_PATTERN, description),
        context_type=context_type,
        context_name=context_name,
        is_learning_event=event_category == "learning",
        event_category=event_category,
        event_hash=build_event_hash(row, occurrence_number),
    )


def parse_moodle_time(value: str) -> datetime:
    cleaned = clean_value(value)
    if not cleaned:
        raise ValueError("Thiếu Time")

    for date_format in (
        "%d/%m/%y, %H:%M:%S",
        "%m/%d/%y, %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(cleaned, date_format)
        except ValueError:
            continue

    raise ValueError(f"Không parse được Time: {cleaned}")


def split_event_context(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None

    context_type, separator, context_name = value.partition(":")
    if not separator:
        return None, value.strip()

    cleaned_type = clean_value(context_type)
    return CONTEXT_TYPE_ALIASES.get(cleaned_type, cleaned_type), clean_value(context_name)


def normalize_log_row(row: dict[str, str]) -> dict[str, str | None]:
    normalized = {}
    for key, value in row.items():
        canonical_key = HEADER_ALIASES.get(key, key)
        normalized[canonical_key] = value

    component = clean_value(normalized.get("Component"))
    event_name = clean_value(normalized.get("Event name"))
    normalized["Component"] = COMPONENT_ALIASES.get(component, component)
    normalized["Event name"] = EVENT_NAME_ALIASES.get(event_name, event_name)
    return normalized


def classify_event(component: str | None, event_name: str | None, user_full_name: str | None) -> str:
    if user_full_name == "UII ThinkSpace Admin":
        return "admin"

    if component in REPORT_COMPONENTS:
        return "report"

    if event_name in ADMIN_EVENT_NAMES:
        return "admin"

    if is_learning_event(component, event_name):
        return "learning"

    if component == "System":
        return "system"

    return "unknown"


def is_learning_event(component: str | None, event_name: str | None) -> bool:
    if component in REPORT_COMPONENTS:
        return False

    return event_name in LEARNING_EVENT_NAMES


def build_logical_event_key(row: dict[str, str]) -> tuple[str, ...]:
    time_value = clean_value(row.get("Time"))
    try:
        time_key = parse_moodle_time(time_value or "").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        time_key = time_value or ""

    return (
        time_key,
        clean_value(row.get("User full name")) or "",
        clean_value(row.get("Affected user")) or "",
        clean_value(row.get("Event context")) or "",
        clean_value(row.get("Component")) or "",
        clean_value(row.get("Event name")) or "",
        clean_value(row.get("Description")) or "",
        clean_value(row.get("Origin")) or "",
        clean_value(row.get("IP address")) or "",
    )


def build_event_hash(row: dict[str, str], occurrence_number: int | None = None) -> str:
    raw_key = "|".join(
        [
            str(occurrence_number or 1),
            *build_logical_event_key(row),
        ]
    )
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def extract_first_int(pattern: re.Pattern[str], value: str | None) -> int | None:
    if not value:
        return None

    match = pattern.search(value)
    return int(match.group(1)) if match else None


def clean_value(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if text in {"", "-"}:
        return None

    return text


def most_common_value(values: list[int]) -> int | None:
    if not values:
        return None

    return max(set(values), key=values.count)


def get_active_excluded_moodle_user_ids(db: Session) -> set[int]:
    return {
        moodle_user_id
        for (moodle_user_id,) in db.query(MoodleLogUserExclusion.moodle_user_id)
        .filter(MoodleLogUserExclusion.is_active == True)
        .all()
    }


def is_ueh_lms_entrepreneurship_enrollment(event: BronzeMoodleLogEvent) -> bool:
    return (
        event.moodle_course_id == UEH_LMS_ENTREPRENEURSHIP_COURSE_ID
        and event.event_name_raw == "User enrolled in course"
    )


def extract_enrollment_email(row: dict[str, str | None]) -> str | None:
    for column_name in ("Affected user", "User full name"):
        value = clean_value(row.get(column_name))
        if value and EMAIL_PATTERN.match(value):
            return value.lower()
    return None


def insert_ueh_lms_entrepreneurship_enrollments(
    db: Session,
    emails: set[str],
) -> None:
    if not emails:
        return

    existing_emails = {
        value
        for (value,) in db.query(RawUehLmsCourseEnrollment.email)
        .filter(
            RawUehLmsCourseEnrollment.external_course_key == UEH_LMS_ENTREPRENEURSHIP_KEY,
            RawUehLmsCourseEnrollment.email.in_(emails),
        )
        .all()
    }

    new_enrollments = [
        RawUehLmsCourseEnrollment(
            source_system="ueh_lms_log",
            external_course_key=UEH_LMS_ENTREPRENEURSHIP_KEY,
            external_course_name=UEH_LMS_ENTREPRENEURSHIP_NAME,
            email_raw=email,
            email=email,
            full_name_raw=email,
            enrollment_status="enrolled",
        )
        for email in sorted(emails - existing_emails)
    ]
    db.add_all(new_enrollments)


def build_import_report(raw_file: RawMoodleLogFile, errors: list[str], excluded_count: int = 0) -> dict[str, Any]:
    return {
        "raw_file_id": raw_file.id,
        "source_file_name": raw_file.source_file_name,
        "source_type": raw_file.source_type,
        "load_status": raw_file.load_status,
        "row_count": raw_file.row_count,
        "inserted_count": raw_file.inserted_count,
        "duplicate_count": raw_file.duplicate_count,
        "failed_count": raw_file.failed_count,
        "excluded_count": excluded_count,
        "course_id": raw_file.course_id,
        "time_min": raw_file.time_min.isoformat() if raw_file.time_min else None,
        "time_max": raw_file.time_max.isoformat() if raw_file.time_max else None,
        "errors": errors[:20],
    }

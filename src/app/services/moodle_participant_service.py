import csv
import hashlib
import io
from typing import Any

from sqlalchemy.orm import Session

from src.app.models.schema import (
    MoodleParticipantEmailExclusion,
    RawMoodleParticipant,
    RawMoodleParticipantFile,
)
from src.app.services.moodle_log_service import clean_value
from src.app.utils.text_utils import normalized_team_name


REQUIRED_PARTICIPANT_HEADERS = {
    "First name",
    "Last name",
    "Email address",
    "Groups",
}


def import_moodle_participants_csv(
    db: Session,
    content: bytes,
    source_file_name: str,
    course_id: int | None = None,
    source_type: str = "manual_upload",
) -> dict[str, Any]:
    text = content.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    headers = set(rows[0].keys()) if rows else set()
    missing_headers = sorted(REQUIRED_PARTICIPANT_HEADERS - headers)

    raw_file = RawMoodleParticipantFile(
        source_file_name=source_file_name,
        source_type=source_type,
        course_id=course_id,
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

    parsed_participants = []
    errors = []
    excluded_count = 0
    excluded_emails = get_active_excluded_emails(db)
    for row_number, row in enumerate(rows, start=2):
        try:
            parsed_participant = parse_moodle_participant_row(
                row=row,
                raw_file_id=raw_file.id,
                source_file_name=source_file_name,
                source_row_number=row_number,
                course_id=course_id,
            )
            if parsed_participant.email in excluded_emails:
                excluded_count += 1
                continue
            parsed_participants.append(parsed_participant)
        except ValueError as exc:
            errors.append(f"Dòng {row_number}: {exc}")

    incoming_hashes = [participant.participant_hash for participant in parsed_participants]
    existing_hashes = set()
    if incoming_hashes:
        existing_hashes = {
            value
            for (value,) in db.query(RawMoodleParticipant.participant_hash)
            .filter(RawMoodleParticipant.participant_hash.in_(incoming_hashes))
            .all()
        }

    seen_hashes = set()
    new_participants = []
    duplicate_count = 0
    for participant in parsed_participants:
        if participant.participant_hash in existing_hashes or participant.participant_hash in seen_hashes:
            duplicate_count += 1
            continue
        seen_hashes.add(participant.participant_hash)
        new_participants.append(participant)

    db.add_all(new_participants)
    raw_file.inserted_count = len(new_participants)
    raw_file.duplicate_count = duplicate_count
    raw_file.failed_count = len(errors)
    raw_file.load_status = "completed" if not errors else "completed_with_errors"
    raw_file.error_message = "\n".join(errors[:20]) if errors else None
    db.commit()
    db.refresh(raw_file)

    return build_import_report(raw_file, errors, excluded_count)


def parse_moodle_participant_row(
    row: dict[str, str],
    raw_file_id: int,
    source_file_name: str = "unknown.csv",
    source_row_number: int | None = None,
    course_id: int | None = None,
) -> RawMoodleParticipant:
    first_name = clean_value(row.get("First name"))
    last_name = clean_value(row.get("Last name"))
    email_raw = clean_value(row.get("Email address"))
    groups_raw = clean_value(row.get("Groups"))
    group_name = normalized_team_name(groups_raw)

    if not first_name and not last_name:
        raise ValueError("Thiếu First name và Last name")

    full_name = " ".join(part for part in [first_name, last_name] if part)
    email = normalize_text_key(email_raw)

    return RawMoodleParticipant(
        raw_file_id=raw_file_id,
        source_row_number=source_row_number,
        course_id=course_id,
        first_name_raw=first_name,
        last_name_raw=last_name,
        email_raw=email_raw,
        groups_raw=groups_raw,
        moodle_full_name=full_name,
        moodle_full_name_key=normalize_text_key(full_name),
        email=email,
        moodle_group_name=group_name,
        participant_hash=build_participant_hash(row, source_file_name, source_row_number, course_id),
    )


def normalize_text_key(value: str | None) -> str | None:
    cleaned = clean_value(value)
    if not cleaned:
        return None

    return " ".join(cleaned.lower().split())


def build_participant_hash(
    row: dict[str, str],
    source_file_name: str,
    source_row_number: int | None,
    course_id: int | None,
) -> str:
    raw_key = "|".join(
        [
            clean_value(source_file_name) or "",
            str(course_id or ""),
            str(source_row_number or ""),
            clean_value(row.get("First name")) or "",
            clean_value(row.get("Last name")) or "",
            clean_value(row.get("Email address")) or "",
            clean_value(row.get("Groups")) or "",
        ]
    )
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def get_active_excluded_emails(db: Session) -> set[str]:
    return {
        email
        for (email,) in db.query(MoodleParticipantEmailExclusion.email)
        .filter(MoodleParticipantEmailExclusion.is_active == True)
        .all()
    }


def build_import_report(
    raw_file: RawMoodleParticipantFile,
    errors: list[str],
    excluded_count: int = 0,
) -> dict[str, Any]:
    return {
        "raw_file_id": raw_file.id,
        "source_file_name": raw_file.source_file_name,
        "source_type": raw_file.source_type,
        "course_id": raw_file.course_id,
        "load_status": raw_file.load_status,
        "row_count": raw_file.row_count,
        "inserted_count": raw_file.inserted_count,
        "duplicate_count": raw_file.duplicate_count,
        "failed_count": raw_file.failed_count,
        "excluded_count": excluded_count,
        "errors": errors[:20],
    }

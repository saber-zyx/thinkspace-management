from datetime import datetime, timezone
import hashlib
import re
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.app.core.config import settings
from src.app.models.schema import (
    BronzeMoodleLogEvent,
    MoodleLogIngestionRun,
    MoodleLogIngestionState,
    MoodleLogUserExclusion,
    RawMoodleLogFile,
)
from src.app.services.moodle_log_service import classify_event, clean_value


IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
COURSE_MODULE_CONTEXT_LEVEL = 70


def get_live_ingestion_status(db: Session) -> dict[str, Any]:
    states = (
        db.query(MoodleLogIngestionState)
        .order_by(MoodleLogIngestionState.source_name, MoodleLogIngestionState.course_id)
        .all()
    )
    latest_runs = (
        db.query(MoodleLogIngestionRun)
        .order_by(MoodleLogIngestionRun.started_at.desc(), MoodleLogIngestionRun.id.desc())
        .limit(10)
        .all()
    )

    return {
        "is_configured": bool(settings.moodle_log_source_database_url),
        "source_name": settings.moodle_log_source_name,
        "poll_course_ids": parse_course_ids(settings.moodle_log_source_poll_course_ids),
        "batch_size": settings.moodle_log_source_batch_size,
        "states": [serialize_state(state) for state in states],
        "latest_runs": [serialize_run(run) for run in latest_runs],
    }


def run_live_moodle_log_ingestion_once(db: Session) -> dict[str, Any]:
    source_name = settings.moodle_log_source_name
    course_ids = parse_course_ids(settings.moodle_log_source_poll_course_ids)
    state = get_or_create_state(db, source_name=source_name, course_id=None)
    run = MoodleLogIngestionRun(
        source_name=source_name,
        course_id=None,
        previous_watermark_id=state.last_moodle_log_id,
        status="running",
    )
    db.add(run)
    db.flush()

    if not settings.moodle_log_source_database_url:
        run.status = "not_configured"
        run.error_message = "Chưa cấu hình MOODLE_LOG_SOURCE_DATABASE_URL."
        run.finished_at = datetime.now(timezone.utc)
        state.status = "not_configured"
        state.error_message = run.error_message
        db.commit()
        return build_run_result(run, state)

    try:
        source_rows = fetch_moodle_standard_log_rows(
            last_moodle_log_id=state.last_moodle_log_id or 0,
            course_ids=course_ids,
            limit=settings.moodle_log_source_batch_size,
        )
        report = insert_live_log_rows(
            db=db,
            source_name=source_name,
            source_rows=source_rows,
        )
        new_watermark_id = max(
            [row["moodle_log_id"] for row in source_rows],
            default=state.last_moodle_log_id,
        )

        run.rows_fetched = len(source_rows)
        run.inserted_count = report["inserted_count"]
        run.duplicate_count = report["duplicate_count"]
        run.failed_count = report["failed_count"]
        run.new_watermark_id = new_watermark_id
        run.status = "completed" if report["failed_count"] == 0 else "completed_with_errors"
        run.finished_at = datetime.now(timezone.utc)

        state.last_moodle_log_id = new_watermark_id
        state.last_event_time = report["latest_event_time"] or state.last_event_time
        state.last_success_at = run.finished_at
        state.status = run.status
        state.error_message = None if report["failed_count"] == 0 else report["error_message"]
        db.commit()
        db.refresh(run)
        db.refresh(state)
        return build_run_result(run, state)
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        state.status = "failed"
        state.error_message = str(exc)
        db.commit()
        return build_run_result(run, state)


def fetch_moodle_standard_log_rows(
    last_moodle_log_id: int,
    course_ids: list[int],
    limit: int,
) -> list[dict[str, Any]]:
    source_table = validate_identifier(settings.moodle_log_source_table)
    user_table = validate_identifier(settings.moodle_log_source_user_table)
    course_table = validate_identifier(settings.moodle_log_source_course_table)

    source_engine = create_engine(settings.moodle_log_source_database_url)
    course_filter = ""
    params: dict[str, Any] = {
        "last_moodle_log_id": last_moodle_log_id,
        "limit": limit,
    }
    if course_ids:
        course_filter = "AND l.courseid = ANY(:course_ids)"
        params["course_ids"] = course_ids

    query = text(
        f"""
        SELECT
            l.id AS moodle_log_id,
            to_timestamp(l.timecreated) AS event_time,
            l.userid AS moodle_user_id,
            l.relateduserid AS moodle_affected_user_id,
            l.courseid AS moodle_course_id,
            l.contextlevel,
            l.contextinstanceid,
            l.component,
            l.eventname,
            l.action,
            l.target,
            l.origin,
            l.ip,
            l.other,
            CONCAT_WS(' ', u.firstname, u.lastname) AS user_full_name,
            CONCAT_WS(' ', au.firstname, au.lastname) AS affected_user_full_name,
            c.fullname AS course_name
        FROM {source_table} l
        LEFT JOIN {user_table} u
            ON u.id = l.userid
        LEFT JOIN {user_table} au
            ON au.id = l.relateduserid
        LEFT JOIN {course_table} c
            ON c.id = l.courseid
        WHERE l.id > :last_moodle_log_id
          {course_filter}
        ORDER BY l.id ASC
        LIMIT :limit
        """
    )

    with source_engine.connect() as connection:
        return [dict(row) for row in connection.execute(query, params).mappings().all()]


def insert_live_log_rows(
    db: Session,
    source_name: str,
    source_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    raw_file = RawMoodleLogFile(
        source_file_name=f"{source_name}:incremental",
        source_type="live_db_incremental",
        row_count=len(source_rows),
        load_status="processing",
    )
    db.add(raw_file)
    db.flush()

    excluded_user_ids = {
        moodle_user_id
        for (moodle_user_id,) in db.query(MoodleLogUserExclusion.moodle_user_id)
        .filter(MoodleLogUserExclusion.is_active == True)
        .all()
    }
    events = []
    latest_event_time = None
    failed_count = 0
    errors = []

    for row in source_rows:
        try:
            event = build_bronze_event_from_standard_log(
                row=row,
                raw_file_id=raw_file.id,
                source_name=source_name,
            )
            if (
                event.moodle_user_id in excluded_user_ids
                or event.moodle_affected_user_id in excluded_user_ids
            ):
                continue
            latest_event_time = max(latest_event_time, event.event_time) if latest_event_time else event.event_time
            events.append(event)
        except Exception as exc:
            failed_count += 1
            errors.append(str(exc))

    existing_hashes = set()
    incoming_hashes = [event.event_hash for event in events]
    if incoming_hashes:
        existing_hashes = {
            value
            for (value,) in db.query(BronzeMoodleLogEvent.event_hash)
            .filter(BronzeMoodleLogEvent.event_hash.in_(incoming_hashes))
            .all()
        }

    new_events = []
    duplicate_count = 0
    for event in events:
        if event.event_hash in existing_hashes:
            duplicate_count += 1
            continue
        new_events.append(event)

    db.add_all(new_events)
    raw_file.inserted_count = len(new_events)
    raw_file.duplicate_count = duplicate_count
    raw_file.failed_count = failed_count
    raw_file.time_min = min([event.event_time for event in events], default=None)
    raw_file.time_max = max([event.event_time for event in events], default=None)
    raw_file.course_id = most_common_course_id(events)
    raw_file.load_status = "completed" if failed_count == 0 else "completed_with_errors"
    raw_file.error_message = "\n".join(errors[:20]) if errors else None

    return {
        "inserted_count": len(new_events),
        "duplicate_count": duplicate_count,
        "failed_count": failed_count,
        "latest_event_time": latest_event_time,
        "error_message": raw_file.error_message,
    }


def build_bronze_event_from_standard_log(
    row: dict[str, Any],
    raw_file_id: int,
    source_name: str,
) -> BronzeMoodleLogEvent:
    event_name = canonical_event_name(row)
    component = canonical_component(row.get("component"))
    context_type = context_type_from_level(row.get("contextlevel"))
    context_name = build_context_name(row, context_type)
    event_context = f"{context_type}: {context_name}" if context_type and context_name else context_name
    description = build_standard_log_description(row, event_name)
    user_full_name = clean_value(row.get("user_full_name"))
    event_category = classify_event(component, event_name, user_full_name)
    moodle_log_id = int(row["moodle_log_id"])

    return BronzeMoodleLogEvent(
        raw_file_id=raw_file_id,
        source_row_number=moodle_log_id,
        event_time=row["event_time"],
        user_full_name_raw=user_full_name,
        affected_user_raw=clean_value(row.get("affected_user_full_name")),
        event_context_raw=event_context,
        component_raw=component,
        event_name_raw=event_name,
        description_raw=description,
        origin_raw=clean_value(row.get("origin")),
        ip_address_raw=clean_value(row.get("ip")),
        moodle_user_id=row.get("moodle_user_id"),
        moodle_affected_user_id=row.get("moodle_affected_user_id"),
        moodle_course_id=row.get("moodle_course_id"),
        moodle_course_module_id=course_module_id_from_row(row),
        moodle_group_id=None,
        context_type=context_type,
        context_name=context_name,
        is_learning_event=event_category == "learning",
        event_category=event_category,
        event_hash=hash_live_log_event(source_name, moodle_log_id),
    )


def canonical_event_name(row: dict[str, Any]) -> str:
    eventname = clean_value(row.get("eventname")) or ""
    action = clean_value(row.get("action")) or ""
    target = clean_value(row.get("target")) or ""
    event_key = eventname.lower()

    if "course_viewed" in event_key:
        return "Course viewed"
    if "course_module_viewed" in event_key:
        return "Course module viewed"
    if "submission_created" in event_key:
        return "Submission created."
    if "submission_updated" in event_key:
        return "Submission updated."
    if "submission_submitted" in event_key or "assessable_submitted" in event_key:
        return "A submission has been submitted."
    if "user_enrolment_created" in event_key or (action == "created" and target == "user_enrolment"):
        return "User enrolled in course"
    if "course_module_completion_updated" in event_key:
        return "Course module completion updated"
    if "attempt_submitted" in event_key:
        return "Quiz attempt submitted"
    if "attempt_viewed" in event_key:
        return "Quiz attempt viewed"
    if "sco_launched" in event_key:
        return "SCO launched"

    readable = eventname.rsplit("\\", 1)[-1].replace("_", " ").strip()
    return readable.title() if readable else f"{action} {target}".strip() or "Unknown event"


def canonical_component(component: Any) -> str | None:
    value = clean_value(component)
    if not value:
        return None
    component_map = {
        "core": "System",
        "mod_assign": "Assignment",
        "mod_feedback": "Feedback",
        "mod_forum": "Forum",
        "mod_h5pactivity": "H5P",
        "mod_page": "Page",
        "mod_quiz": "Quiz",
        "mod_resource": "File",
        "mod_scorm": "SCORM",
    }
    if value in component_map:
        return component_map[value]
    if value.startswith("mod_"):
        return value.replace("mod_", "").title()
    return value


def context_type_from_level(contextlevel: Any) -> str | None:
    if contextlevel == COURSE_MODULE_CONTEXT_LEVEL:
        return "Course module"
    return "Course"


def build_context_name(row: dict[str, Any], context_type: str | None) -> str | None:
    if context_type == "Course module":
        module_id = course_module_id_from_row(row)
        return f"module {module_id}" if module_id else None
    return clean_value(row.get("course_name"))


def build_standard_log_description(row: dict[str, Any], event_name: str) -> str:
    user_id = row.get("moodle_user_id")
    course_id = row.get("moodle_course_id")
    module_id = course_module_id_from_row(row)
    parts = [event_name]
    if user_id is not None:
        parts.append(f"user_id={user_id}")
    if course_id is not None:
        parts.append(f"course_id={course_id}")
    if module_id is not None:
        parts.append(f"course_module_id={module_id}")
    return "; ".join(parts)


def course_module_id_from_row(row: dict[str, Any]) -> int | None:
    if row.get("contextlevel") == COURSE_MODULE_CONTEXT_LEVEL:
        return row.get("contextinstanceid")
    return None


def get_or_create_state(db: Session, source_name: str, course_id: int | None) -> MoodleLogIngestionState:
    state = (
        db.query(MoodleLogIngestionState)
        .filter(
            MoodleLogIngestionState.source_name == source_name,
            MoodleLogIngestionState.course_id.is_(course_id),
        )
        .first()
    )
    if state:
        return state

    state = MoodleLogIngestionState(source_name=source_name, course_id=course_id)
    db.add(state)
    db.flush()
    return state


def parse_course_ids(value: str | None) -> list[int]:
    if not value:
        return []
    return [int(item.strip()) for item in value.split(",") if item.strip().isdigit()]


def validate_identifier(value: str) -> str:
    if not IDENTIFIER_PATTERN.match(value):
        raise ValueError(f"Tên bảng nguồn không hợp lệ: {value}")
    return value


def hash_live_log_event(source_name: str, moodle_log_id: int) -> str:
    return hashlib.sha256(f"live-db|{source_name}|{moodle_log_id}".encode("utf-8")).hexdigest()


def most_common_course_id(events: list[BronzeMoodleLogEvent]) -> int | None:
    course_ids = [event.moodle_course_id for event in events if event.moodle_course_id is not None]
    if not course_ids:
        return None
    return max(set(course_ids), key=course_ids.count)


def build_run_result(run: MoodleLogIngestionRun, state: MoodleLogIngestionState) -> dict[str, Any]:
    return {
        "run": serialize_run(run),
        "state": serialize_state(state),
    }


def serialize_state(state: MoodleLogIngestionState) -> dict[str, Any]:
    return {
        "source_name": state.source_name,
        "course_id": state.course_id,
        "last_moodle_log_id": state.last_moodle_log_id,
        "last_event_time": state.last_event_time.isoformat() if state.last_event_time else None,
        "last_success_at": state.last_success_at.isoformat() if state.last_success_at else None,
        "status": state.status,
        "error_message": state.error_message,
        "updated_at": state.updated_at.isoformat() if state.updated_at else None,
    }


def serialize_run(run: MoodleLogIngestionRun) -> dict[str, Any]:
    return {
        "id": run.id,
        "source_name": run.source_name,
        "course_id": run.course_id,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "status": run.status,
        "rows_fetched": run.rows_fetched,
        "inserted_count": run.inserted_count,
        "duplicate_count": run.duplicate_count,
        "failed_count": run.failed_count,
        "previous_watermark_id": run.previous_watermark_id,
        "new_watermark_id": run.new_watermark_id,
        "error_message": run.error_message,
    }

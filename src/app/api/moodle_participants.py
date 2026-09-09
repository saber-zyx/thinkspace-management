from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.app.core.database import get_db
from src.app.models.schema import RawMoodleParticipant, RawMoodleParticipantFile
from src.app.services.moodle_participant_service import import_moodle_participants_csv

router = APIRouter(prefix="/api/v1/moodle-participants", tags=["Moodle Participants"])


@router.post("/import-csv")
async def import_moodle_participants(
    file: UploadFile = File(...),
    course_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Vui lòng tải lên file CSV participants từ Moodle.")

    content = await file.read()
    try:
        report = import_moodle_participants_csv(
            db=db,
            content=content,
            source_file_name=file.filename,
            source_type="manual_upload",
            course_id=course_id,
        )
        return {"status": "success", "data": report}
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File CSV cần dùng encoding UTF-8.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/summary")
def get_moodle_participants_summary(db: Session = Depends(get_db)):
    raw_files = db.query(func.count(RawMoodleParticipantFile.id)).scalar() or 0
    total_participants = db.query(func.count(RawMoodleParticipant.id)).scalar() or 0
    unique_emails = db.query(func.count(func.distinct(RawMoodleParticipant.email))).scalar() or 0
    unique_full_names = db.query(func.count(func.distinct(RawMoodleParticipant.moodle_full_name_key))).scalar() or 0

    return {
        "raw_files": raw_files,
        "total_participants": total_participants,
        "unique_emails": unique_emails,
        "unique_full_names": unique_full_names,
    }


@router.get("/identity-map-summary")
def get_moodle_identity_map_summary(db: Session = Depends(get_db)):
    identity_summary = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_identities,
                COUNT(registration_id) AS matched_registrations,
                COUNT(*) - COUNT(registration_id) AS unmatched_registrations
            FROM int_moodle_user_identity_map
            """
        )
    ).mappings().one()

    learning_summary = db.execute(
        text(
            """
            SELECT
                COUNT(DISTINCT b.moodle_user_id) AS learning_users,
                COUNT(DISTINCT m.email) AS matched_learning_users
            FROM bronze_moodle_log_events b
            LEFT JOIN int_moodle_user_identity_map m
                ON LOWER(TRIM(b.user_full_name_raw)) = m.moodle_full_name_key
            WHERE b.is_learning_event = TRUE
              AND b.moodle_user_id IS NOT NULL
            """
        )
    ).mappings().one()

    status_rows = db.execute(
        text(
            """
            SELECT identity_status, COUNT(*) AS row_count
            FROM int_moodle_user_identity_map
            GROUP BY identity_status
            ORDER BY row_count DESC, identity_status
            """
        )
    ).mappings().all()

    return {
        "total_identities": identity_summary["total_identities"],
        "matched_registrations": identity_summary["matched_registrations"],
        "unmatched_registrations": identity_summary["unmatched_registrations"],
        "learning_users": learning_summary["learning_users"],
        "matched_learning_users": learning_summary["matched_learning_users"],
        "identity_status_counts": [dict(row) for row in status_rows],
    }

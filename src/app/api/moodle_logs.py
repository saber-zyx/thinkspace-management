from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.app.core.database import get_db
from src.app.models.schema import BronzeMoodleLogEvent, RawMoodleLogFile
from src.app.services.moodle_log_service import import_moodle_log_csv

router = APIRouter(prefix="/api/v1/moodle-logs", tags=["Moodle Logs"])


@router.post("/import-csv")
async def import_moodle_logs_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Vui lòng tải lên file CSV log Moodle.")

    content = await file.read()
    try:
        report = import_moodle_log_csv(
            db=db,
            content=content,
            source_file_name=file.filename,
            source_type="manual_upload",
        )
        return {"status": "success", "data": report}
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File CSV cần dùng encoding UTF-8.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/bronze-summary")
def get_bronze_moodle_log_summary(db: Session = Depends(get_db)):
    total_events = db.query(func.count(BronzeMoodleLogEvent.id)).scalar() or 0
    learning_events = (
        db.query(func.count(BronzeMoodleLogEvent.id))
        .filter(BronzeMoodleLogEvent.is_learning_event == True)
        .scalar()
        or 0
    )
    raw_files = db.query(func.count(RawMoodleLogFile.id)).scalar() or 0
    latest_event_time = db.query(func.max(BronzeMoodleLogEvent.event_time)).scalar()

    return {
        "raw_files": raw_files,
        "total_events": total_events,
        "learning_events": learning_events,
        "latest_event_time": latest_event_time.isoformat() if latest_event_time else None,
    }


@router.get("/silver-summary")
def get_silver_moodle_learning_summary(db: Session = Depends(get_db)):
    summary = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS learning_event_rows,
                COUNT(DISTINCT moodle_user_id) AS learning_users,
                COUNT(DISTINCT email) AS matched_learning_emails,
                COUNT(DISTINCT team_name_key) AS learning_teams,
                MIN(event_time) AS first_event_time,
                MAX(event_time) AS latest_event_time
            FROM silver_moodle_learning_events
            """
        )
    ).mappings().one()

    unmapped = db.execute(
        text(
            """
            SELECT COUNT(*) AS unmapped_event_rows
            FROM silver_moodle_learning_events
            WHERE email IS NULL
            """
        )
    ).mappings().one()

    return {
        "learning_event_rows": summary["learning_event_rows"],
        "learning_users": summary["learning_users"],
        "matched_learning_emails": summary["matched_learning_emails"],
        "learning_teams": summary["learning_teams"],
        "unmapped_event_rows": unmapped["unmapped_event_rows"],
        "first_event_time": summary["first_event_time"].isoformat() if summary["first_event_time"] else None,
        "latest_event_time": summary["latest_event_time"].isoformat() if summary["latest_event_time"] else None,
    }


@router.get("/activity-dim-summary")
def get_moodle_activity_dim_summary(db: Session = Depends(get_db)):
    summary = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_activities,
                COUNT(*) FILTER (WHERE is_submission_activity = TRUE) AS submission_activities,
                COUNT(*) FILTER (WHERE is_learning_material = TRUE) AS learning_materials,
                SUM(submission_final_event_rows) AS submission_final_event_rows,
                SUM(unique_submitters) AS summed_unique_submitters
            FROM dim_moodle_course_activities
            """
        )
    ).mappings().one()
    global_submitters = db.execute(
        text(
            """
            SELECT COUNT(DISTINCT email) AS global_unique_submitters
            FROM silver_moodle_learning_events
            WHERE is_submission_final_event = TRUE
            """
        )
    ).mappings().one()

    by_type = db.execute(
        text(
            """
            SELECT
                COALESCE(activity_type, 'Chưa xác định') AS activity_type,
                COUNT(*) AS activity_count
            FROM dim_moodle_course_activities
            GROUP BY COALESCE(activity_type, 'Chưa xác định')
            ORDER BY activity_count DESC, activity_type
            """
        )
    ).mappings().all()

    return {
        "total_activities": summary["total_activities"],
        "submission_activities": summary["submission_activities"],
        "learning_materials": summary["learning_materials"],
        "submission_final_event_rows": summary["submission_final_event_rows"] or 0,
        "global_unique_submitters": global_submitters["global_unique_submitters"] or 0,
        "summed_unique_submitters": summary["summed_unique_submitters"] or 0,
        "activity_type_distribution": [dict(row) for row in by_type],
    }


@router.get("/gold-user-summary")
def get_gold_user_learning_summary(db: Session = Depends(get_db)):
    summary = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_users,
                COUNT(*) FILTER (WHERE has_ever_accessed = TRUE) AS accessed_users,
                COUNT(*) FILTER (WHERE has_ever_accessed = FALSE) AS not_started_users,
                COUNT(*) FILTER (WHERE has_submitted = TRUE) AS submitted_users,
                ROUND(AVG(viewed_activity_count)::NUMERIC, 2) AS avg_viewed_activities,
                MAX(last_access_at) AS latest_access_at
            FROM gold_user_learning_summary
            """
        )
    ).mappings().one()

    status_distribution = db.execute(
        text(
            """
            SELECT
                current_learning_status,
                COUNT(*) AS user_count
            FROM gold_user_learning_summary
            GROUP BY current_learning_status
            ORDER BY user_count DESC, current_learning_status
            """
        )
    ).mappings().all()

    top_active_users = db.execute(
        text(
            """
            SELECT
                full_name,
                email,
                team_name,
                viewed_activity_count,
                submitted_activity_count,
                learning_event_count,
                current_learning_status,
                last_access_at
            FROM gold_user_learning_summary
            WHERE has_ever_accessed = TRUE
            ORDER BY viewed_activity_count DESC, learning_event_count DESC, last_access_at DESC
            LIMIT 10
            """
        )
    ).mappings().all()

    return {
        "total_users": summary["total_users"],
        "accessed_users": summary["accessed_users"],
        "not_started_users": summary["not_started_users"],
        "submitted_users": summary["submitted_users"],
        "avg_viewed_activities": float(summary["avg_viewed_activities"] or 0),
        "latest_access_at": summary["latest_access_at"].isoformat() if summary["latest_access_at"] else None,
        "status_distribution": [dict(row) for row in status_distribution],
        "top_active_users": [
            {
                **dict(row),
                "last_access_at": row["last_access_at"].isoformat() if row["last_access_at"] else None,
            }
            for row in top_active_users
        ],
    }


@router.get("/gold-registered-user-summary")
def get_gold_registered_user_learning_summary(db: Session = Depends(get_db)):
    summary = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_registered_users,
                COUNT(*) FILTER (
                    WHERE has_moodle_participant = TRUE
                ) AS mapped_to_moodle_users,
                COUNT(*) FILTER (
                    WHERE has_moodle_participant = FALSE
                ) AS missing_moodle_participant_users,
                COUNT(*) FILTER (
                    WHERE has_ever_accessed = TRUE
                ) AS accessed_users,
                COUNT(*) FILTER (
                    WHERE has_ever_accessed = FALSE
                ) AS not_started_users,
                COUNT(*) FILTER (
                    WHERE has_submitted = TRUE
                ) AS submitted_users,
                COUNT(DISTINCT team_name_key) FILTER (
                    WHERE team_name_key IS NOT NULL
                ) AS total_registered_teams,
                COUNT(DISTINCT team_name_key) FILTER (
                    WHERE has_ever_accessed = TRUE
                      AND team_name_key IS NOT NULL
                ) AS active_registered_teams,
                ROUND(AVG(viewed_activity_count)::NUMERIC, 2) AS avg_viewed_activities,
                MAX(last_access_at) AS latest_access_at
            FROM gold_registered_user_learning_summary
            """
        )
    ).mappings().one()

    status_distribution = db.execute(
        text(
            """
            SELECT
                current_learning_status,
                COUNT(*) AS user_count
            FROM gold_registered_user_learning_summary
            GROUP BY current_learning_status
            ORDER BY user_count DESC, current_learning_status
            """
        )
    ).mappings().all()

    team_distribution = db.execute(
        text(
            """
            SELECT
                team_name,
                COUNT(*) AS registered_users,
                COUNT(*) FILTER (WHERE has_ever_accessed = TRUE) AS accessed_users,
                COUNT(*) FILTER (WHERE has_submitted = TRUE) AS submitted_users,
                MAX(last_access_at) AS latest_access_at
            FROM gold_registered_user_learning_summary
            WHERE team_name_key IS NOT NULL
            GROUP BY team_name
            ORDER BY accessed_users DESC, registered_users DESC, team_name
            LIMIT 10
            """
        )
    ).mappings().all()

    return {
        "total_registered_users": summary["total_registered_users"],
        "mapped_to_moodle_users": summary["mapped_to_moodle_users"],
        "missing_moodle_participant_users": summary["missing_moodle_participant_users"],
        "accessed_users": summary["accessed_users"],
        "not_started_users": summary["not_started_users"],
        "submitted_users": summary["submitted_users"],
        "total_registered_teams": summary["total_registered_teams"],
        "active_registered_teams": summary["active_registered_teams"],
        "avg_viewed_activities": float(summary["avg_viewed_activities"] or 0),
        "latest_access_at": summary["latest_access_at"].isoformat() if summary["latest_access_at"] else None,
        "status_distribution": [dict(row) for row in status_distribution],
        "team_distribution": [
            {
                **dict(row),
                "latest_access_at": row["latest_access_at"].isoformat() if row["latest_access_at"] else None,
            }
            for row in team_distribution
        ],
    }


@router.get("/gold-team-summary")
def get_gold_team_learning_summary(db: Session = Depends(get_db)):
    summary = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_teams,
                COUNT(*) FILTER (
                    WHERE has_any_access = TRUE
                ) AS active_teams,
                COUNT(*) FILTER (
                    WHERE has_any_access = FALSE
                ) AS not_started_teams,
                COUNT(*) FILTER (
                    WHERE has_any_submission = TRUE
                ) AS submitted_teams,
                COALESCE(SUM(registered_users), 0) AS registered_team_users,
                COALESCE(SUM(accessed_users), 0) AS accessed_team_users,
                COALESCE(SUM(not_started_users), 0) AS not_started_team_users,
                COALESCE(SUM(submitted_users), 0) AS submitted_team_users,
                ROUND(AVG(avg_viewed_activities_per_user)::NUMERIC, 2) AS avg_viewed_activities_per_team_user,
                MAX(last_access_at) AS latest_access_at
            FROM gold_team_learning_summary
            """
        )
    ).mappings().one()

    status_distribution = db.execute(
        text(
            """
            SELECT
                current_team_learning_status,
                COUNT(*) AS team_count
            FROM gold_team_learning_summary
            GROUP BY current_team_learning_status
            ORDER BY team_count DESC, current_team_learning_status
            """
        )
    ).mappings().all()

    teams = db.execute(
        text(
            """
            SELECT
                team_name_key,
                team_name,
                registered_users,
                accessed_users,
                not_started_users,
                active_users,
                inactive_users,
                submitted_users,
                viewed_activity_count,
                submitted_activity_count,
                submitted_activity_names,
                learning_event_count,
                current_team_learning_status,
                last_access_at
            FROM gold_team_learning_summary
            ORDER BY
                has_any_submission DESC,
                has_any_access DESC,
                accessed_users DESC,
                registered_users DESC,
                team_name
            """
        )
    ).mappings().all()

    return {
        "total_teams": summary["total_teams"],
        "active_teams": summary["active_teams"],
        "not_started_teams": summary["not_started_teams"],
        "submitted_teams": summary["submitted_teams"],
        "registered_team_users": summary["registered_team_users"],
        "accessed_team_users": summary["accessed_team_users"],
        "not_started_team_users": summary["not_started_team_users"],
        "submitted_team_users": summary["submitted_team_users"],
        "avg_viewed_activities_per_team_user": float(
            summary["avg_viewed_activities_per_team_user"] or 0
        ),
        "latest_access_at": summary["latest_access_at"].isoformat() if summary["latest_access_at"] else None,
        "status_distribution": [dict(row) for row in status_distribution],
        "teams": [
            {
                **dict(row),
                "last_access_at": row["last_access_at"].isoformat() if row["last_access_at"] else None,
            }
            for row in teams
        ],
    }


@router.get("/gold-team-members")
def get_gold_team_members(
    team_name_key: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    team = db.execute(
        text(
            """
            SELECT
                team_name_key,
                team_name,
                registered_users,
                accessed_users,
                not_started_users,
                submitted_users,
                viewed_activity_count,
                submitted_activity_count,
                current_team_learning_status,
                last_access_at
            FROM gold_team_learning_summary
            WHERE team_name_key = :team_name_key
            """
        ),
        {"team_name_key": team_name_key},
    ).mappings().first()

    if not team:
        raise HTTPException(status_code=404, detail="Không tìm thấy đội.")

    members = db.execute(
        text(
            """
            SELECT
                registration_id,
                participant_id,
                moodle_user_id,
                full_name,
                email,
                student_id,
                role,
                has_ever_accessed,
                first_access_at,
                last_access_at,
                days_since_last_access,
                learning_event_count,
                access_event_count,
                viewed_activity_count,
                active_days_count,
                submission_event_count,
                submission_work_event_count,
                submission_final_event_count,
                submitted_activity_count,
                submitted_activity_names,
                latest_submission_at,
                has_submitted,
                current_learning_status
            FROM gold_registered_user_learning_summary
            WHERE team_name_key = :team_name_key
            ORDER BY
                has_submitted DESC,
                has_ever_accessed DESC,
                viewed_activity_count DESC,
                learning_event_count DESC,
                full_name
            """
        ),
        {"team_name_key": team_name_key},
    ).mappings().all()

    return {
        "team": {
            **dict(team),
            "last_access_at": team["last_access_at"].isoformat() if team["last_access_at"] else None,
        },
        "members": [
            {
                **dict(row),
                "first_access_at": row["first_access_at"].isoformat() if row["first_access_at"] else None,
                "last_access_at": row["last_access_at"].isoformat() if row["last_access_at"] else None,
                "latest_submission_at": row["latest_submission_at"].isoformat()
                if row["latest_submission_at"]
                else None,
            }
            for row in members
        ],
    }


@router.get("/gold-individual-summary")
def get_gold_individual_learning_summary(db: Session = Depends(get_db)):
    summary = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_individuals,
                COUNT(*) FILTER (
                    WHERE has_moodle_participant = TRUE
                ) AS mapped_to_moodle_users,
                COUNT(*) FILTER (
                    WHERE individual_group_status = 'individual_with_moodle_group'
                ) AS individuals_with_moodle_group,
                COUNT(*) FILTER (
                    WHERE has_ever_accessed = TRUE
                ) AS accessed_individuals,
                COUNT(*) FILTER (
                    WHERE has_ever_accessed = FALSE
                ) AS not_started_individuals,
                COUNT(*) FILTER (
                    WHERE current_learning_status = 'active'
                ) AS active_individuals,
                COUNT(*) FILTER (
                    WHERE current_learning_status = 'inactive'
                ) AS inactive_individuals,
                COUNT(*) FILTER (
                    WHERE has_submitted = TRUE
                ) AS submitted_individuals,
                ROUND(AVG(viewed_activity_count)::NUMERIC, 2) AS avg_viewed_activities,
                MAX(last_access_at) AS latest_access_at
            FROM gold_individual_learning_summary
            """
        )
    ).mappings().one()

    status_distribution = db.execute(
        text(
            """
            SELECT
                current_learning_status,
                COUNT(*) AS individual_count
            FROM gold_individual_learning_summary
            GROUP BY current_learning_status
            ORDER BY individual_count DESC, current_learning_status
            """
        )
    ).mappings().all()

    individuals = db.execute(
        text(
            """
            SELECT
                full_name,
                email,
                moodle_group_name,
                individual_group_status,
                has_ever_accessed,
                viewed_activity_count,
                submitted_activity_count,
                learning_event_count,
                current_learning_status,
                last_access_at
            FROM gold_individual_learning_summary
            ORDER BY
                has_submitted DESC,
                has_ever_accessed DESC,
                viewed_activity_count DESC,
                learning_event_count DESC,
                full_name
            """
        )
    ).mappings().all()

    return {
        "total_individuals": summary["total_individuals"],
        "mapped_to_moodle_users": summary["mapped_to_moodle_users"],
        "individuals_with_moodle_group": summary["individuals_with_moodle_group"],
        "accessed_individuals": summary["accessed_individuals"],
        "not_started_individuals": summary["not_started_individuals"],
        "active_individuals": summary["active_individuals"],
        "inactive_individuals": summary["inactive_individuals"],
        "submitted_individuals": summary["submitted_individuals"],
        "avg_viewed_activities": float(summary["avg_viewed_activities"] or 0),
        "latest_access_at": summary["latest_access_at"].isoformat() if summary["latest_access_at"] else None,
        "status_distribution": [dict(row) for row in status_distribution],
        "individuals": [
            {
                **dict(row),
                "last_access_at": row["last_access_at"].isoformat() if row["last_access_at"] else None,
            }
            for row in individuals
        ],
    }


@router.get("/learning-dashboard-overview")
def get_learning_dashboard_overview(db: Session = Depends(get_db)):
    registered_summary = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_registered_users,
                COUNT(*) FILTER (WHERE has_ever_accessed = TRUE) AS accessed_users,
                COUNT(*) FILTER (WHERE has_ever_accessed = FALSE) AS not_started_users,
                COUNT(*) FILTER (WHERE has_submitted = TRUE) AS submitted_users,
                ROUND(AVG(viewed_activity_count)::NUMERIC, 2) AS avg_viewed_activities,
                MAX(last_access_at) AS latest_access_at
            FROM gold_registered_user_learning_summary
            """
        )
    ).mappings().one()

    team_summary = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_teams,
                COUNT(*) FILTER (WHERE has_any_access = TRUE) AS active_teams,
                COUNT(*) FILTER (WHERE has_any_access = FALSE) AS not_started_teams,
                COUNT(*) FILTER (WHERE has_any_submission = TRUE) AS submitted_teams
            FROM gold_team_learning_summary
            """
        )
    ).mappings().one()

    individual_summary = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_individuals,
                COUNT(*) FILTER (WHERE has_ever_accessed = TRUE) AS accessed_individuals,
                COUNT(*) FILTER (WHERE has_ever_accessed = FALSE) AS not_started_individuals,
                COUNT(*) FILTER (WHERE has_submitted = TRUE) AS submitted_individuals,
                COUNT(*) FILTER (
                    WHERE individual_group_status = 'individual_with_moodle_group'
                ) AS individuals_with_moodle_group
            FROM gold_individual_learning_summary
            """
        )
    ).mappings().one()

    activity_type_summary = db.execute(
        text(
            """
            SELECT
                COALESCE(e.activity_type, 'unknown') AS activity_type,
                COUNT(DISTINCT e.moodle_course_module_id) FILTER (
                    WHERE e.moodle_course_module_id IS NOT NULL
                ) AS activity_count,
                COUNT(*) FILTER (WHERE e.is_access_event = TRUE) AS access_event_count,
                COUNT(DISTINCT u.email) FILTER (
                    WHERE e.is_access_event = TRUE
                ) AS unique_viewers,
                COUNT(*) FILTER (
                    WHERE e.is_submission_final_event = TRUE
                ) AS submission_final_event_count,
                COUNT(DISTINCT u.email) FILTER (
                    WHERE e.is_submission_final_event = TRUE
                ) AS unique_submitters
            FROM silver_moodle_learning_events e
            JOIN gold_registered_user_learning_summary u
                ON LOWER(TRIM(e.email)) = u.email
            GROUP BY COALESCE(e.activity_type, 'unknown')
            ORDER BY access_event_count DESC, activity_type
            """
        )
    ).mappings().all()

    top_viewed_activities = db.execute(
        text(
            """
            SELECT
                e.moodle_course_module_id,
                COALESCE(e.activity_type, 'unknown') AS activity_type,
                e.activity_name,
                COUNT(*) FILTER (WHERE e.is_access_event = TRUE) AS access_event_count,
                COUNT(DISTINCT u.email) FILTER (
                    WHERE e.is_access_event = TRUE
                ) AS unique_viewers,
                MAX(e.event_time) AS last_access_at
            FROM silver_moodle_learning_events e
            JOIN gold_registered_user_learning_summary u
                ON LOWER(TRIM(e.email)) = u.email
            WHERE e.moodle_course_module_id IS NOT NULL
              AND e.activity_name IS NOT NULL
            GROUP BY
                e.moodle_course_module_id,
                COALESCE(e.activity_type, 'unknown'),
                e.activity_name
            ORDER BY unique_viewers DESC, access_event_count DESC, activity_name
            LIMIT 10
            """
        )
    ).mappings().all()

    low_attention_activities = db.execute(
        text(
            """
            SELECT
                d.moodle_course_module_id,
                COALESCE(d.activity_type, 'unknown') AS activity_type,
                d.activity_name,
                COUNT(u.email) FILTER (WHERE e.is_access_event = TRUE) AS access_event_count,
                COUNT(DISTINCT u.email) FILTER (
                    WHERE e.is_access_event = TRUE
                ) AS unique_viewers,
                MAX(e.event_time) FILTER (
                    WHERE e.is_access_event = TRUE
                      AND u.email IS NOT NULL
                ) AS last_access_at
            FROM dim_moodle_course_activities d
            LEFT JOIN silver_moodle_learning_events e
                ON d.moodle_course_module_id = e.moodle_course_module_id
            LEFT JOIN gold_registered_user_learning_summary u
                ON LOWER(TRIM(e.email)) = u.email
            WHERE d.is_learning_material = TRUE
            GROUP BY
                d.moodle_course_module_id,
                COALESCE(d.activity_type, 'unknown'),
                d.activity_name
            ORDER BY unique_viewers ASC, access_event_count ASC, activity_name
            LIMIT 10
            """
        )
    ).mappings().all()

    submission_activities = db.execute(
        text(
            """
            SELECT
                d.moodle_course_module_id,
                d.activity_name,
                COUNT(DISTINCT u.email) FILTER (
                    WHERE e.is_access_event = TRUE
                ) AS unique_viewers,
                COUNT(DISTINCT u.email) FILTER (
                    WHERE e.is_submission_final_event = TRUE
                ) AS unique_submitters,
                COUNT(u.email) FILTER (
                    WHERE e.is_submission_final_event = TRUE
                ) AS submission_final_event_count,
                MAX(e.event_time) FILTER (
                    WHERE e.is_submission_final_event = TRUE
                      AND u.email IS NOT NULL
                ) AS latest_submission_at
            FROM dim_moodle_course_activities d
            LEFT JOIN silver_moodle_learning_events e
                ON d.moodle_course_module_id = e.moodle_course_module_id
            LEFT JOIN gold_registered_user_learning_summary u
                ON LOWER(TRIM(e.email)) = u.email
            WHERE d.is_submission_activity = TRUE
            GROUP BY d.moodle_course_module_id, d.activity_name
            ORDER BY unique_submitters DESC, submission_final_event_count DESC, d.activity_name
            """
        )
    ).mappings().all()

    recent_submissions = db.execute(
        text(
            """
            SELECT
                e.event_time AS submitted_at,
                e.activity_name,
                u.full_name,
                u.email,
                u.team_name
            FROM silver_moodle_learning_events e
            JOIN gold_registered_user_learning_summary u
                ON LOWER(TRIM(e.email)) = u.email
            WHERE e.is_submission_final_event = TRUE
            ORDER BY e.event_time DESC
            LIMIT 20
            """
        )
    ).mappings().all()

    submitted_teams = db.execute(
        text(
            """
            SELECT
                team_name,
                registered_users,
                submitted_users,
                submitted_activity_count,
                submitted_activity_names,
                latest_submission_at
            FROM gold_team_learning_summary
            WHERE has_any_submission = TRUE
            ORDER BY latest_submission_at DESC, team_name
            """
        )
    ).mappings().all()

    return {
        "registered_summary": {
            "total_registered_users": registered_summary["total_registered_users"],
            "accessed_users": registered_summary["accessed_users"],
            "not_started_users": registered_summary["not_started_users"],
            "submitted_users": registered_summary["submitted_users"],
            "avg_viewed_activities": float(registered_summary["avg_viewed_activities"] or 0),
            "latest_access_at": registered_summary["latest_access_at"].isoformat()
            if registered_summary["latest_access_at"]
            else None,
        },
        "team_summary": dict(team_summary),
        "individual_summary": dict(individual_summary),
        "activity_type_summary": [dict(row) for row in activity_type_summary],
        "top_viewed_activities": [
            {
                **dict(row),
                "last_access_at": row["last_access_at"].isoformat() if row["last_access_at"] else None,
            }
            for row in top_viewed_activities
        ],
        "low_attention_activities": [
            {
                **dict(row),
                "last_access_at": row["last_access_at"].isoformat() if row["last_access_at"] else None,
            }
            for row in low_attention_activities
        ],
        "submission_activities": [
            {
                **dict(row),
                "latest_submission_at": row["latest_submission_at"].isoformat()
                if row["latest_submission_at"]
                else None,
            }
            for row in submission_activities
        ],
        "recent_submissions": [
            {
                **dict(row),
                "submitted_at": row["submitted_at"].isoformat() if row["submitted_at"] else None,
            }
            for row in recent_submissions
        ],
        "submitted_teams": [
            {
                **dict(row),
                "latest_submission_at": row["latest_submission_at"].isoformat()
                if row["latest_submission_at"]
                else None,
            }
            for row in submitted_teams
        ],
    }


@router.get("/team-activities-detail")
def get_team_activities_detail(
    team_name_key: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    team = db.execute(
        text(
            """
            SELECT
                team_name_key,
                team_name,
                registered_users,
                accessed_users,
                not_started_users,
                submitted_users,
                viewed_activity_count,
                submitted_activity_count,
                current_team_learning_status,
                last_access_at
            FROM gold_team_learning_summary
            WHERE team_name_key = :team_name_key
            """
        ),
        {"team_name_key": team_name_key},
    ).mappings().first()

    team_members = db.execute(
        text(
            """
            SELECT
                registration_id,
                full_name,
                email,
                role,
                has_ever_accessed,
                viewed_activity_count,
                learning_event_count,
                submitted_activity_count,
                current_learning_status,
                last_access_at
            FROM gold_registered_user_learning_summary
            WHERE team_name_key = :team_name_key
            ORDER BY
                has_submitted DESC,
                has_ever_accessed DESC,
                viewed_activity_count DESC,
                learning_event_count DESC,
                full_name
            """
        ),
        {"team_name_key": team_name_key},
    ).mappings().all()

    if not team or not team_members:
        raise HTTPException(status_code=404, detail="Không tìm thấy đội.")

    activities = db.execute(
        text(
            """
            SELECT 
                LOWER(TRIM(email)) AS email_key,
                moodle_course_module_id,
                MAX(activity_name) AS activity_name,
                MAX(activity_type) AS activity_type,
                MIN(event_time) AS first_access_at,
                MAX(event_time) AS last_access_at,
                COUNT(*) AS event_count,
                COUNT(*) FILTER (WHERE is_access_event = TRUE) AS access_event_count,
                COUNT(*) FILTER (WHERE is_submission_event = TRUE) AS submission_event_count,
                COUNT(*) FILTER (WHERE is_submission_final_event = TRUE) AS submission_final_event_count,
                MAX(CASE WHEN is_submission_final_event = TRUE THEN 1 ELSE 0 END) AS has_submitted,
                STRING_AGG(DISTINCT progress_signal_type, ', ' ORDER BY progress_signal_type) AS progress_signal_types
            FROM silver_moodle_learning_events
            WHERE team_name_key = :team_name_key 
              AND moodle_course_module_id IS NOT NULL
              AND activity_name IS NOT NULL
            GROUP BY LOWER(TRIM(email)), moodle_course_module_id
            ORDER BY last_access_at DESC
            """
        ),
        {"team_name_key": team_name_key},
    ).mappings().all()

    activities_by_email = {}
    for act in activities:
        email = act["email_key"]
        if email not in activities_by_email:
            activities_by_email[email] = []
        activities_by_email[email].append({
            "moodle_course_module_id": act["moodle_course_module_id"],
            "activity_name": act["activity_name"],
            "activity_type": act["activity_type"],
            "first_access_at": act["first_access_at"].isoformat() if act["first_access_at"] else None,
            "last_access_at": act["last_access_at"].isoformat() if act["last_access_at"] else None,
            "event_count": act["event_count"],
            "access_event_count": act["access_event_count"],
            "submission_event_count": act["submission_event_count"],
            "submission_final_event_count": act["submission_final_event_count"],
            "has_submitted": bool(act["has_submitted"]),
            "progress_signal_types": act["progress_signal_types"],
        })

    members_detail = []
    for member in team_members:
        email_key = member["email"].lower().strip() if member["email"] else ""
        members_detail.append({
            "full_name": member["full_name"],
            "email": member["email"],
            "role": member["role"],
            "has_ever_accessed": member["has_ever_accessed"],
            "viewed_activity_count": member["viewed_activity_count"],
            "learning_event_count": member["learning_event_count"],
            "submitted_activity_count": member["submitted_activity_count"],
            "current_learning_status": member["current_learning_status"],
            "last_access_at": member["last_access_at"].isoformat() if member["last_access_at"] else None,
            "activities": activities_by_email.get(email_key, []),
        })

    return {
        "team_name_key": team_name_key,
        "team": {
            **dict(team),
            "last_access_at": team["last_access_at"].isoformat() if team["last_access_at"] else None,
        },
        "empty_activity_note": "Những activity hoặc H5P không hiển thị nghĩa là người dùng chưa có log cho hoạt động đó.",
        "members": members_detail,
    }


@router.get("/individual-activities-detail")
def get_individual_activities_detail(
    email: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    email_key = email.lower().strip()
    user = db.execute(
        text(
            """
            SELECT
                full_name,
                email,
                role,
                has_ever_accessed,
                viewed_activity_count,
                learning_event_count,
                submitted_activity_count,
                current_learning_status,
                last_access_at
            FROM gold_individual_learning_summary
            WHERE LOWER(TRIM(email)) = :email_key
            """
        ),
        {"email_key": email_key},
    ).mappings().first()

    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy cá nhân.")

    activities = db.execute(
        text(
            """
            SELECT 
                moodle_course_module_id,
                MAX(activity_name) AS activity_name,
                MAX(activity_type) AS activity_type,
                MIN(event_time) AS first_access_at,
                MAX(event_time) AS last_access_at,
                COUNT(*) AS event_count,
                COUNT(*) FILTER (WHERE is_access_event = TRUE) AS access_event_count,
                COUNT(*) FILTER (WHERE is_submission_event = TRUE) AS submission_event_count,
                COUNT(*) FILTER (WHERE is_submission_final_event = TRUE) AS submission_final_event_count,
                MAX(CASE WHEN is_submission_final_event = TRUE THEN 1 ELSE 0 END) AS has_submitted,
                STRING_AGG(DISTINCT progress_signal_type, ', ' ORDER BY progress_signal_type) AS progress_signal_types
            FROM silver_moodle_learning_events
            WHERE LOWER(TRIM(email)) = :email_key
              AND moodle_course_module_id IS NOT NULL
              AND activity_name IS NOT NULL
            GROUP BY moodle_course_module_id
            ORDER BY last_access_at DESC
            """
        ),
        {"email_key": email_key},
    ).mappings().all()

    return {
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"],
        "has_ever_accessed": user["has_ever_accessed"],
        "viewed_activity_count": user["viewed_activity_count"],
        "learning_event_count": user["learning_event_count"],
        "submitted_activity_count": user["submitted_activity_count"],
        "current_learning_status": user["current_learning_status"],
        "last_access_at": user["last_access_at"].isoformat() if user["last_access_at"] else None,
        "empty_activity_note": "Những activity hoặc H5P không hiển thị nghĩa là người dùng chưa có log cho hoạt động đó.",
        "activities": [
            {
                "moodle_course_module_id": act["moodle_course_module_id"],
                "activity_name": act["activity_name"],
                "activity_type": act["activity_type"],
                "first_access_at": act["first_access_at"].isoformat() if act["first_access_at"] else None,
                "last_access_at": act["last_access_at"].isoformat() if act["last_access_at"] else None,
                "event_count": act["event_count"],
                "access_event_count": act["access_event_count"],
                "submission_event_count": act["submission_event_count"],
                "submission_final_event_count": act["submission_final_event_count"],
                "progress_signal_types": act["progress_signal_types"],
                "has_submitted": bool(act["has_submitted"])
            }
            for act in activities
        ]
    }

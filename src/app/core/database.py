import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

# Lấy thông tin database từ biến môi trường.
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://thinkspace:password123@localhost:5432/thinkspacedb"
)

# Nếu cấu hình không phải PostgreSQL thì dùng SQLite nhẹ cho môi trường thử nghiệm.
if not DATABASE_URL.startswith("postgresql"):
    DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL)

if DATABASE_URL.startswith("postgresql"):
    @event.listens_for(engine, "connect")
    def set_postgresql_search_path(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("SET search_path TO public")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

REGISTRATION_LONG_TEXT_COLUMNS = (
    "team_name",
    "project_domain",
    "source",
)


def ensure_registration_text_columns() -> None:
    """
    Giữ database PostgreSQL cũ tương thích với model SQLAlchemy hiện tại.
    create_all() không tự sửa kiểu cột đã tồn tại, nên cần nới các cột có thể
    chứa câu trả lời dài trước khi người dùng upload file mới.
    """
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        table_exists = connection.execute(
            text("SELECT to_regclass('public.registrations')")
        ).scalar()
        if not table_exists:
            return

        for column_name in REGISTRATION_LONG_TEXT_COLUMNS:
            data_type = connection.execute(
                text(
                    """
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'registrations'
                      AND column_name = :column_name
                    """
                ),
                {"column_name": column_name},
            ).scalar()
            if data_type == "text":
                continue

            connection.execute(
                text(
                    f"ALTER TABLE registrations "
                    f"ALTER COLUMN {column_name} TYPE TEXT "
                    f"USING {column_name}::TEXT"
                )
            )


def ensure_moodle_log_bronze_columns() -> None:
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        table_exists = connection.execute(
            text("SELECT to_regclass('public.bronze_moodle_log_events')")
        ).scalar()
        if not table_exists:
            return

        column_exists = connection.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'bronze_moodle_log_events'
                  AND column_name = 'source_row_number'
                """
            )
        ).scalar()

        if not column_exists:
            connection.execute(
                text("ALTER TABLE bronze_moodle_log_events ADD COLUMN source_row_number INTEGER")
            )


def ensure_moodle_identity_map_view() -> None:
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        required_tables = (
            "raw_moodle_participants",
            "registrations",
        )
        for table_name in required_tables:
            table_exists = connection.execute(
                text(f"SELECT to_regclass('public.{table_name}')")
            ).scalar()
            if not table_exists:
                return

        connection.execute(
            text(
                """
                CREATE OR REPLACE VIEW int_moodle_user_identity_map AS
                SELECT
                    p.id AS participant_id,
                    p.raw_file_id AS participant_file_id,
                    p.course_id,
                    p.moodle_full_name,
                    p.moodle_full_name_key,
                    p.email,
                    p.moodle_group_name,
                    r.id AS registration_id,
                    r.full_name AS registration_full_name,
                    r.student_id,
                    r.role,
                    r.team_name AS registration_team_name,
                    CASE
                        WHEN r.id IS NULL THEN 'unmatched_registration'
                        WHEN NULLIF(TRIM(COALESCE(p.moodle_group_name, '')), '') IS NULL THEN 'matched_without_moodle_group'
                        WHEN NULLIF(TRIM(COALESCE(r.team_name, '')), '') IS NULL THEN 'matched_without_registration_team'
                        WHEN LOWER(TRIM(p.moodle_group_name)) = LOWER(TRIM(r.team_name)) THEN 'matched_same_team'
                        ELSE 'matched_team_conflict'
                    END AS identity_status,
                    p.loaded_at
                FROM raw_moodle_participants p
                LEFT JOIN registrations r
                    ON LOWER(TRIM(p.email)) = LOWER(TRIM(r.email))
                """
            )
        )


def ensure_moodle_silver_learning_events_view() -> None:
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        required_relations = (
            "bronze_moodle_log_events",
            "int_moodle_user_identity_map",
        )
        for relation_name in required_relations:
            relation_exists = connection.execute(
                text(f"SELECT to_regclass('public.{relation_name}')")
            ).scalar()
            if not relation_exists:
                return

        connection.execute(text("DROP VIEW IF EXISTS silver_moodle_learning_events CASCADE"))
        connection.execute(
            text(
                """
                CREATE OR REPLACE VIEW silver_moodle_learning_events AS
                SELECT
                    b.id AS bronze_event_id,
                    b.raw_file_id,
                    b.source_row_number,
                    b.event_time,
                    CAST(b.event_time AS DATE) AS event_date,
                    b.moodle_user_id,
                    m.participant_id,
                    m.registration_id,
                    COALESCE(
                        NULLIF(TRIM(m.registration_full_name), ''),
                        NULLIF(TRIM(m.moodle_full_name), ''),
                        NULLIF(TRIM(b.user_full_name_raw), '')
                    ) AS full_name,
                    m.email,
                    m.student_id,
                    m.role,
                    COALESCE(
                        NULLIF(TRIM(m.registration_team_name), ''),
                        NULLIF(TRIM(m.moodle_group_name), '')
                    ) AS team_name,
                    LOWER(
                        COALESCE(
                            NULLIF(TRIM(m.registration_team_name), ''),
                            NULLIF(TRIM(m.moodle_group_name), '')
                        )
                    ) AS team_name_key,
                    COALESCE(b.moodle_course_id, m.course_id) AS moodle_course_id,
                    b.moodle_course_module_id,
                    b.component_raw AS component,
                    NULLIF(TRIM(b.context_type), '') AS activity_type,
                    NULLIF(TRIM(b.context_name), '') AS activity_name,
                    b.event_name_raw AS event_name,
                    b.event_category,
                    b.is_learning_event,
                    b.event_name_raw IN (
                        'Course viewed',
                        'Course module viewed',
                        'Section viewed',
                        'H5P content viewed',
                        'xAPI statement received',
                        'The status of the submission has been viewed.',
                        'Submission form viewed.',
                        'SCO launched',
                        'SCORM status submitted',
                        'SCORM raw score submitted',
                        'Quiz attempt viewed',
                        'Quiz attempt reviewed',
                        'Quiz attempt started',
                        'Quiz attempt summary viewed'
                    ) AS is_view_event,
                    b.event_name_raw IN (
                        'Course viewed',
                        'Course module viewed',
                        'Section viewed',
                        'H5P content viewed',
                        'xAPI statement received',
                        'The status of the submission has been viewed.',
                        'Submission form viewed.',
                        'SCO launched',
                        'SCORM status submitted',
                        'SCORM raw score submitted',
                        'Quiz attempt viewed',
                        'Quiz attempt reviewed',
                        'Quiz attempt started',
                        'Quiz attempt summary viewed'
                    ) AS is_access_event,
                    b.event_name_raw IN (
                        'Submission created.',
                        'Submission updated.',
                        'A file has been uploaded.',
                        'An online text has been uploaded.',
                        'A submission has been submitted.',
                        'The status of the submission has been updated.',
                        'Quiz attempt submitted',
                        'Course module completion updated'
                    ) AS is_submission_event,
                    b.event_name_raw IN (
                        'A submission has been submitted.',
                        'Quiz attempt submitted',
                        'Course module completion updated'
                    ) AS is_submission_final_event,
                    b.event_name_raw IN (
                        'A submission has been submitted.',
                        'Quiz attempt submitted',
                        'Course module completion updated'
                    ) AS is_completion_event,
                    CASE
                        WHEN b.event_name_raw IN (
                            'A submission has been submitted.',
                            'Quiz attempt submitted',
                            'Course module completion updated'
                        ) THEN 'submission_final'
                        WHEN b.event_name_raw IN (
                            'Submission created.',
                            'Submission updated.',
                            'A file has been uploaded.',
                            'An online text has been uploaded.',
                            'The status of the submission has been updated.'
                        ) THEN 'submission_work'
                        WHEN b.event_name_raw IN (
                            'Course viewed',
                            'Course module viewed',
                            'Section viewed',
                            'H5P content viewed',
                            'xAPI statement received',
                            'The status of the submission has been viewed.',
                            'Submission form viewed.',
                            'SCO launched',
                            'SCORM status submitted',
                            'SCORM raw score submitted',
                            'Quiz attempt viewed',
                            'Quiz attempt reviewed',
                            'Quiz attempt started',
                            'Quiz attempt summary viewed'
                        ) THEN 'access'
                        ELSE 'other_learning'
                    END AS progress_signal_type,
                    b.origin_raw AS origin,
                    m.identity_status,
                    b.loaded_at
                FROM bronze_moodle_log_events b
                LEFT JOIN int_moodle_user_identity_map m
                    ON LOWER(TRIM(b.user_full_name_raw)) = m.moodle_full_name_key
                WHERE b.is_learning_event = TRUE
                  AND b.moodle_user_id IS NOT NULL
                """
            )
        )


def ensure_moodle_course_activities_view() -> None:
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        relation_exists = connection.execute(
            text("SELECT to_regclass('public.bronze_moodle_log_events')")
        ).scalar()
        if not relation_exists:
            return

        connection.execute(
            text(
                """
                CREATE OR REPLACE VIEW dim_moodle_course_activities AS
                WITH module_context_counts AS (
                    SELECT
                        moodle_course_module_id,
                        COALESCE(moodle_course_id, 12) AS moodle_course_id,
                        NULLIF(TRIM(context_type), '') AS activity_type,
                        NULLIF(TRIM(context_name), '') AS activity_name,
                        COUNT(*) AS context_event_count,
                        ROW_NUMBER() OVER (
                            PARTITION BY moodle_course_module_id
                            ORDER BY COUNT(*) DESC, MAX(event_time) DESC
                        ) AS context_rank
                    FROM bronze_moodle_log_events
                    WHERE moodle_course_module_id IS NOT NULL
                    GROUP BY
                        moodle_course_module_id,
                        COALESCE(moodle_course_id, 12),
                        NULLIF(TRIM(context_type), ''),
                        NULLIF(TRIM(context_name), '')
                ),
                module_stats AS (
                    SELECT
                        moodle_course_module_id,
                        MIN(event_time) AS first_seen_at,
                        MAX(event_time) AS last_seen_at,
                        COUNT(*) AS total_event_rows,
                        COUNT(*) FILTER (WHERE is_learning_event = TRUE) AS learning_event_rows,
                        COUNT(DISTINCT moodle_user_id) FILTER (
                            WHERE is_learning_event = TRUE
                              AND moodle_user_id IS NOT NULL
                        ) AS unique_learning_users,
                        COUNT(*) FILTER (
                            WHERE event_name_raw = 'A submission has been submitted.'
                        ) AS submission_final_event_rows,
                        COUNT(DISTINCT moodle_user_id) FILTER (
                            WHERE event_name_raw = 'A submission has been submitted.'
                              AND moodle_user_id IS NOT NULL
                        ) AS unique_submitters
                    FROM bronze_moodle_log_events
                    WHERE moodle_course_module_id IS NOT NULL
                    GROUP BY moodle_course_module_id
                )
                SELECT
                    c.moodle_course_module_id,
                    c.moodle_course_id,
                    c.activity_type,
                    c.activity_name,
                    LOWER(TRIM(COALESCE(c.activity_type, 'unknown'))) AS activity_type_key,
                    LOWER(TRIM(COALESCE(c.activity_name, 'unknown'))) AS activity_name_key,
                    c.activity_type = 'Assignment' AS is_submission_activity,
                    c.activity_type IN ('Page', 'File', 'Forum', 'H5P')
                        OR c.activity_name ILIKE '%guideline%'
                        OR c.activity_name ILIKE '%handbook%'
                        OR c.activity_name ILIKE '%read me%' AS is_learning_material,
                    s.total_event_rows,
                    s.learning_event_rows,
                    s.unique_learning_users,
                    s.submission_final_event_rows,
                    s.unique_submitters,
                    s.first_seen_at,
                    s.last_seen_at
                FROM module_context_counts c
                JOIN module_stats s
                    ON s.moodle_course_module_id = c.moodle_course_module_id
                WHERE c.context_rank = 1
                """
            )
        )


def ensure_gold_user_learning_summary_view() -> None:
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        required_relations = (
            "int_moodle_user_identity_map",
            "silver_moodle_learning_events",
        )
        for relation_name in required_relations:
            relation_exists = connection.execute(
                text(f"SELECT to_regclass('public.{relation_name}')")
            ).scalar()
            if not relation_exists:
                return

        connection.execute(text("DROP VIEW IF EXISTS gold_user_learning_summary CASCADE"))
        connection.execute(
            text(
                """
                CREATE OR REPLACE VIEW gold_user_learning_summary AS
                WITH user_event_summary AS (
                    SELECT
                        email,
                        MAX(moodle_course_id) AS moodle_course_id,
                        MAX(moodle_user_id) AS moodle_user_id,
                        MIN(event_time) AS first_access_at,
                        MAX(event_time) AS last_access_at,
                        MAX(event_time) FILTER (
                            WHERE is_submission_final_event = TRUE
                        ) AS latest_submission_at,
                        COUNT(*) AS learning_event_count,
                        COUNT(*) FILTER (
                            WHERE is_access_event = TRUE
                        ) AS access_event_count,
                        COUNT(*) FILTER (
                            WHERE is_submission_event = TRUE
                        ) AS submission_event_count,
                        COUNT(*) FILTER (
                            WHERE progress_signal_type = 'submission_work'
                        ) AS submission_work_event_count,
                        COUNT(*) FILTER (
                            WHERE is_submission_final_event = TRUE
                        ) AS submission_final_event_count,
                        COUNT(DISTINCT event_date) AS active_days_count,
                        COUNT(DISTINCT moodle_course_module_id) FILTER (
                            WHERE is_access_event = TRUE
                              AND moodle_course_module_id IS NOT NULL
                        ) AS viewed_activity_count,
                        COUNT(DISTINCT moodle_course_module_id) FILTER (
                            WHERE is_submission_final_event = TRUE
                              AND moodle_course_module_id IS NOT NULL
                        ) AS submitted_activity_count,
                        STRING_AGG(
                            DISTINCT activity_name,
                            ', ' ORDER BY activity_name
                        ) FILTER (
                            WHERE is_submission_final_event = TRUE
                              AND activity_name IS NOT NULL
                        ) AS submitted_activity_names
                    FROM silver_moodle_learning_events
                    WHERE email IS NOT NULL
                    GROUP BY email
                )
                SELECT
                    CURRENT_DATE AS snapshot_date,
                    COALESCE(m.course_id, s.moodle_course_id, 12) AS moodle_course_id,
                    m.participant_id,
                    m.registration_id,
                    s.moodle_user_id,
                    COALESCE(
                        NULLIF(TRIM(m.registration_full_name), ''),
                        NULLIF(TRIM(m.moodle_full_name), '')
                    ) AS full_name,
                    m.email,
                    m.student_id,
                    m.role,
                    COALESCE(
                        NULLIF(TRIM(m.registration_team_name), ''),
                        NULLIF(TRIM(m.moodle_group_name), '')
                    ) AS team_name,
                    LOWER(
                        COALESCE(
                            NULLIF(TRIM(m.registration_team_name), ''),
                            NULLIF(TRIM(m.moodle_group_name), '')
                        )
                    ) AS team_name_key,
                    m.identity_status,
                    COALESCE(s.learning_event_count, 0) > 0 AS has_ever_accessed,
                    s.first_access_at,
                    s.last_access_at,
                    CASE
                        WHEN s.last_access_at IS NULL THEN NULL
                        ELSE CURRENT_DATE - CAST(s.last_access_at AS DATE)
                    END AS days_since_last_access,
                    COALESCE(s.learning_event_count, 0) AS learning_event_count,
                    COALESCE(s.access_event_count, 0) AS access_event_count,
                    COALESCE(s.viewed_activity_count, 0) AS viewed_activity_count,
                    COALESCE(s.active_days_count, 0) AS active_days_count,
                    COALESCE(s.submission_event_count, 0) AS submission_event_count,
                    COALESCE(s.submission_work_event_count, 0) AS submission_work_event_count,
                    COALESCE(s.submission_final_event_count, 0) AS submission_final_event_count,
                    COALESCE(s.submitted_activity_count, 0) AS submitted_activity_count,
                    s.submitted_activity_names,
                    s.latest_submission_at,
                    COALESCE(s.submission_final_event_count, 0) > 0 AS has_submitted,
                    CASE
                        WHEN COALESCE(s.learning_event_count, 0) = 0 THEN 'not_started'
                        WHEN COALESCE(s.submission_final_event_count, 0) > 0 THEN 'submitted'
                        WHEN CAST(s.last_access_at AS DATE) >= CURRENT_DATE - INTERVAL '7 days' THEN 'active'
                        ELSE 'inactive'
                    END AS current_learning_status
                FROM int_moodle_user_identity_map m
                LEFT JOIN user_event_summary s
                    ON LOWER(TRIM(m.email)) = LOWER(TRIM(s.email))
                """
            )
        )


def ensure_gold_registered_user_learning_summary_view() -> None:
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        required_relations = (
            "registrations",
            "int_moodle_user_identity_map",
            "silver_moodle_learning_events",
        )
        for relation_name in required_relations:
            relation_exists = connection.execute(
                text(f"SELECT to_regclass('public.{relation_name}')")
            ).scalar()
            if not relation_exists:
                return

        connection.execute(text("DROP VIEW IF EXISTS gold_registered_user_learning_summary CASCADE"))
        connection.execute(
            text(
                """
                CREATE OR REPLACE VIEW gold_registered_user_learning_summary AS
                WITH identity_one AS (
                    SELECT *
                    FROM (
                        SELECT
                            m.*,
                            ROW_NUMBER() OVER (
                                PARTITION BY LOWER(TRIM(m.email))
                                ORDER BY
                                    CASE
                                        WHEN m.registration_id IS NOT NULL THEN 0
                                        ELSE 1
                                    END,
                                    m.participant_id
                            ) AS identity_rank
                        FROM int_moodle_user_identity_map m
                        WHERE NULLIF(TRIM(m.email), '') IS NOT NULL
                    ) ranked
                    WHERE identity_rank = 1
                ),
                registered_event_summary AS (
                    SELECT
                        LOWER(TRIM(email)) AS email_key,
                        MAX(moodle_course_id) AS moodle_course_id,
                        MAX(moodle_user_id) AS moodle_user_id,
                        MIN(event_time) AS first_access_at,
                        MAX(event_time) AS last_access_at,
                        MAX(event_time) FILTER (
                            WHERE is_submission_final_event = TRUE
                        ) AS latest_submission_at,
                        COUNT(*) AS learning_event_count,
                        COUNT(*) FILTER (
                            WHERE is_access_event = TRUE
                        ) AS access_event_count,
                        COUNT(*) FILTER (
                            WHERE is_submission_event = TRUE
                        ) AS submission_event_count,
                        COUNT(*) FILTER (
                            WHERE progress_signal_type = 'submission_work'
                        ) AS submission_work_event_count,
                        COUNT(*) FILTER (
                            WHERE is_submission_final_event = TRUE
                        ) AS submission_final_event_count,
                        COUNT(DISTINCT event_date) AS active_days_count,
                        COUNT(DISTINCT moodle_course_module_id) FILTER (
                            WHERE is_access_event = TRUE
                              AND moodle_course_module_id IS NOT NULL
                        ) AS viewed_activity_count,
                        COUNT(DISTINCT moodle_course_module_id) FILTER (
                            WHERE is_submission_final_event = TRUE
                              AND moodle_course_module_id IS NOT NULL
                        ) AS submitted_activity_count,
                        STRING_AGG(
                            DISTINCT activity_name,
                            ', ' ORDER BY activity_name
                        ) FILTER (
                            WHERE is_submission_final_event = TRUE
                              AND activity_name IS NOT NULL
                        ) AS submitted_activity_names
                    FROM silver_moodle_learning_events
                    WHERE NULLIF(TRIM(email), '') IS NOT NULL
                    GROUP BY LOWER(TRIM(email))
                )
                SELECT
                    CURRENT_DATE AS snapshot_date,
                    COALESCE(i.course_id, s.moodle_course_id, 12) AS moodle_course_id,
                    r.id AS registration_id,
                    i.participant_id,
                    s.moodle_user_id,
                    r.full_name,
                    LOWER(TRIM(r.email)) AS email,
                    r.student_id,
                    r.role,
                    NULLIF(TRIM(r.team_name), '') AS team_name,
                    LOWER(NULLIF(TRIM(r.team_name), '')) AS team_name_key,
                    COALESCE(i.moodle_full_name, r.full_name) AS moodle_full_name,
                    i.moodle_group_name,
                    COALESCE(i.identity_status, 'missing_moodle_participant') AS identity_status,
                    i.participant_id IS NOT NULL AS has_moodle_participant,
                    COALESCE(s.learning_event_count, 0) > 0 AS has_ever_accessed,
                    s.first_access_at,
                    s.last_access_at,
                    CASE
                        WHEN s.last_access_at IS NULL THEN NULL
                        ELSE CURRENT_DATE - CAST(s.last_access_at AS DATE)
                    END AS days_since_last_access,
                    COALESCE(s.learning_event_count, 0) AS learning_event_count,
                    COALESCE(s.access_event_count, 0) AS access_event_count,
                    COALESCE(s.viewed_activity_count, 0) AS viewed_activity_count,
                    COALESCE(s.active_days_count, 0) AS active_days_count,
                    COALESCE(s.submission_event_count, 0) AS submission_event_count,
                    COALESCE(s.submission_work_event_count, 0) AS submission_work_event_count,
                    COALESCE(s.submission_final_event_count, 0) AS submission_final_event_count,
                    COALESCE(s.submitted_activity_count, 0) AS submitted_activity_count,
                    s.submitted_activity_names,
                    s.latest_submission_at,
                    COALESCE(s.submission_final_event_count, 0) > 0 AS has_submitted,
                    CASE
                        WHEN COALESCE(s.learning_event_count, 0) = 0 THEN 'not_started'
                        WHEN COALESCE(s.submission_final_event_count, 0) > 0 THEN 'submitted'
                        WHEN CAST(s.last_access_at AS DATE) >= CURRENT_DATE - INTERVAL '7 days' THEN 'active'
                        ELSE 'inactive'
                    END AS current_learning_status
                FROM registrations r
                LEFT JOIN identity_one i
                    ON LOWER(TRIM(r.email)) = LOWER(TRIM(i.email))
                LEFT JOIN registered_event_summary s
                    ON LOWER(TRIM(r.email)) = s.email_key
                WHERE NULLIF(TRIM(r.email), '') IS NOT NULL
                """
            )
        )


def ensure_gold_team_learning_summary_view() -> None:
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        required_relations = (
            "gold_registered_user_learning_summary",
            "silver_moodle_learning_events",
        )
        for relation_name in required_relations:
            relation_exists = connection.execute(
                text(f"SELECT to_regclass('public.{relation_name}')")
            ).scalar()
            if not relation_exists:
                return

        connection.execute(text("DROP VIEW IF EXISTS gold_team_learning_summary CASCADE"))
        connection.execute(
            text(
                """
                CREATE OR REPLACE VIEW gold_team_learning_summary AS
                WITH registered_team_users AS (
                    SELECT *
                    FROM gold_registered_user_learning_summary
                    WHERE team_name_key IS NOT NULL
                ),
                registered_team_events AS (
                    SELECT
                        u.team_name_key,
                        COUNT(DISTINCT e.moodle_course_module_id) FILTER (
                            WHERE e.is_access_event = TRUE
                              AND e.moodle_course_module_id IS NOT NULL
                        ) AS team_viewed_activity_count,
                        COUNT(DISTINCT e.moodle_course_module_id) FILTER (
                            WHERE e.is_submission_final_event = TRUE
                              AND e.moodle_course_module_id IS NOT NULL
                        ) AS team_submitted_activity_count,
                        STRING_AGG(
                            DISTINCT e.activity_name,
                            ', ' ORDER BY e.activity_name
                        ) FILTER (
                            WHERE e.is_submission_final_event = TRUE
                              AND e.activity_name IS NOT NULL
                        ) AS team_submitted_activity_names
                    FROM registered_team_users u
                    JOIN silver_moodle_learning_events e
                        ON u.email = LOWER(TRIM(e.email))
                    GROUP BY u.team_name_key
                )
                SELECT
                    CURRENT_DATE AS snapshot_date,
                    COALESCE(MAX(u.moodle_course_id), 12) AS moodle_course_id,
                    u.team_name_key,
                    MIN(u.team_name) AS team_name,
                    COUNT(*) AS registered_users,
                    COUNT(*) FILTER (
                        WHERE u.has_moodle_participant = TRUE
                    ) AS mapped_to_moodle_users,
                    COUNT(*) FILTER (
                        WHERE u.has_ever_accessed = TRUE
                    ) AS accessed_users,
                    COUNT(*) FILTER (
                        WHERE u.has_ever_accessed = FALSE
                    ) AS not_started_users,
                    COUNT(*) FILTER (
                        WHERE u.current_learning_status = 'active'
                    ) AS active_users,
                    COUNT(*) FILTER (
                        WHERE u.current_learning_status = 'inactive'
                    ) AS inactive_users,
                    COUNT(*) FILTER (
                        WHERE u.has_submitted = TRUE
                    ) AS submitted_users,
                    COALESCE(SUM(u.learning_event_count), 0) AS learning_event_count,
                    COALESCE(SUM(u.access_event_count), 0) AS access_event_count,
                    COALESCE(SUM(u.submission_event_count), 0) AS submission_event_count,
                    COALESCE(SUM(u.submission_work_event_count), 0) AS submission_work_event_count,
                    COALESCE(SUM(u.submission_final_event_count), 0) AS submission_final_event_count,
                    COALESCE(SUM(u.active_days_count), 0) AS active_days_count,
                    COALESCE(e.team_viewed_activity_count, 0) AS viewed_activity_count,
                    COALESCE(SUM(u.viewed_activity_count), 0) AS total_user_viewed_activity_count,
                    COALESCE(e.team_submitted_activity_count, 0) AS submitted_activity_count,
                    e.team_submitted_activity_names AS submitted_activity_names,
                    ROUND(AVG(u.viewed_activity_count)::NUMERIC, 2) AS avg_viewed_activities_per_user,
                    MIN(u.first_access_at) AS first_access_at,
                    MAX(u.last_access_at) AS last_access_at,
                    MAX(u.latest_submission_at) AS latest_submission_at,
                    CASE
                        WHEN MAX(u.last_access_at) IS NULL THEN NULL
                        ELSE CURRENT_DATE - CAST(MAX(u.last_access_at) AS DATE)
                    END AS days_since_last_team_access,
                    COUNT(*) FILTER (
                        WHERE u.has_ever_accessed = TRUE
                    ) > 0 AS has_any_access,
                    COUNT(*) FILTER (
                        WHERE u.has_submitted = TRUE
                    ) > 0 AS has_any_submission,
                    CASE
                        WHEN COUNT(*) FILTER (WHERE u.has_submitted = TRUE) > 0 THEN 'submitted'
                        WHEN COUNT(*) FILTER (WHERE u.has_ever_accessed = TRUE) = 0 THEN 'not_started'
                        WHEN COUNT(*) FILTER (WHERE u.current_learning_status = 'active') > 0 THEN 'active'
                        ELSE 'inactive'
                    END AS current_team_learning_status
                FROM registered_team_users u
                LEFT JOIN registered_team_events e
                    ON u.team_name_key = e.team_name_key
                GROUP BY
                    u.team_name_key,
                    e.team_viewed_activity_count,
                    e.team_submitted_activity_count,
                    e.team_submitted_activity_names
                """
            )
        )


def ensure_gold_individual_learning_summary_view() -> None:
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        relation_exists = connection.execute(
            text("SELECT to_regclass('public.gold_registered_user_learning_summary')")
        ).scalar()
        if not relation_exists:
            return

        connection.execute(text("DROP VIEW IF EXISTS gold_individual_learning_summary CASCADE"))
        connection.execute(
            text(
                """
                CREATE OR REPLACE VIEW gold_individual_learning_summary AS
                SELECT
                    snapshot_date,
                    moodle_course_id,
                    registration_id,
                    participant_id,
                    moodle_user_id,
                    full_name,
                    email,
                    student_id,
                    role,
                    moodle_full_name,
                    moodle_group_name,
                    CASE
                        WHEN NULLIF(TRIM(moodle_group_name), '') IS NOT NULL
                            THEN 'individual_with_moodle_group'
                        ELSE 'individual_solo'
                    END AS individual_group_status,
                    identity_status,
                    has_moodle_participant,
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
                WHERE team_name_key IS NULL
                """
            )
        )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

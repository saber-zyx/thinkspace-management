WITH learner_flags AS (
    SELECT
        u.registration_id,
        u.full_name,
        u.email,
        u.role,
        COALESCE(NULLIF(u.team_name, ''), 'Cá nhân tự do') AS project_name,
        u.has_ever_accessed,
        u.last_access_at,
        u.viewed_activity_count,
        u.learning_event_count,
        COUNT(*) FILTER (
            WHERE e.moodle_course_module_id = 707
              AND e.is_access_event = TRUE
        ) AS pre_program_survey_view_count,
        COUNT(DISTINCT e.moodle_course_module_id) FILTER (
            WHERE e.moodle_course_module_id IN (
                650, 653, 656, 659, 662, 665,
                651, 654, 657, 660, 663, 666,
                714, 716
            )
              AND e.is_access_event = TRUE
        ) AS milestone_fmc3_module_count,
        COUNT(*) FILTER (
            WHERE e.moodle_course_module_id IN (
                650, 653, 656, 659, 662, 665,
                651, 654, 657, 660, 663, 666,
                714, 716
            )
              AND e.is_access_event = TRUE
        ) AS milestone_fmc3_view_count
    FROM gold_registered_user_learning_summary u
    LEFT JOIN silver_moodle_learning_events e
        ON LOWER(TRIM(e.email)) = u.email
    GROUP BY
        u.registration_id,
        u.full_name,
        u.email,
        u.role,
        COALESCE(NULLIF(u.team_name, ''), 'Cá nhân tự do'),
        u.has_ever_accessed,
        u.last_access_at,
        u.viewed_activity_count,
        u.learning_event_count
),
reminder_segments AS (
    SELECT
        registration_id,
        full_name,
        email,
        role,
        project_name,
        CASE
            WHEN has_ever_accessed THEN 'Đã có hoạt động'
            ELSE 'Chưa có hoạt động'
        END AS thinkspace_access_status,
        COALESCE(viewed_activity_count, 0) AS viewed_activity_count,
        COALESCE(learning_event_count, 0) AS learning_event_count,
        pre_program_survey_view_count,
        milestone_fmc3_module_count,
        milestone_fmc3_view_count,
        last_access_at,
        CONCAT_WS('; ',
            CASE
                WHEN has_ever_accessed = FALSE
                    THEN 'Chưa có bất kỳ hoạt động nào trên ThinkSpace/Moodle'
            END,
            CASE
                WHEN has_ever_accessed = TRUE AND pre_program_survey_view_count = 0
                    THEN 'Đã vào ThinkSpace nhưng chưa vào Pre-Program Survey'
                WHEN has_ever_accessed = FALSE
                    THEN 'Chưa vào Pre-Program Survey'
            END,
            CASE
                WHEN milestone_fmc3_module_count = 0
                    THEN 'Chưa có hoạt động ở các milestone hoặc khóa entrepreneurship/FMC3'
            END
        ) AS reminder_reason,
        CASE
            WHEN has_ever_accessed = FALSE THEN 'Cao'
            WHEN pre_program_survey_view_count = 0
             AND milestone_fmc3_module_count = 0 THEN 'Cao'
            WHEN pre_program_survey_view_count = 0 THEN 'Vừa'
            WHEN milestone_fmc3_module_count = 0 THEN 'Vừa'
            ELSE 'Thấp'
        END AS reminder_priority
    FROM learner_flags
)
SELECT
    registration_id,
    full_name,
    email,
    role,
    project_name,
    thinkspace_access_status,
    viewed_activity_count,
    learning_event_count,
    pre_program_survey_view_count,
    milestone_fmc3_module_count,
    milestone_fmc3_view_count,
    last_access_at,
    reminder_priority,
    reminder_reason
FROM reminder_segments
WHERE thinkspace_access_status = 'Chưa có hoạt động'
   OR pre_program_survey_view_count = 0
   OR milestone_fmc3_module_count = 0
ORDER BY
    CASE reminder_priority
        WHEN 'Cao' THEN 1
        WHEN 'Vừa' THEN 2
        ELSE 3
    END,
    thinkspace_access_status DESC,
    project_name,
    full_name,
    email;

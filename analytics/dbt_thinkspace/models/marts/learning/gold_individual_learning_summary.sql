{{ config(materialized='view', alias='gold_individual_learning_summary') }}

select
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
    case
        when nullif(trim(moodle_group_name), '') is not null
            then 'individual_with_moodle_group'
        else 'individual_solo'
    end as individual_group_status,
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
from {{ ref('gold_registered_user_learning_summary') }}
where team_name_key is null

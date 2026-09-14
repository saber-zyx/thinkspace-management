{{ config(materialized='view', alias='gold_team_learning_summary') }}

with project_summary as (
    select *
    from {{ ref('gold_project_learning_summary') }}
    where project_type = 'team'
)

select
    snapshot_date,
    moodle_course_id,
    project_key as team_name_key,
    project_name as team_name,
    registered_users,
    mapped_to_moodle_users,
    accessed_users,
    not_started_users,
    active_users,
    inactive_users,
    submitted_users,
    learning_event_count,
    access_event_count,
    submission_event_count,
    submission_work_event_count,
    submission_final_event_count,
    active_days_count,
    viewed_activity_count,
    total_user_viewed_activity_count,
    submitted_activity_count,
    submitted_activity_names,
    avg_viewed_activities_per_user,
    first_access_at,
    last_access_at,
    latest_submission_at,
    days_since_last_project_access as days_since_last_team_access,
    has_any_access,
    has_any_submission,
    current_project_learning_status as current_team_learning_status
from project_summary

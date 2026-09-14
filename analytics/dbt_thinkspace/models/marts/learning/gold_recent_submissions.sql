{{ config(materialized='view', alias='gold_recent_submissions') }}

with learning_events as (
    select *
    from {{ ref('silver_moodle_learning_events') }}
),

registered_users as (
    select *
    from {{ ref('gold_registered_user_learning_summary') }}
),

recent_submissions as (
    select
        e.bronze_event_id,
        e.event_time as submitted_at,
        e.moodle_course_module_id,
        e.activity_name,
        u.full_name,
        u.email,
        u.team_name
    from learning_events e
    join registered_users u
        on lower(trim(e.email)) = u.email
    where e.is_submission_final_event = true
)

select *
from recent_submissions

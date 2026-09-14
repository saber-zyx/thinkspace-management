{{ config(materialized='view', alias='gold_learning_activity_detail') }}

with learning_events as (
    select *
    from {{ ref('silver_moodle_learning_events') }}
),

registered_users as (
    select *
    from {{ ref('gold_registered_user_learning_summary') }}
),

activity_detail as (
    select
        md5(
            coalesce(u.email, '') || '|' || coalesce(e.moodle_course_module_id::text, '')
        ) as activity_detail_key,
        u.registration_id,
        u.full_name,
        u.email,
        lower(trim(u.email)) as email_key,
        u.role,
        u.team_name,
        u.team_name_key,
        e.moodle_course_module_id,
        max(e.activity_name) as activity_name,
        max(e.activity_type) as activity_type,
        min(e.event_time) as first_access_at,
        max(e.event_time) as last_access_at,
        count(*) as event_count,
        count(*) filter (
            where e.is_access_event = true
        ) as access_event_count,
        count(*) filter (
            where e.is_submission_event = true
        ) as submission_event_count,
        count(*) filter (
            where e.progress_signal_type = 'submission_work'
        ) as submission_work_event_count,
        count(*) filter (
            where e.is_submission_final_event = true
        ) as submission_final_event_count,
        max(case when e.is_submission_final_event = true then 1 else 0 end) as has_submitted,
        string_agg(
            distinct e.progress_signal_type,
            ', ' order by e.progress_signal_type
        ) as progress_signal_types
    from learning_events e
    join registered_users u
        on lower(trim(e.email)) = u.email
    where e.moodle_course_module_id is not null
      and e.activity_name is not null
    group by
        u.registration_id,
        u.full_name,
        u.email,
        lower(trim(u.email)),
        u.role,
        u.team_name,
        u.team_name_key,
        e.moodle_course_module_id
)

select *
from activity_detail

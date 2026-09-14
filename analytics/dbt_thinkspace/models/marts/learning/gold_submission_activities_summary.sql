{{ config(materialized='view', alias='gold_submission_activities_summary') }}

select
    d.moodle_course_module_id,
    d.activity_name,
    count(distinct u.email) filter (
        where e.is_access_event = true
    ) as unique_viewers,
    count(distinct u.email) filter (
        where e.is_submission_final_event = true
    ) as unique_submitters,
    count(u.email) filter (
        where e.is_submission_final_event = true
    ) as submission_final_event_count,
    max(e.event_time) filter (
        where e.is_submission_final_event = true
          and u.email is not null
    ) as latest_submission_at
from {{ ref('dim_moodle_course_activities') }} d
left join {{ ref('silver_moodle_learning_events') }} e
    on d.moodle_course_module_id = e.moodle_course_module_id
left join {{ ref('gold_registered_user_learning_summary') }} u
    on lower(trim(e.email)) = u.email
where d.is_submission_activity = true
group by d.moodle_course_module_id, d.activity_name

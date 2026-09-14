{{ config(materialized='view', alias='gold_activity_type_summary') }}

select
    coalesce(e.activity_type, 'unknown') as activity_type,
    count(distinct e.moodle_course_module_id) filter (
        where e.moodle_course_module_id is not null
    ) as activity_count,
    count(*) filter (
        where e.is_access_event = true
    ) as access_event_count,
    count(distinct u.email) filter (
        where e.is_access_event = true
    ) as unique_viewers,
    count(*) filter (
        where e.is_submission_final_event = true
    ) as submission_final_event_count,
    count(distinct u.email) filter (
        where e.is_submission_final_event = true
    ) as unique_submitters
from {{ ref('silver_moodle_learning_events') }} e
inner join {{ ref('gold_registered_user_learning_summary') }} u
    on lower(trim(e.email)) = u.email
group by coalesce(e.activity_type, 'unknown')

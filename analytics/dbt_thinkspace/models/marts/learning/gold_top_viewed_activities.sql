{{ config(materialized='view', alias='gold_top_viewed_activities') }}

with learning_events as (
    select *
    from {{ ref('silver_moodle_learning_events') }}
),

registered_users as (
    select *
    from {{ ref('gold_registered_user_learning_summary') }}
),

activity_summary as (
    select
        e.moodle_course_module_id,
        coalesce(e.activity_type, 'unknown') as activity_type,
        e.activity_name,
        count(*) filter (
            where e.is_access_event = true
        ) as access_event_count,
        count(distinct u.email) filter (
            where e.is_access_event = true
        ) as unique_viewers,
        max(e.event_time) filter (
            where e.is_access_event = true
        ) as last_access_at
    from learning_events e
    join registered_users u
        on lower(trim(e.email)) = u.email
    where e.moodle_course_module_id is not null
      and e.activity_name is not null
    group by
        e.moodle_course_module_id,
        coalesce(e.activity_type, 'unknown'),
        e.activity_name
)

select *
from activity_summary

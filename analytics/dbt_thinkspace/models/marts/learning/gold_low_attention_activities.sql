{{ config(materialized='view', alias='gold_low_attention_activities') }}

with activities as (
    select *
    from {{ ref('dim_moodle_course_activities') }}
),

learning_events as (
    select *
    from {{ ref('silver_moodle_learning_events') }}
),

registered_users as (
    select *
    from {{ ref('gold_registered_user_learning_summary') }}
),

activity_summary as (
    select
        d.moodle_course_module_id,
        coalesce(d.activity_type, 'unknown') as activity_type,
        d.activity_name,
        count(u.email) filter (
            where e.is_access_event = true
        ) as access_event_count,
        count(distinct u.email) filter (
            where e.is_access_event = true
        ) as unique_viewers,
        max(e.event_time) filter (
            where e.is_access_event = true
              and u.email is not null
        ) as last_access_at
    from activities d
    left join learning_events e
        on d.moodle_course_module_id = e.moodle_course_module_id
    left join registered_users u
        on lower(trim(e.email)) = u.email
    where d.is_learning_material = true
    group by
        d.moodle_course_module_id,
        coalesce(d.activity_type, 'unknown'),
        d.activity_name
)

select *
from activity_summary

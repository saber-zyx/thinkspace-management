{{ config(materialized='view', alias='dim_moodle_course_activities') }}

with bronze_events as (
    select *
    from {{ source('app_public', 'bronze_moodle_log_events') }}
    where moodle_course_module_id is not null
),

module_context_counts as (
    select
        moodle_course_module_id,
        coalesce(moodle_course_id, 12) as moodle_course_id,
        nullif(trim(context_type), '') as activity_type,
        nullif(trim(context_name), '') as activity_name,
        count(*) as context_event_count,
        row_number() over (
            partition by moodle_course_module_id
            order by count(*) desc, max(event_time) desc
        ) as context_rank
    from bronze_events
    group by
        moodle_course_module_id,
        coalesce(moodle_course_id, 12),
        nullif(trim(context_type), ''),
        nullif(trim(context_name), '')
),

module_stats as (
    select
        moodle_course_module_id,
        min(event_time) as first_seen_at,
        max(event_time) as last_seen_at,
        count(*) as total_event_rows,
        count(*) filter (
            where is_learning_event = true
        ) as learning_event_rows,
        count(distinct moodle_user_id) filter (
            where is_learning_event = true
              and moodle_user_id is not null
        ) as unique_learning_users,
        count(*) filter (
            where event_name_raw = 'A submission has been submitted.'
        ) as submission_final_event_rows,
        count(distinct moodle_user_id) filter (
            where event_name_raw = 'A submission has been submitted.'
              and moodle_user_id is not null
        ) as unique_submitters
    from bronze_events
    group by moodle_course_module_id
)

select
    c.moodle_course_module_id,
    c.moodle_course_id,
    c.activity_type,
    c.activity_name,
    lower(trim(coalesce(c.activity_type, 'unknown'))) as activity_type_key,
    lower(trim(coalesce(c.activity_name, 'unknown'))) as activity_name_key,
    c.activity_type = 'Assignment' as is_submission_activity,
    c.activity_type in ('Page', 'File', 'Forum', 'H5P')
        or c.activity_name ilike '%guideline%'
        or c.activity_name ilike '%handbook%'
        or c.activity_name ilike '%read me%' as is_learning_material,
    s.total_event_rows,
    s.learning_event_rows,
    s.unique_learning_users,
    s.submission_final_event_rows,
    s.unique_submitters,
    s.first_seen_at,
    s.last_seen_at
from module_context_counts c
inner join module_stats s
    on s.moodle_course_module_id = c.moodle_course_module_id
where c.context_rank = 1

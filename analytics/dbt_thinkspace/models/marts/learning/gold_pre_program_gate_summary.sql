{{ config(materialized='view', alias='gold_pre_program_gate_summary') }}

with registered as (
    select email
    from {{ ref('gold_registered_user_learning_summary') }}
),

user_flags as (
    select
        u.email,
        count(*) filter (
            where e.moodle_course_module_id = 707
              and e.is_access_event = true
        ) > 0 as viewed_survey_page,
        count(*) filter (
            where e.is_access_event = true
              and e.moodle_course_module_id is not null
              and e.moodle_course_module_id not in (707, 709)
        ) > 0 as accessed_any_content_after_survey
    from registered u
    left join {{ ref('silver_moodle_learning_events') }} e
        on lower(trim(e.email)) = u.email
    group by u.email
)

select
    1 as summary_id,
    count(*) as total_registered_users,
    count(*) filter (
        where viewed_survey_page = true
    ) as survey_page_viewers,
    count(*) filter (
        where accessed_any_content_after_survey = true
    ) as post_survey_content_users,
    count(*) filter (
        where viewed_survey_page = true
          and accessed_any_content_after_survey = false
    ) as viewed_survey_but_no_later_content
from user_flags

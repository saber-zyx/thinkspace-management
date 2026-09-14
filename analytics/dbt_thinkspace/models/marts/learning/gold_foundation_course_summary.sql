{{ config(materialized='view', alias='gold_foundation_course_summary') }}

with registered as (
    select email, team_name_key
    from {{ ref('gold_registered_user_learning_summary') }}
),

user_flags as (
    select
        u.email,
        u.team_name_key,
        count(*) filter (
            where e.moodle_course_module_id = 714
              and e.is_access_event = true
        ) > 0 as viewed_fmc3_lms_guideline,
        count(*) filter (
            where e.moodle_course_module_id = 716
              and e.is_access_event = true
        ) > 0 as accessed_foundation_submission,
        count(*) filter (
            where e.moodle_course_module_id = 716
              and e.is_submission_final_event = true
        ) > 0 as submitted_foundation_certificate
    from registered u
    left join {{ ref('silver_moodle_learning_events') }} e
        on lower(trim(e.email)) = u.email
    group by u.email, u.team_name_key
)

select
    1 as summary_id,
    count(*) as total_registered_users,
    count(*) filter (
        where viewed_fmc3_lms_guideline = true
    ) as fmc3_guideline_viewers,
    count(*) filter (
        where submitted_foundation_certificate = true
    ) as foundation_submission_users,
    count(distinct team_name_key) filter (
        where submitted_foundation_certificate = true
          and team_name_key is not null
    ) as foundation_active_teams,
    count(*) filter (
        where viewed_fmc3_lms_guideline = false
          and accessed_foundation_submission = true
    ) as skipped_fmc3_guideline_but_accessed_content,
    count(*) filter (
        where viewed_fmc3_lms_guideline = true
          and accessed_foundation_submission = false
    ) as viewed_fmc3_guideline_but_no_content_access
from user_flags

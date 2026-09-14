{{ config(materialized='view', alias='gold_key_activity_spotlights') }}

with target_activities as (
    select *
    from (
        values
            (1, 'pre_program_survey_page', 'Pre-Program Survey', 707, array[707]::integer[]),
            (2, 'lms_guideline', 'UEH LMS Registration Guideline (FMC3)', 714, array[714]::integer[]),
            (3, 'ueh_lms_entrepreneurship_enrollment', 'Đăng ký UEH LMS Entrepreneurship', null::integer, array[]::integer[]),
            (4, 'certificate_submission', 'Certificate Submission', 716, array[716]::integer[])
    ) as t(
        display_order,
        spotlight_key,
        spotlight_label,
        moodle_course_module_id,
        tracked_module_ids
    )
),

registered_total as (
    select count(*) as total_registered_users
    from {{ ref('gold_registered_user_learning_summary') }}
),

active_enrollments as (
    select distinct email
    from {{ ref('stg_ueh_lms_course_enrollments') }}
    where external_course_key = 'fmc3_entrepreneurship'
      and enrollment_status in ('enrolled', 'active')
),

registered_enrollments as (
    select count(*) as enrolled_registered_users
    from {{ ref('gold_registered_user_learning_summary') }} u
    inner join active_enrollments e
        on u.email = e.email
),

activity_dim_summary as (
    select
        t.display_order,
        coalesce(max(d.activity_type), 'unknown') as activity_type,
        case
            when t.spotlight_key in ('pre_program_survey_page', 'ueh_lms_entrepreneurship_enrollment')
                then t.spotlight_label
            else coalesce(max(d.activity_name), t.spotlight_label)
        end as activity_name,
        coalesce(sum(d.total_event_rows), 0) as total_moodle_log_rows,
        coalesce(sum(d.learning_event_rows), 0) as total_learning_log_rows,
        max(d.last_seen_at) as last_moodle_log_at
    from target_activities t
    left join {{ ref('dim_moodle_course_activities') }} d
        on d.moodle_course_module_id = any(t.tracked_module_ids)
    where t.spotlight_key <> 'ueh_lms_entrepreneurship_enrollment'
    group by
        t.display_order,
        t.spotlight_key,
        t.spotlight_label
),

activity_event_summary as (
    select
        t.display_order,
        count(distinct scope_e.email) as total_learning_log_users,
        count(scope_u.email) filter (
            where scope_e.is_access_event = true
        ) as access_event_count,
        count(distinct scope_u.email) filter (
            where scope_e.is_access_event = true
        ) as unique_viewers,
        count(scope_u.email) filter (
            where scope_e.progress_signal_type = 'submission_work'
        ) as submission_work_event_count,
        count(scope_u.email) filter (
            where scope_e.is_submission_final_event = true
        ) as submission_final_event_count,
        count(distinct scope_u.email) filter (
            where scope_e.is_submission_final_event = true
        ) as unique_submitters,
        max(scope_e.event_time) as last_interaction_at
    from target_activities t
    left join {{ ref('silver_moodle_learning_events') }} scope_e
        on scope_e.moodle_course_module_id = any(t.tracked_module_ids)
    left join {{ ref('gold_registered_user_learning_summary') }} scope_u
        on lower(trim(scope_e.email)) = scope_u.email
    where t.spotlight_key <> 'ueh_lms_entrepreneurship_enrollment'
    group by
        t.display_order
),

activity_events as (
    select
        t.display_order,
        t.spotlight_key,
        t.spotlight_label,
        t.moodle_course_module_id,
        d.activity_type,
        d.activity_name,
        d.total_moodle_log_rows,
        d.total_learning_log_rows,
        e.total_learning_log_users,
        e.access_event_count,
        e.unique_viewers,
        e.submission_work_event_count,
        e.submission_final_event_count,
        e.unique_submitters,
        e.last_interaction_at,
        d.last_moodle_log_at
    from target_activities t
    inner join activity_dim_summary d
        on t.display_order = d.display_order
    inner join activity_event_summary e
        on t.display_order = e.display_order
    where t.spotlight_key <> 'ueh_lms_entrepreneurship_enrollment'
),

enrollment_spotlight as (
    select
        t.display_order,
        t.spotlight_key,
        t.spotlight_label,
        t.moodle_course_module_id,
        'external_system' as activity_type,
        t.spotlight_label as activity_name,
        0::bigint as total_moodle_log_rows,
        0::bigint as total_learning_log_rows,
        0::bigint as total_learning_log_users,
        0::bigint as access_event_count,
        re.enrolled_registered_users::bigint as unique_viewers,
        0::bigint as submission_work_event_count,
        0::bigint as submission_final_event_count,
        re.enrolled_registered_users::bigint as unique_submitters,
        null::timestamp with time zone as last_interaction_at,
        null::timestamp with time zone as last_moodle_log_at
    from target_activities t
    cross join registered_enrollments re
    where t.spotlight_key = 'ueh_lms_entrepreneurship_enrollment'
),

combined as (
    select *
    from activity_events
    union all
    select *
    from enrollment_spotlight
)

select
    c.*,
    round(
        case
            when r.total_registered_users = 0 then 0
            else c.unique_viewers::numeric * 100 / r.total_registered_users
        end,
        1
    ) as viewer_rate
from combined c
cross join registered_total r

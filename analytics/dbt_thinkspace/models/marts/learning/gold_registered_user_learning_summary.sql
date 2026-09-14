{{ config(materialized='view', alias='gold_registered_user_learning_summary') }}

with registrations as (
    select *
    from {{ ref('stg_registrations') }}
),

identity_ranked as (
    select
        m.*,
        row_number() over (
            partition by lower(trim(m.email))
            order by
                case
                    when m.registration_id is not null then 0
                    else 1
                end,
                m.participant_id
        ) as identity_rank
    from {{ ref('int_moodle_user_identity_map') }} m
    where nullif(trim(m.email), '') is not null
),

identity_one as (
    select *
    from identity_ranked
    where identity_rank = 1
),

registered_event_summary as (
    select
        lower(trim(email)) as email_key,
        max(moodle_course_id) as moodle_course_id,
        max(moodle_user_id) as moodle_user_id,
        min(event_time) as first_access_at,
        max(event_time) as last_access_at,
        max(event_time) filter (
            where is_submission_final_event = true
        ) as latest_submission_at,
        count(*) as learning_event_count,
        count(*) filter (
            where is_access_event = true
        ) as access_event_count,
        count(*) filter (
            where is_submission_event = true
        ) as submission_event_count,
        count(*) filter (
            where progress_signal_type = 'submission_work'
        ) as submission_work_event_count,
        count(*) filter (
            where is_submission_final_event = true
        ) as submission_final_event_count,
        count(distinct event_date) as active_days_count,
        count(distinct moodle_course_module_id) filter (
            where is_access_event = true
              and moodle_course_module_id is not null
        ) as viewed_activity_count,
        count(distinct moodle_course_module_id) filter (
            where is_submission_final_event = true
              and moodle_course_module_id is not null
        ) as submitted_activity_count,
        string_agg(
            distinct activity_name,
            ', ' order by activity_name
        ) filter (
            where is_submission_final_event = true
              and activity_name is not null
        ) as submitted_activity_names
    from {{ ref('silver_moodle_learning_events') }}
    where nullif(trim(email), '') is not null
    group by lower(trim(email))
),

registered_users as (
    select
        current_date as snapshot_date,
        coalesce(i.course_id, s.moodle_course_id, 12) as moodle_course_id,
        r.registration_id,
        i.participant_id,
        s.moodle_user_id,
        r.full_name,
        lower(trim(r.email)) as email,
        r.student_id,
        r.role,
        nullif(trim(r.team_name), '') as team_name,
        lower(nullif(trim(r.team_name), '')) as team_name_key,
        coalesce(i.moodle_full_name, r.full_name) as moodle_full_name,
        i.moodle_group_name,
        coalesce(i.identity_status, 'missing_moodle_participant') as identity_status,
        i.participant_id is not null as has_moodle_participant,
        coalesce(s.learning_event_count, 0) > 0 as has_ever_accessed,
        s.first_access_at,
        s.last_access_at,
        case
            when s.last_access_at is null then null
            else current_date - cast(s.last_access_at as date)
        end as days_since_last_access,
        coalesce(s.learning_event_count, 0) as learning_event_count,
        coalesce(s.access_event_count, 0) as access_event_count,
        coalesce(s.viewed_activity_count, 0) as viewed_activity_count,
        coalesce(s.active_days_count, 0) as active_days_count,
        coalesce(s.submission_event_count, 0) as submission_event_count,
        coalesce(s.submission_work_event_count, 0) as submission_work_event_count,
        coalesce(s.submission_final_event_count, 0) as submission_final_event_count,
        coalesce(s.submitted_activity_count, 0) as submitted_activity_count,
        s.submitted_activity_names,
        s.latest_submission_at,
        coalesce(s.submission_final_event_count, 0) > 0 as has_submitted,
        case
            when coalesce(s.learning_event_count, 0) = 0 then 'not_started'
            when coalesce(s.submission_final_event_count, 0) > 0 then 'submitted'
            when cast(s.last_access_at as date) >= current_date - interval '7 days' then 'active'
            else 'inactive'
        end as current_learning_status
    from registrations r
    left join identity_one i
        on lower(trim(r.email)) = lower(trim(i.email))
    left join registered_event_summary s
        on lower(trim(r.email)) = s.email_key
    where nullif(trim(r.email), '') is not null
)

select *
from registered_users

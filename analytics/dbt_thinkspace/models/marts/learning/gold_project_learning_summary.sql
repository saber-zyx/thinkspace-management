{{ config(materialized='view', alias='gold_project_learning_summary') }}

with registered_users as (
    select *
    from {{ ref('gold_registered_user_learning_summary') }}
),

team_users as (
    select *
    from registered_users
    where team_name_key is not null
),

registered_events as (
    select
        e.*,
        coalesce(u.team_name_key, u.email) as project_key
    from {{ ref('silver_moodle_learning_events') }} e
    inner join registered_users u
        on lower(trim(e.email)) = u.email
),

project_event_summary as (
    select
        project_key,
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
    from registered_events
    group by project_key
),

team_projects as (
    select
        current_date as snapshot_date,
        coalesce(max(moodle_course_id), 12) as moodle_course_id,
        u.team_name_key as project_key,
        min(team_name) as project_name,
        'team' as project_type,
        count(*) as registered_users,
        count(*) filter (
            where has_moodle_participant = true
        ) as mapped_to_moodle_users,
        count(*) filter (
            where has_ever_accessed = true
        ) as accessed_users,
        count(*) filter (
            where has_ever_accessed = false
        ) as not_started_users,
        count(*) filter (
            where current_learning_status = 'active'
        ) as active_users,
        count(*) filter (
            where current_learning_status = 'inactive'
        ) as inactive_users,
        count(*) filter (
            where has_submitted = true
        ) as submitted_users,
        coalesce(sum(u.learning_event_count), 0) as learning_event_count,
        coalesce(sum(u.access_event_count), 0) as access_event_count,
        coalesce(sum(u.submission_event_count), 0) as submission_event_count,
        coalesce(sum(u.submission_work_event_count), 0) as submission_work_event_count,
        coalesce(sum(u.submission_final_event_count), 0) as submission_final_event_count,
        coalesce(sum(u.active_days_count), 0) as active_days_count,
        count(distinct u.email) filter (
            where has_ever_accessed = true
        ) as active_member_count,
        coalesce(max(e.viewed_activity_count), 0) as viewed_activity_count,
        coalesce(sum(u.viewed_activity_count), 0) as total_user_viewed_activity_count,
        coalesce(max(e.submitted_activity_count), 0) as submitted_activity_count,
        max(e.submitted_activity_names) as submitted_activity_names,
        round(avg(u.viewed_activity_count)::numeric, 2) as avg_viewed_activities_per_user,
        min(u.first_access_at) as first_access_at,
        max(u.last_access_at) as last_access_at,
        max(u.latest_submission_at) as latest_submission_at,
        case
            when max(u.last_access_at) is null then null
            else current_date - cast(max(u.last_access_at) as date)
        end as days_since_last_project_access,
        count(*) filter (
            where has_ever_accessed = true
        ) > 0 as has_any_access,
        count(*) filter (
            where has_submitted = true
        ) > 0 as has_any_submission,
        case
            when count(*) filter (where has_submitted = true) > 0 then 'submitted'
            when count(*) filter (where has_ever_accessed = true) = 0 then 'not_started'
            when count(*) filter (where current_learning_status = 'active') > 0 then 'active'
            else 'inactive'
        end as current_project_learning_status
    from team_users u
    left join project_event_summary e
        on u.team_name_key = e.project_key
    group by u.team_name_key
),

individual_projects as (
    select
        snapshot_date,
        coalesce(moodle_course_id, 12) as moodle_course_id,
        email as project_key,
        full_name as project_name,
        'individual' as project_type,
        1 as registered_users,
        case when has_moodle_participant then 1 else 0 end as mapped_to_moodle_users,
        case when has_ever_accessed then 1 else 0 end as accessed_users,
        case when has_ever_accessed then 0 else 1 end as not_started_users,
        case when current_learning_status = 'active' then 1 else 0 end as active_users,
        case when current_learning_status = 'inactive' then 1 else 0 end as inactive_users,
        case when has_submitted then 1 else 0 end as submitted_users,
        learning_event_count,
        access_event_count,
        submission_event_count,
        submission_work_event_count,
        submission_final_event_count,
        active_days_count,
        case when has_ever_accessed then 1 else 0 end as active_member_count,
        viewed_activity_count,
        viewed_activity_count as total_user_viewed_activity_count,
        submitted_activity_count,
        submitted_activity_names,
        viewed_activity_count::numeric as avg_viewed_activities_per_user,
        first_access_at,
        last_access_at,
        latest_submission_at,
        days_since_last_access as days_since_last_project_access,
        has_ever_accessed as has_any_access,
        has_submitted as has_any_submission,
        current_learning_status as current_project_learning_status
    from registered_users
    where team_name_key is null
),

project_summary as (
    select *
    from team_projects
    union all
    select *
    from individual_projects
)

select *
from project_summary

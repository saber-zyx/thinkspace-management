{{ config(materialized='view', alias='gold_daily_learning_interactions') }}

select
    e.event_date,
    count(*) as total_interactions,
    count(*) filter (
        where e.is_access_event = true
    ) as access_interactions,
    count(*) filter (
        where e.progress_signal_type = 'submission_work'
    ) as submission_work_interactions,
    count(*) filter (
        where e.is_submission_final_event = true
    ) as submitted_interactions,
    count(distinct u.email) as active_users,
    count(distinct u.team_name_key) filter (
        where u.team_name_key is not null
    ) as active_team_projects,
    count(distinct coalesce(u.team_name_key, u.email)) as active_projects
from {{ ref('silver_moodle_learning_events') }} e
inner join {{ ref('gold_registered_user_learning_summary') }} u
    on lower(trim(e.email)) = u.email
group by e.event_date

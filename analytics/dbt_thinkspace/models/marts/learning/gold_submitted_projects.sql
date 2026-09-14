{{ config(materialized='view', alias='gold_submitted_projects') }}

with projects as (
    select *
    from {{ ref('gold_project_learning_summary') }}
    where has_any_submission = true
)

select
    project_key,
    project_name,
    project_type,
    project_name as team_name,
    registered_users,
    submitted_users,
    submitted_activity_count,
    submitted_activity_names,
    latest_submission_at
from projects

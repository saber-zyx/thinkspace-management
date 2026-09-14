{{ config(materialized='view', alias='gold_milestone_traction_summary') }}

with milestone_map as (
    select *
    from (
        values
            (1, 'Milestone 1', 'Start Here - Identify Your Market', 650, 651),
            (2, 'Milestone 2', 'Understand Your User', 653, 654),
            (3, 'Milestone 3', 'Coming up with the Problem Statement', 656, 657),
            (4, 'Milestone 4', 'Design Your Offering', 659, 660),
            (5, 'Milestone 5', 'Shape the Value', 662, 663),
            (6, 'Final Submission', 'Final Submission', 665, 666)
    ) as m(
        display_order,
        milestone_code,
        milestone_name,
        guideline_module_id,
        submission_module_id
    )
),

registered_users as (
    select *
    from {{ ref('gold_registered_user_learning_summary') }}
),

registered_events as (
    select
        e.*,
        u.full_name,
        u.email as registered_email,
        u.team_name as registered_team_name,
        coalesce(u.team_name_key, u.email) as project_key,
        coalesce(nullif(u.team_name, ''), u.full_name) as project_name
    from {{ ref('silver_moodle_learning_events') }} e
    inner join registered_users u
        on lower(trim(e.email)) = u.email
),

submitted_projects as (
    select
        m.display_order,
        e.project_key,
        max(e.project_name) as project_name,
        max(e.registered_team_name) as team_name,
        count(*) as submitted_count,
        count(distinct e.registered_email) as submitted_user_count,
        max(e.event_time) as latest_submitted_at
    from milestone_map m
    inner join registered_events e
        on e.moodle_course_module_id = m.submission_module_id
    where e.is_submission_final_event = true
    group by m.display_order, e.project_key
),

milestone_summary as (
    select
        m.display_order,
        m.milestone_code,
        m.milestone_name,
        m.guideline_module_id,
        m.submission_module_id,
        count(*) filter (
            where e.moodle_course_module_id = m.guideline_module_id
              and e.is_access_event = true
        ) as guideline_view_count,
        count(distinct e.email) filter (
            where e.moodle_course_module_id = m.guideline_module_id
              and e.is_access_event = true
        ) as guideline_user_count,
        count(*) filter (
            where e.moodle_course_module_id = m.submission_module_id
              and e.is_submission_final_event = true
        ) as submission_done_count,
        count(distinct e.project_key) filter (
            where e.moodle_course_module_id = m.submission_module_id
              and e.is_submission_final_event = true
        ) as submission_done_project_count,
        coalesce((
            select jsonb_agg(
                jsonb_build_object(
                    'project_key', sp.project_key,
                    'project_name', sp.project_name,
                    'team_name', sp.team_name,
                    'submitted_count', sp.submitted_count,
                    'submitted_user_count', sp.submitted_user_count,
                    'latest_submitted_at', sp.latest_submitted_at
                )
                order by sp.latest_submitted_at desc, sp.project_name
            )
            from submitted_projects sp
            where sp.display_order = m.display_order
        ), '[]'::jsonb) as submitted_projects
    from milestone_map m
    left join registered_events e
        on e.moodle_course_module_id in (
            m.guideline_module_id,
            m.submission_module_id
        )
    group by
        m.display_order,
        m.milestone_code,
        m.milestone_name,
        m.guideline_module_id,
        m.submission_module_id
)

select *
from milestone_summary
order by display_order

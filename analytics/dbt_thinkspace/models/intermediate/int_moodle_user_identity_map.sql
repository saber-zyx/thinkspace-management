{{ config(materialized='view', alias='int_moodle_user_identity_map') }}

with participants as (
    select *
    from {{ ref('stg_moodle_participants') }}
),

registrations as (
    select *
    from {{ ref('stg_registrations') }}
)

select
    p.participant_id,
    p.participant_file_id,
    p.course_id,
    p.moodle_full_name,
    p.moodle_full_name_key,
    p.email,
    p.moodle_group_name,
    r.registration_id,
    r.full_name as registration_full_name,
    r.student_id,
    r.role,
    r.team_name as registration_team_name,
    case
        when r.registration_id is null then 'unmatched_registration'
        when nullif(trim(coalesce(p.moodle_group_name, '')), '') is null then 'matched_without_moodle_group'
        when nullif(trim(coalesce(r.team_name, '')), '') is null then 'matched_without_registration_team'
        when lower(trim(p.moodle_group_name)) = lower(trim(r.team_name)) then 'matched_same_team'
        else 'matched_team_conflict'
    end as identity_status,
    p.loaded_at
from participants p
left join registrations r
    on p.email = r.email

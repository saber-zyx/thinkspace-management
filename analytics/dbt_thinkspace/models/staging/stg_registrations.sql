{{ config(materialized='view', alias='stg_registrations') }}

select
    id as registration_id,
    job_id,
    nullif(trim(full_name), '') as full_name,
    lower(trim(email)) as email,
    nullif(trim(student_id), '') as student_id,
    nullif(trim(phone), '') as phone,
    nullif(trim(role), '') as role,
    nullif(trim(team_name), '') as team_name,
    lower(nullif(trim(team_name), '')) as team_name_key,
    nullif(trim(school), '') as school,
    nullif(trim(project_domain), '') as project_domain,
    nullif(trim(source), '') as source,
    created_at
from {{ source('app_public', 'registrations') }}
where nullif(trim(email), '') is not null

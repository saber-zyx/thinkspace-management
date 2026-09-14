{{ config(materialized='view', alias='gold_ueh_lms_entrepreneurship_enrollment_detail') }}

with registrations as (
    select *
    from {{ ref('stg_registrations') }}
),

enrollment_ranked as (
    select
        e.*,
        row_number() over (
            partition by lower(trim(e.email))
            order by e.loaded_at desc, e.id desc
        ) as enrollment_rank
    from {{ ref('stg_ueh_lms_course_enrollments') }} e
    where e.external_course_key = 'fmc3_entrepreneurship'
      and e.enrollment_status in ('enrolled', 'active')
      and nullif(trim(e.email), '') is not null
),

latest_enrollment as (
    select *
    from enrollment_ranked
    where enrollment_rank = 1
)

select
    r.registration_id,
    r.full_name,
    lower(trim(r.email)) as email,
    r.role,
    nullif(trim(r.team_name), '') as team_name,
    e.external_course_name,
    e.enrollment_status,
    e.enrolled_at,
    e.loaded_at
from registrations r
join latest_enrollment e
    on lower(trim(r.email)) = lower(trim(e.email))
where nullif(trim(r.email), '') is not null

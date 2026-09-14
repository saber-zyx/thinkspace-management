{{ config(materialized='view', alias='gold_ueh_lms_entrepreneurship_enrollment_summary') }}

with registered as (
    select
        lower(trim(email)) as email,
        count(*) as registration_rows
    from {{ ref('stg_registrations') }}
    where nullif(trim(email), '') is not null
    group by lower(trim(email))
),

enrolled as (
    select distinct lower(trim(email)) as email
    from {{ ref('stg_ueh_lms_course_enrollments') }}
    where external_course_key = 'fmc3_entrepreneurship'
      and enrollment_status in ('enrolled', 'active')
      and nullif(trim(email), '') is not null
)

select
    1 as summary_id,
    coalesce((select sum(registration_rows) from registered), 0) as total_registered_users,
    count(r.email) filter (
        where e.email is not null
    ) as enrolled_registered_users,
    coalesce((select count(*) from enrolled), 0) as source_enrolled_emails,
    round(
        case
            when coalesce((select sum(registration_rows) from registered), 0) = 0 then 0
            else count(r.email) filter (where e.email is not null)::numeric * 100
                / coalesce((select sum(registration_rows) from registered), 0)
        end,
        1
    ) as enrollment_rate
from registered r
left join enrolled e
    on r.email = e.email

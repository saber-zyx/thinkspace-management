{{ config(materialized='view', alias='stg_ueh_lms_course_enrollments') }}

select
    id,
    nullif(trim(source_system), '') as source_system,
    nullif(trim(external_course_key), '') as external_course_key,
    nullif(trim(external_course_name), '') as external_course_name,
    nullif(trim(email_raw), '') as email_raw,
    lower(trim(email)) as email,
    nullif(trim(full_name_raw), '') as full_name_raw,
    nullif(trim(enrollment_status), '') as enrollment_status,
    enrolled_at,
    loaded_at
from {{ source('app_public', 'raw_ueh_lms_course_enrollments') }}
where nullif(trim(email), '') is not null

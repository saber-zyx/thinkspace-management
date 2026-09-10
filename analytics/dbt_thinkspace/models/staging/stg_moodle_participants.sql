{{ config(materialized='view', alias='stg_moodle_participants') }}

select
    id as participant_id,
    raw_file_id as participant_file_id,
    course_id,
    source_row_number,
    nullif(trim(first_name_raw), '') as first_name_raw,
    nullif(trim(last_name_raw), '') as last_name_raw,
    nullif(trim(email_raw), '') as email_raw,
    nullif(trim(groups_raw), '') as groups_raw,
    nullif(trim(moodle_full_name), '') as moodle_full_name,
    lower(trim(moodle_full_name_key)) as moodle_full_name_key,
    lower(trim(email)) as email,
    nullif(trim(moodle_group_name), '') as moodle_group_name,
    lower(nullif(trim(moodle_group_name), '')) as moodle_group_name_key,
    participant_hash,
    loaded_at
from {{ source('app_public', 'raw_moodle_participants') }}
where nullif(trim(email), '') is not null

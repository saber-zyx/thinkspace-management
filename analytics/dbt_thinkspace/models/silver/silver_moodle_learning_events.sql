{{ config(materialized='view', alias='silver_moodle_learning_events') }}

with bronze_events as (
    select *
    from {{ source('app_public', 'bronze_moodle_log_events') }}
),

identity_map as (
    select *
    from {{ ref('int_moodle_user_identity_map') }}
),

learning_events as (
    select
        b.id as bronze_event_id,
        b.raw_file_id,
        b.source_row_number,
        b.event_time,
        cast(b.event_time as date) as event_date,
        b.moodle_user_id,
        m.participant_id,
        m.registration_id,
        coalesce(
            nullif(trim(m.registration_full_name), ''),
            nullif(trim(m.moodle_full_name), ''),
            nullif(trim(b.user_full_name_raw), '')
        ) as full_name,
        m.email,
        m.student_id,
        m.role,
        coalesce(
            nullif(trim(m.registration_team_name), ''),
            nullif(trim(m.moodle_group_name), '')
        ) as team_name,
        lower(
            coalesce(
                nullif(trim(m.registration_team_name), ''),
                nullif(trim(m.moodle_group_name), '')
            )
        ) as team_name_key,
        coalesce(b.moodle_course_id, m.course_id) as moodle_course_id,
        b.moodle_course_module_id,
        b.component_raw as component,
        nullif(trim(b.context_type), '') as activity_type,
        nullif(trim(b.context_name), '') as activity_name,
        b.event_name_raw as event_name,
        b.event_category,
        b.is_learning_event,
        b.event_name_raw in (
            'Course viewed',
            'Course module viewed',
            'Section viewed',
            'H5P content viewed',
            'xAPI statement received',
            'The status of the submission has been viewed.',
            'Submission form viewed.',
            'SCO launched',
            'SCORM status submitted',
            'SCORM raw score submitted',
            'Quiz attempt viewed',
            'Quiz attempt reviewed',
            'Quiz attempt started',
            'Quiz attempt summary viewed'
        ) as is_view_event,
        b.event_name_raw in (
            'Course viewed',
            'Course module viewed',
            'Section viewed',
            'H5P content viewed',
            'xAPI statement received',
            'The status of the submission has been viewed.',
            'Submission form viewed.',
            'SCO launched',
            'SCORM status submitted',
            'SCORM raw score submitted',
            'Quiz attempt viewed',
            'Quiz attempt reviewed',
            'Quiz attempt started',
            'Quiz attempt summary viewed'
        ) as is_access_event,
        b.event_name_raw in (
            'Submission created.',
            'Submission updated.',
            'A file has been uploaded.',
            'An online text has been uploaded.',
            'A submission has been submitted.',
            'The status of the submission has been updated.',
            'Quiz attempt submitted',
            'Course module completion updated'
        ) as is_submission_event,
        b.event_name_raw in (
            'A submission has been submitted.',
            'Quiz attempt submitted',
            'Course module completion updated'
        ) as is_submission_final_event,
        b.event_name_raw in (
            'A submission has been submitted.',
            'Quiz attempt submitted',
            'Course module completion updated'
        ) as is_completion_event,
        case
            when b.event_name_raw in (
                'A submission has been submitted.',
                'Quiz attempt submitted',
                'Course module completion updated'
            ) then 'submission_final'
            when b.event_name_raw in (
                'Submission created.',
                'Submission updated.',
                'A file has been uploaded.',
                'An online text has been uploaded.',
                'The status of the submission has been updated.'
            ) then 'submission_work'
            when b.event_name_raw in (
                'Course viewed',
                'Course module viewed',
                'Section viewed',
                'H5P content viewed',
                'xAPI statement received',
                'The status of the submission has been viewed.',
                'Submission form viewed.',
                'SCO launched',
                'SCORM status submitted',
                'SCORM raw score submitted',
                'Quiz attempt viewed',
                'Quiz attempt reviewed',
                'Quiz attempt started',
                'Quiz attempt summary viewed'
            ) then 'access'
            else 'other_learning'
        end as progress_signal_type,
        b.origin_raw as origin,
        m.identity_status,
        b.loaded_at
    from bronze_events b
    left join identity_map m
        on lower(trim(b.user_full_name_raw)) = m.moodle_full_name_key
    where b.is_learning_event = true
      and b.moodle_user_id is not null
)

select *
from learning_events

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    total_rows = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    status = Column(String(50), default="completed") # completed, failed
    log_summary = Column(Text, nullable=True)


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, index=True) # Liên kết tới đợt sync nào
    full_name = Column(String(255))
    email = Column(String(255), index=True)
    student_id = Column(String(50))
    phone = Column(String(50))
    role = Column(String(50)) # Leader, Member, Individual
    team_name = Column(Text, nullable=True) # Null nếu là cá nhân
    school = Column(String(100), default="UEH")
    project_domain = Column(Text, nullable=True)
    source = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RawMoodleLogFile(Base):
    __tablename__ = "raw_moodle_log_files"

    id = Column(Integer, primary_key=True, index=True)
    source_file_name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False, default="manual_upload")
    course_id = Column(Integer, nullable=True)
    row_count = Column(Integer, default=0)
    inserted_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    time_min = Column(DateTime(timezone=True), nullable=True)
    time_max = Column(DateTime(timezone=True), nullable=True)
    load_status = Column(String(50), default="completed")
    error_message = Column(Text, nullable=True)
    loaded_at = Column(DateTime(timezone=True), server_default=func.now())


class RawMoodleParticipantFile(Base):
    __tablename__ = "raw_moodle_participant_files"

    id = Column(Integer, primary_key=True, index=True)
    source_file_name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False, default="manual_upload")
    course_id = Column(Integer, nullable=True, index=True)
    row_count = Column(Integer, default=0)
    inserted_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    load_status = Column(String(50), default="completed")
    error_message = Column(Text, nullable=True)
    loaded_at = Column(DateTime(timezone=True), server_default=func.now())


class RawMoodleParticipant(Base):
    __tablename__ = "raw_moodle_participants"
    __table_args__ = (
        UniqueConstraint("participant_hash", name="uq_raw_moodle_participants_participant_hash"),
    )

    id = Column(Integer, primary_key=True, index=True)
    raw_file_id = Column(Integer, ForeignKey("raw_moodle_participant_files.id"), nullable=False, index=True)
    source_row_number = Column(Integer, nullable=True)
    course_id = Column(Integer, nullable=True, index=True)
    first_name_raw = Column(String(255), nullable=True)
    last_name_raw = Column(String(255), nullable=True)
    email_raw = Column(String(255), nullable=True)
    groups_raw = Column(Text, nullable=True)
    moodle_full_name = Column(String(255), nullable=True, index=True)
    moodle_full_name_key = Column(String(255), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    moodle_group_name = Column(Text, nullable=True)
    participant_hash = Column(String(64), nullable=False, index=True)
    loaded_at = Column(DateTime(timezone=True), server_default=func.now())


class MoodleParticipantEmailExclusion(Base):
    __tablename__ = "moodle_participant_email_exclusions"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    reason = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MoodleLogUserExclusion(Base):
    __tablename__ = "moodle_log_user_exclusions"

    id = Column(Integer, primary_key=True, index=True)
    moodle_user_id = Column(Integer, nullable=False, unique=True, index=True)
    reason = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RawUehLmsCourseEnrollment(Base):
    __tablename__ = "raw_ueh_lms_course_enrollments"
    __table_args__ = (
        UniqueConstraint(
            "external_course_key",
            "email",
            name="uq_raw_ueh_lms_course_enrollments_course_email",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    source_system = Column(String(100), default="ueh_lms", nullable=False)
    external_course_key = Column(String(100), default="fmc3_entrepreneurship", nullable=False, index=True)
    external_course_name = Column(String(255), nullable=True)
    email_raw = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    full_name_raw = Column(String(255), nullable=True)
    enrollment_status = Column(String(50), default="enrolled", nullable=False, index=True)
    enrolled_at = Column(DateTime(timezone=True), nullable=True)
    loaded_at = Column(DateTime(timezone=True), server_default=func.now())


class MoodleLogIngestionState(Base):
    __tablename__ = "moodle_log_ingestion_state"
    __table_args__ = (
        UniqueConstraint("source_name", "course_id", name="uq_moodle_log_ingestion_state_source_course"),
    )

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(100), nullable=False, index=True)
    course_id = Column(Integer, nullable=True, index=True)
    last_moodle_log_id = Column(Integer, nullable=True)
    last_event_time = Column(DateTime(timezone=True), nullable=True)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="not_started", nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MoodleLogIngestionRun(Base):
    __tablename__ = "moodle_log_ingestion_runs"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(100), nullable=False, index=True)
    course_id = Column(Integer, nullable=True, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="running", nullable=False, index=True)
    rows_fetched = Column(Integer, default=0)
    inserted_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    previous_watermark_id = Column(Integer, nullable=True)
    new_watermark_id = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)


class BronzeMoodleLogEvent(Base):
    __tablename__ = "bronze_moodle_log_events"
    __table_args__ = (
        UniqueConstraint("event_hash", name="uq_bronze_moodle_log_events_event_hash"),
    )

    id = Column(Integer, primary_key=True, index=True)
    raw_file_id = Column(Integer, ForeignKey("raw_moodle_log_files.id"), nullable=False, index=True)
    source_row_number = Column(Integer, nullable=True)
    event_time = Column(DateTime(timezone=True), nullable=False, index=True)
    user_full_name_raw = Column(String(255), nullable=True, index=True)
    affected_user_raw = Column(String(255), nullable=True)
    event_context_raw = Column(Text, nullable=True)
    component_raw = Column(String(100), nullable=True, index=True)
    event_name_raw = Column(String(255), nullable=True, index=True)
    description_raw = Column(Text, nullable=True)
    origin_raw = Column(String(50), nullable=True)
    ip_address_raw = Column(String(100), nullable=True)
    moodle_user_id = Column(Integer, nullable=True, index=True)
    moodle_affected_user_id = Column(Integer, nullable=True, index=True)
    moodle_course_id = Column(Integer, nullable=True, index=True)
    moodle_course_module_id = Column(Integer, nullable=True, index=True)
    moodle_group_id = Column(Integer, nullable=True, index=True)
    context_type = Column(String(100), nullable=True)
    context_name = Column(Text, nullable=True)
    is_learning_event = Column(Boolean, default=False, nullable=False)
    event_category = Column(String(50), default="unknown", nullable=False, index=True)
    event_hash = Column(String(64), nullable=False, index=True)
    loaded_at = Column(DateTime(timezone=True), server_default=func.now())

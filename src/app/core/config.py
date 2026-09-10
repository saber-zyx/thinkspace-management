from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    app_debug: bool = True

    # Google Sheets Integration
    google_service_account_file: str = ""
    google_sheet_default_worksheet: str = ""

    # Moodle Integration
    moodle_base_url: str = ""
    moodle_token: str = ""
    moodle_default_role_id: str = ""
    moodle_log_source_database_url: str = ""
    moodle_log_source_name: str = "moodle_standard_log"
    moodle_log_source_table: str = "mdl_logstore_standard_log"
    moodle_log_source_user_table: str = "mdl_user"
    moodle_log_source_course_table: str = "mdl_course"
    moodle_log_source_poll_course_ids: str = ""
    moodle_log_source_batch_size: int = 1000

    # PostgreSQL Configuration
    postgres_user: str = ""
    postgres_password: str = ""
    postgres_db: str = ""
    postgres_host: str = ""
    postgres_port: str = "5432"
    database_url: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

import os

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

# Lấy thông tin database từ biến môi trường.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://thinkspace:password123@localhost:5432/thinkspacedb",
)

# Nếu cấu hình không phải PostgreSQL thì dùng SQLite nhẹ cho môi trường thử nghiệm.
if not DATABASE_URL.startswith("postgresql"):
    DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL)

if DATABASE_URL.startswith("postgresql"):

    @event.listens_for(engine, "connect")
    def set_postgresql_search_path(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("SET search_path TO public")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

REGISTRATION_LONG_TEXT_COLUMNS = (
    "team_name",
    "project_domain",
    "source",
)


def ensure_registration_text_columns() -> None:
    """
    Giữ database PostgreSQL cũ tương thích với model SQLAlchemy hiện tại.
    create_all() không tự sửa kiểu cột đã tồn tại, nên cần nới các cột có thể
    chứa câu trả lời dài trước khi người dùng upload file mới.
    """
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        table_exists = connection.execute(
            text("SELECT to_regclass('public.registrations')")
        ).scalar()
        if not table_exists:
            return

        for column_name in REGISTRATION_LONG_TEXT_COLUMNS:
            data_type = connection.execute(
                text(
                    """
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'registrations'
                      AND column_name = :column_name
                    """
                ),
                {"column_name": column_name},
            ).scalar()
            if data_type == "text":
                continue

            connection.execute(
                text(
                    f"ALTER TABLE registrations "
                    f"ALTER COLUMN {column_name} TYPE TEXT "
                    f"USING {column_name}::TEXT"
                )
            )


def ensure_moodle_log_bronze_columns() -> None:
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        table_exists = connection.execute(
            text("SELECT to_regclass('public.bronze_moodle_log_events')")
        ).scalar()
        if not table_exists:
            return

        column_exists = connection.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'bronze_moodle_log_events'
                  AND column_name = 'source_row_number'
                """
            )
        ).scalar()

        if not column_exists:
            connection.execute(
                text(
                    "ALTER TABLE bronze_moodle_log_events "
                    "ADD COLUMN source_row_number INTEGER"
                )
            )


# Các view analytics được quản lý bởi dbt trong schema analytics.
# FastAPI chỉ giữ phần kết nối DB và các migration nhẹ cho bảng nguồn.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

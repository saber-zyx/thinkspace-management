import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from src.app.api.dashboard import router as dashboard_router
from src.app.api.health import router as health_router
from src.app.api.moodle_logs import router as moodle_logs_router
from src.app.api.moodle_participants import router as moodle_participants_router
from src.app.core.config import settings
from src.app.core.database import (
    engine,
    ensure_moodle_log_bronze_columns,
    ensure_registration_text_columns,
)
from src.app.models.schema import Base
from src.app.services.msforms_service import process_msforms_excel

app = FastAPI(
    title="ThinkSpace Management API",
    description="API tự động hóa tiếp nhận và ghi danh khóa học trên Moodle.",
    version="1.0.0",
    debug=settings.app_debug,
)

# Đăng ký các router.
app.include_router(health_router)
app.include_router(dashboard_router)
app.include_router(moodle_logs_router)
app.include_router(moodle_participants_router)

# Tạo bảng nguồn khi startup. Các view analytics do dbt quản lý.
Base.metadata.create_all(bind=engine)
ensure_registration_text_columns()
ensure_moodle_log_bronze_columns()


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API đang hoạt động!"}


@app.post("/api/v1/sync/msforms")
async def sync_msforms(course_id: int = Form(...), file: UploadFile = File(...)):
    """
    Endpoint nhận file Excel từ frontend, gửi sang msforms_service xử lý.
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Vui lòng tải lên file Excel (.xlsx)",
        )

    try:
        content = await file.read()
        report = process_msforms_excel(content, course_id)
        return {"status": "success", "data": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Đảm bảo thư mục static tồn tại trước khi mount.
static_path = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_path, exist_ok=True)

# Mount thư mục static cho giao diện Web.
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

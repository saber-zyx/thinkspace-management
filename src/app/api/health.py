from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["System"])
async def health_check():
    """
    Endpoint kiểm tra trạng thái hoạt động của hệ thống.
    """
    return {
        "status": "ok",
        "message": "ThinkSpace Management API is running"
    }

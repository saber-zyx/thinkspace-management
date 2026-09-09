import logging
from typing import Optional
from src.app.integrations.moodle import moodle_client

logger = logging.getLogger(__name__)

def get_or_create_group(course_id: int, team_name: str) -> Optional[int]:
    """
    Tìm kiếm hoặc tạo mới một Group trên Moodle.
    Trả về group_id.
    """
    try:
        groups = moodle_client.get_course_groups(course_id)
        for g in groups:
            if g.get("name") == team_name:
                logger.info(f"Group '{team_name}' đã tồn tại (ID: {g.get('id')})")
                return g.get("id")
                
        logger.info(f"Group '{team_name}' chưa tồn tại. Đang tạo mới...")
        new_group = moodle_client.create_group(course_id, team_name)
        group_id = new_group.get("id")
        logger.info(f"Đã tạo Group thành công (ID: {group_id})")
        return group_id
    except Exception as e:
        logger.error(f"Lỗi khi xử lý Group {team_name}: {str(e)}")
        return None

from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class Member(BaseModel):
    """
    Model Member chuẩn (Canonical Model) đại diện cho một thành viên/người tham gia.
    Tất cả các nguồn dữ liệu đầu vào (Google Sheet, Form, v.v.) đều sẽ được
    map (ánh xạ) về cấu trúc này trước khi được xử lý tiếp.
    """
    first_name: str = Field(..., description="Tên (Ví dụ: Trường, Anh, Tiến)")
    last_name: str = Field(..., description="Họ và tên đệm (Ví dụ: Võ Thiên, Hoài Bảo)")
    email: EmailStr = Field(..., description="Địa chỉ email hợp lệ, dùng làm định danh chính")
    
    student_id: Optional[str] = Field(None, description="Mã số sinh viên (MSSV)")
    phone: Optional[str] = Field(None, description="Số điện thoại liên hệ")
    school: Optional[str] = Field(None, description="Tên trường (Ví dụ: UEH, UEL, HCMU)")
    role: Optional[str] = Field(None, description="Vai trò trong nhóm (Ví dụ: Leader, Member)")
    class_name: Optional[str] = Field(None, description="Khóa - Lớp (Ví dụ: K112-TI123)")
    major: Optional[str] = Field(None, description="Ngành học (Ví dụ: CNDMST)")
    
    @property
    def full_name(self) -> str:
        """Trả về họ và tên đầy đủ."""
        return f"{self.last_name} {self.first_name}".strip()

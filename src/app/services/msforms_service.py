import openpyxl
import io
import logging
import base64
import re
import unicodedata
from datetime import datetime
from openpyxl.utils.datetime import from_excel
from src.app.models.member import Member
from src.app.services.member_service import process_sheet_url
from src.app.services.moodle_service import sync_member_to_moodle
from src.app.services.group_service import get_or_create_group
from src.app.core.database import SessionLocal
from src.app.models.schema import Registration
from src.app.utils.text_utils import normalized_team_name

logger = logging.getLogger(__name__)


def normalize_header(value: object) -> str:
    text = str(value or "").replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text).lower()
    return " ".join(text.split())


def build_header_index(ws) -> dict[str, int]:
    return {
        normalize_header(cell.value): idx
        for idx, cell in enumerate(ws[1])
        if cell.value is not None
    }


def find_header_index(headers: dict[str, int], *needles: str, fallback: int | None = None) -> int | None:
    normalized_needles = [normalize_header(needle) for needle in needles]
    for header, idx in headers.items():
        if all(needle in header for needle in normalized_needles):
            return idx
    return fallback


def looks_like_sheet_url(value: str) -> bool:
    return "docs.google.com/spreadsheets" in value.lower()


def looks_like_team_registration(value: str) -> bool:
    normalized = normalize_header(value)
    return "nhom" in normalized or "group" in normalized


def normalize_team_name(team_name: str) -> str:
    return normalized_team_name(team_name) or ""


def split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    first_name = parts[-1]
    last_name = " ".join(parts[:-1])
    return first_name, last_name

def process_msforms_excel(file_content: bytes, course_id: int) -> dict:
    """
    Nhận nội dung file Excel từ MS Forms, phân loại và đồng bộ lên Moodle.
    Hỗ trợ xử lý Batch (Cá nhân & Đội nhóm).
    """
    wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
    ws = wb.active
    header_indices = build_header_index(ws)
    col_completion_time = find_header_index(header_indices, "completion time", fallback=2)
    col_start_time = find_header_index(header_indices, "start time", fallback=1)
    col_modified_time = find_header_index(header_indices, "last modified time", fallback=5)
    col_full_name = find_header_index(header_indices, "ho va ten cua ban", fallback=6)
    col_email = find_header_index(header_indices, "email2", fallback=7)
    col_is_ueh = find_header_index(header_indices, "sinh vien ueh", fallback=8)
    col_student_id = find_header_index(header_indices, "ma so sinh vien", fallback=9)
    col_phone = find_header_index(header_indices, "so dien thoai", fallback=12)
    col_participation_type = find_header_index(header_indices, "tham gia", "hinh thuc", fallback=15)
    col_sheet_link = find_header_index(header_indices, "danh sach thanh vien", fallback=18)
    col_team_name = find_header_index(header_indices, "ten y tuong", fallback=19)
    col_project_domain = find_header_index(header_indices, "linh vuc hoat dong", fallback=22)
    col_source = find_header_index(header_indices, "ban biet den", fallback=27)
    
    db = SessionLocal()
    
    report = {
        "total_rows": 0,
        "teams_processed": 0,
        "individuals_processed": 0,
        "success_count": 0,
        "fail_count": 0,
        "logs": [],
        "new_users": []
    }
    
    try:
        # Bắt đầu đọc từ dòng 2 (bỏ qua header)
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            # Đảm bảo dòng không trống
            if not any(row):
                continue
            
            report["total_rows"] += 1
            
            # Chỉ mục cột (dựa vào file mẫu, 0-indexed)
            # Col 6 (Last modified time) -> idx 5
            # Col 7 (Họ và tên) -> idx 6
            # Col 8 (Email2) -> idx 7
            # Col 9 (Bạn có phải sinh viên UEH không) -> idx 8
            # Col 10 (MSSV) -> idx 9
            # Col 13 (SDT) -> idx 12
            # Col 19 (Link Sheet) -> idx 18
            # Col 20 (Tên ý tưởng) -> idx 19
            
            def safe_get(idx: int | None) -> str:
                return str(row[idx]).strip() if idx is not None and len(row) > idx and row[idx] is not None else ""

            def raw_get(idx: int | None):
                return row[idx] if idx is not None and len(row) > idx else None

            raw_time = raw_get(col_completion_time) or raw_get(col_start_time) or raw_get(col_modified_time)
            created_dt = None
            if isinstance(raw_time, datetime):
                created_dt = raw_time
            elif isinstance(raw_time, (int, float)):
                try:
                    created_dt = from_excel(raw_time)
                except Exception:
                    pass
            elif isinstance(raw_time, str) and raw_time.strip():
                date_str = raw_time.strip()
                for fmt in ("%m/%d/%y %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d/%m/%y %H:%M:%S"):
                    try:
                        created_dt = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        pass
                if not created_dt:
                    created_dt = datetime.now()
            else:
                created_dt = datetime.now()
                
            full_name = safe_get(col_full_name)
            email = safe_get(col_email)
            is_ueh_str = safe_get(col_is_ueh)
            student_id = safe_get(col_student_id)
            phone = safe_get(col_phone)
            participation_type = safe_get(col_participation_type)
            sheet_link = safe_get(col_sheet_link)
            team_name = normalize_team_name(safe_get(col_team_name))
            project_domain = safe_get(col_project_domain)
            source = safe_get(col_source)
            is_group_registration = looks_like_sheet_url(sheet_link)
            wants_group_registration = looks_like_team_registration(participation_type)
            
            if is_ueh_str.lower() == "có":
                leader_school = "UEH"
            elif not is_ueh_str or is_ueh_str.lower() == "không" or is_ueh_str.lower() == "other":
                leader_school = "Khác"
            else:
                leader_school = is_ueh_str
            
            try:
                # Kiểm tra xem người điền form đã tồn tại trong DB chưa
                leader_exists = False
                if email:
                    existing_registration = db.query(Registration).filter(Registration.email == email).first()
                    if existing_registration:
                        leader_exists = True
                        report["logs"].append({"type": "warning", "msg": f"Email {email} đã tồn tại. Bỏ qua đăng ký cho user này."})
                        
                # Rẽ nhánh: Đăng ký Nhóm
                if is_group_registration:
                    report["teams_processed"] += 1
                    logger.info(f"Đang xử lý Nhóm: {team_name}")
                    report["logs"].append({"type": "info", "msg": f"⏳ Đang xử lý Nhóm '{team_name}' từ Google Sheet..."})
                    
                    # 1. Lấy Group ID
                    group_id = None
                    if team_name:
                        group_id = get_or_create_group(course_id, team_name)
                        
                    # 2. XỬ LÝ TRƯỞNG NHÓM (Người điền MS Forms) ĐỂ TRÁNH BỊ SÓT
                    if not leader_exists and email and full_name:
                        first_name, last_name = split_name(full_name)
                        leader = Member(
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            phone=phone,
                            student_id=student_id,
                            role="Leader",
                            school=leader_school
                        )
                        is_success, msg, user_meta = sync_member_to_moodle(leader, course_id, group_id)
                        if is_success:
                            report["success_count"] += 1
                            report["logs"].append({"type": "success", "msg": f"[Trưởng nhóm] {leader.full_name}: {msg}"})
                            if user_meta.get("is_new"):
                                report["new_users"].append({"Name": leader.full_name, "Email": leader.email, "Username": user_meta.get("username")})
                                
                            # Lưu vào DB
                            db.add(Registration(
                                full_name=leader.full_name, email=leader.email, 
                                student_id=leader.student_id, phone=leader.phone,
                                role=leader.role, team_name=team_name, school=leader.school,
                                project_domain=project_domain, source=source,
                                created_at=created_dt
                            ))
                            db.flush() # Đẩy xuống DB ngay để tránh insert đúp khi duyệt file sheet
                        else:
                            report["fail_count"] += 1
                            report["logs"].append({"type": "error", "msg": f"[Trưởng nhóm] {leader.full_name}: {msg}"})

                    # 3. Xử lý thành viên từ Google Sheet
                    extracted_team_name, members, parse_errors = process_sheet_url(sheet_link)
                    
                    if parse_errors:
                        report["logs"].append({"type": "warning", "msg": f"Nhóm '{team_name}' có lỗi data: {parse_errors}"})
                    
                    for member in members:
                        # Bỏ qua nếu thành viên này chính là Trưởng nhóm (đã được xử lý ở bước 2 hoặc đã tồn tại)
                        if email and member.email and member.email.lower().strip() == email.lower().strip():
                            continue
                            
                        # Kiểm tra xem thành viên này đã có trong DB chưa (trường hợp thêm thành viên mới vào sheet cũ)
                        if member.email:
                            existing_member = db.query(Registration).filter(Registration.email == member.email).first()
                            if existing_member:
                                report["logs"].append({"type": "warning", "msg": f"Thành viên {member.email} đã có trên hệ thống. Bỏ qua."})
                                continue

                        # Xử lý các thành viên còn lại
                        is_success, msg, user_meta = sync_member_to_moodle(member, course_id, group_id)
                        if is_success:
                            report["success_count"] += 1
                            report["logs"].append({"type": "success", "msg": f"{member.full_name}: {msg}"})
                            if user_meta.get("is_new"):
                                report["new_users"].append({"Name": member.full_name, "Email": member.email, "Username": user_meta.get("username")})
                            
                            db.add(Registration(
                                full_name=member.full_name, email=member.email, 
                                student_id=member.student_id, phone=member.phone,
                                role=member.role, team_name=team_name, school=member.school or "Khác",
                                project_domain=project_domain, source=source,
                                created_at=created_dt
                            ))
                            db.flush()
                        else:
                            report["fail_count"] += 1
                            report["logs"].append({"type": "error", "msg": f"{member.full_name}: {msg}"})
                            
                # Rẽ nhánh: Đăng ký Cá nhân
                elif wants_group_registration:
                    report["teams_processed"] += 1
                    report["logs"].append({
                        "type": "warning",
                        "msg": (
                            f"Nhóm '{team_name or full_name}' được đánh dấu là đăng ký nhóm "
                            "nhưng cột danh sách thành viên không có link Google Sheet hợp lệ. "
                            "Hệ thống chỉ xử lý trưởng nhóm, chưa thể thêm thành viên thiếu email."
                        )
                    })

                    group_id = get_or_create_group(course_id, team_name) if team_name else None

                    if leader_exists:
                        continue

                    if not email or not full_name:
                        continue

                    first_name, last_name = split_name(full_name)
                    leader = Member(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=phone,
                        student_id=student_id,
                        role="Leader",
                        school=leader_school
                    )

                    is_success, msg, user_meta = sync_member_to_moodle(leader, course_id, group_id)

                    if is_success:
                        report["success_count"] += 1
                        report["logs"].append({"type": "success", "msg": f"[Trưởng nhóm] {leader.full_name}: {msg}"})
                        if user_meta.get("is_new"):
                            report["new_users"].append({"Name": leader.full_name, "Email": leader.email, "Username": user_meta.get("username")})

                        db.add(Registration(
                            full_name=leader.full_name, email=leader.email,
                            student_id=leader.student_id, phone=leader.phone,
                            role=leader.role, team_name=team_name, school=leader.school,
                            project_domain=project_domain, source=source,
                            created_at=created_dt
                        ))
                        db.flush()
                    else:
                        report["fail_count"] += 1
                        report["logs"].append({"type": "error", "msg": f"[Trưởng nhóm] {leader.full_name}: {msg}"})

                else:
                    if leader_exists:
                        # Vì là cá nhân, nếu đã tồn tại thì dừng xử lý dòng này
                        continue
                        
                    if not email or not full_name:
                        continue # Dòng không hợp lệ
                        
                    report["individuals_processed"] += 1
                    logger.info(f"Đang xử lý Cá nhân: {full_name}")
                    
                    first_name, last_name = split_name(full_name)
                    member = Member(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=phone,
                        student_id=student_id,
                        role="Individual",
                        school=leader_school
                    )
                    
                    # Đồng bộ cá nhân (không gán Group)
                    is_success, msg, user_meta = sync_member_to_moodle(member, course_id, group_id=None)
                    
                    if is_success:
                        report["success_count"] += 1
                        report["logs"].append({"type": "success", "msg": f"[Cá nhân] {member.full_name}: {msg}"})
                        if user_meta.get("is_new"):
                            report["new_users"].append({"Name": member.full_name, "Email": member.email, "Username": user_meta.get("username")})
                            
                        db.add(Registration(
                            full_name=member.full_name, email=member.email, 
                            student_id=member.student_id, phone=member.phone,
                            role=member.role, team_name=None, school=member.school,
                            project_domain=project_domain, source=source,
                            created_at=created_dt
                        ))
                    else:
                        report["fail_count"] += 1
                        report["logs"].append({"type": "error", "msg": f"[Cá nhân] {member.full_name}: {msg}"})
                        
            except Exception as e:
                report["fail_count"] += 1
                report["logs"].append({"type": "error", "msg": f"Lỗi dòng {row_idx}: {str(e)}"})
                
        db.commit()
    finally:
        db.close()
        
    # Tạo file excel chứa user mới (in-memory) nếu có user mới
    if report["new_users"]:
        new_wb = openpyxl.Workbook()
        new_ws = new_wb.active
        new_ws.title = "New Users"
        new_ws.append(["Name", "Email", "Username", "Password"])
        for u in report["new_users"]:
            new_ws.append([u["Name"], u["Email"], u["Username"], "Sandbox@2026"])
            
        output = io.BytesIO()
        new_wb.save(output)
        output.seek(0)
        report["excel_base64"] = base64.b64encode(output.read()).decode("utf-8")
        
    return report

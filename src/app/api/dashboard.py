from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.app.core.database import get_db
from src.app.models.schema import Registration, SyncJob

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_users = db.query(func.count(Registration.id)).scalar()
    team_name_clean = func.nullif(func.trim(Registration.team_name), "")
    team_name_key = func.lower(team_name_clean)
    total_teams = (
        db.query(func.count(func.distinct(team_name_key)))
        .filter(team_name_clean.isnot(None))
        .scalar()
    )
    total_individuals = (
        db.query(func.count(Registration.id))
        .filter(team_name_clean.is_(None))
        .scalar()
    )
    
    # Số lượng theo ngày
    daily_registrations = db.query(
        func.date(Registration.created_at).label('date'),
        func.count(Registration.id).label('count')
    ).group_by(func.date(Registration.created_at)).order_by(func.date(Registration.created_at).asc()).all()
    
    daily_labels = [str(r.date) for r in daily_registrations]
    daily_data = [r.count for r in daily_registrations]
    
    # Số lượng theo trường
    school_registrations = db.query(
        Registration.school,
        func.count(Registration.id).label('count')
    ).filter(
        Registration.school != None
    ).group_by(Registration.school).order_by(func.count(Registration.id).desc()).all()
    
    school_labels = [r.school for r in school_registrations]
    school_data = [r.count for r in school_registrations]
    
    # Lĩnh vực dự án (chỉ đếm Leader và Individual để đại diện cho 1 dự án)
    domain_registrations = db.query(
        Registration.project_domain,
        func.count(Registration.id).label('count')
    ).filter(
        Registration.project_domain != None,
        Registration.role.in_(['Leader', 'Individual'])
    ).group_by(Registration.project_domain).order_by(func.count(Registration.id).desc()).all()
    
    domain_labels = [r.project_domain for r in domain_registrations]
    domain_data = [r.count for r in domain_registrations]

    # Nguồn biết đến
    source_registrations = db.query(
        Registration.source,
        func.count(Registration.id).label('count')
    ).filter(
        Registration.source != None
    ).group_by(Registration.source).order_by(func.count(Registration.id).desc()).all()

    source_labels = [r.source for r in source_registrations]
    source_data = [r.count for r in source_registrations]
    
    return {
        "summary": {
            "total_users": total_users,
            "total_teams": total_teams,
            "total_individuals": total_individuals,
        },
        "charts": {
            "daily_trend": {
                "labels": daily_labels,
                "data": daily_data
            },
            "university_distribution": {
                "labels": school_labels,
                "data": school_data
            },
            "project_domain_distribution": {
                "labels": domain_labels,
                "data": domain_data
            },
            "source_distribution": {
                "labels": source_labels,
                "data": source_data
            }
        }
    }

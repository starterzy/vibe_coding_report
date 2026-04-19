from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models import get_db, Department, User, RoleEnum
from backend.models.schemas import DepartmentResponse, DepartmentCreate
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/api/departments", tags=["部门"])

@router.get("", response_model=list[DepartmentResponse])
async def get_departments(db: Session = Depends(get_db)):
    depts = db.query(Department).all()
    return [DepartmentResponse(id=d.id, name=d.name) for d in depts]

@router.post("", response_model=DepartmentResponse)
async def create_department(
    dept: DepartmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.roles != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")

    existing = db.query(Department).filter(Department.name == dept.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department already exists")

    new_dept = Department(name=dept.name)
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    return DepartmentResponse(id=new_dept.id, name=new_dept.name)

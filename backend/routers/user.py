from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from backend.models import get_db, User, Department, UserDepartment, UserApproverSequence, RoleEnum
from backend.services.auth_service import get_current_user, get_password_hash
from pydantic import BaseModel

router = APIRouter(prefix="/api/users", tags=["用户管理"])

class UserCreate(BaseModel):
    username: str
    password: str
    roles: List[str] = []
    department_ids: List[int] = []
    approver_sequence_ids: List[int] = []
    phone: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    roles: Optional[List[str]] = None
    department_ids: Optional[List[int]] = None
    approver_sequence_ids: Optional[List[int]] = None
    phone: Optional[str] = None
    is_active: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    username: str
    roles: List[str]
    departments: List[str]
    approver_sequences: List[int]
    phone: Optional[str]
    is_active: int
    class Config:
        from_attributes = True

@router.get("", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role = current_user.roles.value if hasattr(current_user.roles, 'value') else str(current_user.roles)
    if user_role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")

    users = db.query(User).all()
    result = []
    for u in users:
        result.append(UserResponse(
            id=u.id,
            username=u.username,
            roles=[u.roles.value] if hasattr(u.roles, 'value') else [str(u.roles)],
            departments=[ud.department.name for ud in u.user_departments],
            approver_sequences=[seq.sequence for seq in u.approver_sequences],
            phone=u.phone,
            is_active=u.is_active
        ))
    return result

@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role = current_user.roles.value if hasattr(current_user.roles, 'value') else str(current_user.roles)
    if user_role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")

    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    if user_data.phone:
        existing_phone = db.query(User).filter(User.phone == user_data.phone).first()
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone already exists")

    role_enum = RoleEnum(user_data.roles[0]) if user_data.roles else RoleEnum.FILLER

    user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        roles=role_enum,
        phone=user_data.phone
    )
    db.add(user)
    db.flush()

    for dept_id in user_data.department_ids:
        ud = UserDepartment(user_id=user.id, department_id=dept_id)
        db.add(ud)

    for seq_id in user_data.approver_sequence_ids:
        uas = UserApproverSequence(user_id=user.id, sequence=seq_id)
        db.add(uas)

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        roles=[user.roles.value] if hasattr(user.roles, 'value') else [str(user.roles)],
        departments=[ud.department.name for ud in user.user_departments],
        approver_sequences=[seq.sequence for seq in user.approver_sequences],
        phone=user.phone,
        is_active=user.is_active
    )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role = current_user.roles.value if hasattr(current_user.roles, 'value') else str(current_user.roles)
    if user_role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_data.username:
        existing = db.query(User).filter(User.username == user_data.username, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        user.username = user_data.username

    if user_data.password:
        user.password_hash = get_password_hash(user_data.password)

    if user_data.roles:
        user.roles = RoleEnum(user_data.roles[0])

    if user_data.phone is not None:
        existing_phone = db.query(User).filter(User.phone == user_data.phone, User.id != user_id).first()
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone already exists")
        user.phone = user_data.phone

    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    if user_data.department_ids is not None:
        db.query(UserDepartment).filter(UserDepartment.user_id == user_id).delete()
        for dept_id in user_data.department_ids:
            ud = UserDepartment(user_id=user.id, department_id=dept_id)
            db.add(ud)

    if user_data.approver_sequence_ids is not None:
        db.query(UserApproverSequence).filter(UserApproverSequence.user_id == user_id).delete()
        for seq_id in user_data.approver_sequence_ids:
            uas = UserApproverSequence(user_id=user.id, sequence=seq_id)
            db.add(uas)

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        roles=[user.roles.value] if hasattr(user.roles, 'value') else [str(user.roles)],
        departments=[ud.department.name for ud in user.user_departments],
        approver_sequences=[seq.sequence for seq in user.approver_sequences],
        phone=user.phone,
        is_active=user.is_active
    )

@router.delete("/{user_id}")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role = current_user.roles.value if hasattr(current_user.roles, 'value') else str(current_user.roles)
    if user_role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = 0
    db.commit()

    return {"message": "User deactivated"}

@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role = current_user.roles.value if hasattr(current_user.roles, 'value') else str(current_user.roles)
    if user_role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = 1
    db.commit()

    return {"message": "User activated"}

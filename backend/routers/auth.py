from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.models import get_db, User, UserDepartment, Department
from backend.services.auth_service import authenticate_user, create_access_token, get_current_user, get_password_hash
from backend.models.schemas import LoginResponse, UserResponse, UserCreate, LoginRequest

router = APIRouter(prefix="/api/auth", tags=["认证"])

@router.post("/login", response_model=LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_access_token(data={"sub": user.username})
    departments = [ud.department.name for ud in user.user_departments]
    approver_sequences = [seq.sequence for seq in user.approver_sequences]
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            roles=[user.roles.value] if isinstance(user.roles, type) else [user.roles],
            departments=departments,
            approver_sequences=approver_sequences
        )
    )

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        roles=user_data.roles[0] if user_data.roles else None
    )
    db.add(user)
    db.flush()

    for dept_id in user_data.department_ids:
        ud = UserDepartment(user_id=user.id, department_id=dept_id)
        db.add(ud)

    db.commit()
    db.refresh(user)
    departments = [ud.department.name for ud in user.user_departments]
    return UserResponse(
        id=user.id,
        username=user.username,
        roles=[user.roles.value] if user.roles else [],
        departments=departments
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    departments = [ud.department.name for ud in current_user.user_departments]
    approver_sequences = [seq.sequence for seq in current_user.approver_sequences]
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        roles=[current_user.roles.value] if current_user.roles else [],
        departments=departments,
        approver_sequences=approver_sequences
    )

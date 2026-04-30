from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class RoleEnum(str, Enum):
    FILLER = "filler"
    APPROVER = "approver"
    LEADER = "leader"
    ADMIN = "admin"

class StatusEnum(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"

# 部门
class DepartmentBase(BaseModel):
    name: str

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: int
    class Config:
        from_attributes = True

# 用户
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    roles: List[RoleEnum] = []
    department_ids: List[int] = []
    approver_sequence_ids: List[int] = []  # 审批者可审批的序号列表

class UserResponse(UserBase):
    id: int
    roles: List[str] = []
    departments: List[str] = []
    approver_sequences: List[int] = []  # 审批者可审批的序号列表
    class Config:
        from_attributes = True

# 登录
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# 任务和措施
class MeasureResponse(BaseModel):
    id: int
    content: str
    task_id: int
    person_liable: Optional[str] = None
    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    id: int
    sequence: int
    name: str
    target: str
    leader: str
    department_name: str
    partner_depts: str
    deadline: str
    measures: List[MeasureResponse] = []
    class Config:
        from_attributes = True

# 填报记录（现在与 task_id 关联）
class ReportRecordBase(BaseModel):
    task_id: int  # 改为 task_id
    month: str  # YYYY-MM格式
    current_content: Optional[str] = None
    next_plan: Optional[str] = None

class ReportRecordCreate(ReportRecordBase):
    pass

class ReportRecordUpdate(BaseModel):
    current_content: Optional[str] = None
    next_plan: Optional[str] = None

class RejectRequest(BaseModel):
    reason: str  # 退回原因

class ReportRecordResponse(ReportRecordBase):
    id: int
    submitter_id: int
    submitter_name: str
    status: str
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    reject_reason: Optional[str] = None
    task_name: str
    task_sequence: int
    task_target: str = ""
    class Config:
        from_attributes = True

# 任务列表（包含填报状态）
class TaskWithReportStatus(BaseModel):
    task: TaskResponse
    monthly_status: dict  # {month: status}

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import datetime
from backend.models import get_db, User, Task, Measure, ReportRecord, Department, RoleEnum, StatusEnum, TaskLeader, TaskDepartment, TaskPartnerDepartment, UserApproverSequence
from backend.models.schemas import (
    TaskResponse, MeasureResponse, ReportRecordCreate, ReportRecordUpdate,
    ReportRecordResponse, RejectRequest
)
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/api/report", tags=["报表"])

def task_to_response(task: Task) -> TaskResponse:
    # 牵头领导 - 多人用换行分隔
    leader = "\n".join([l.leader_name for l in task.leaders]) if task.leaders else ""

    # 牵头部门 - 多个部门用换行分隔
    department_name = "\n".join([d.department.name for d in task.departments]) if task.departments else ""

    # 配合部门 - 多个部门用换行分隔
    partner_list = []
    for p in task.partner_departments:
        if p.department:
            partner_list.append(p.department.name)
        elif p.department_name:
            partner_list.append(p.department_name)
    partner_depts = "\n".join(partner_list) if partner_list else ""

    return TaskResponse(
        id=task.id,
        sequence=task.sequence,
        name=task.name,
        target=task.target,
        leader=leader,
        department_name=department_name,
        partner_depts=partner_depts,
        deadline=task.deadline or "",
        measures=[
            MeasureResponse(
                id=m.id,
                content=m.content,
                task_id=m.task_id,
                person_liable=m.person_liable
            ) for m in task.measures
        ]
    )

@router.get("/tasks", response_model=list[TaskResponse])
async def get_tasks(
    year: int = Query(2026),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tasks = db.query(Task).filter(Task.year == year).order_by(Task.sequence).all()
    return [task_to_response(t) for t in tasks]

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_to_response(task)

@router.get("/records", response_model=list[ReportRecordResponse])
async def get_records(
    month: Optional[str] = None,  # YYYY-MM格式
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(ReportRecord).options(
        joinedload(ReportRecord.measure).joinedload(Measure.task)
    )

    user_role = current_user.roles.value if hasattr(current_user.roles, 'value') else str(current_user.roles)

    # 权限控制：领导层只能看已审核的记录，其他人（管理、审批者、填报者）都能看到所有记录
    if user_role == 'leader':
        # 领导层只能看已审核的记录
        query = query.filter(ReportRecord.status == StatusEnum.APPROVED)
    # filler、approver、admin 都能看到所有记录，不需要额外过滤

    if status_filter:
        query = query.filter(ReportRecord.status == StatusEnum[status_filter.upper()])

    if month:
        query = query.filter(ReportRecord.month == month)

    records = query.all()
    result = []
    for r in records:
        result.append(ReportRecordResponse(
            id=r.id,
            measure_id=r.measure_id,
            submitter_id=r.submitter_id,
            submitter_name=r.submitter.username,
            month=r.month,
            current_content=r.current_content,
            next_plan=r.next_plan,
            status=r.status.value,
            submitted_at=r.submitted_at,
            reviewed_at=r.reviewed_at,
            reviewer_id=r.reviewer_id,
            reviewer_name=r.reviewer.username if r.reviewer else None,
            reject_reason=r.reject_reason,
            measure_content=r.measure.content,
            task_name=r.measure.task.name,
            task_sequence=r.measure.task.sequence
        ))
    return result

@router.post("/records", response_model=ReportRecordResponse)
async def create_record(
    record: ReportRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    measure = db.query(Measure).filter(Measure.id == record.measure_id).first()
    if not measure:
        raise HTTPException(status_code=404, detail="Measure not found")

    # 检查是否已存在当月记录
    existing = db.query(ReportRecord).filter(
        ReportRecord.measure_id == record.measure_id,
        ReportRecord.month == record.month
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Record already exists for this month")

    new_record = ReportRecord(
        measure_id=record.measure_id,
        submitter_id=current_user.id,
        month=record.month,
        current_content=record.current_content,
        next_plan=record.next_plan,
        status=StatusEnum.DRAFT
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return ReportRecordResponse(
        id=new_record.id,
        measure_id=new_record.measure_id,
        submitter_id=new_record.submitter_id,
        submitter_name=current_user.username,
        month=new_record.month,
        current_content=new_record.current_content,
        next_plan=new_record.next_plan,
        status=new_record.status.value,
        submitted_at=new_record.submitted_at,
        reviewed_at=new_record.reviewed_at,
        reviewer_id=new_record.reviewer_id,
        reviewer_name=None,
        measure_content=measure.content,
        task_name=measure.task.name,
        task_sequence=measure.task.sequence
    )

@router.put("/records/{record_id}", response_model=ReportRecordResponse)
async def update_record(
    record_id: int,
    update_data: ReportRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(ReportRecord).filter(ReportRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    user_role = current_user.roles.value if hasattr(current_user.roles, 'value') else str(current_user.roles)

    # 草稿可以修改，已审批的记录只有管理员可以修改
    if record.status.value == StatusEnum.APPROVED.value and user_role != 'admin':
        db.rollback()
        raise HTTPException(status_code=400, detail="已审核的记录无法修改")
    if record.status.value != StatusEnum.DRAFT.value and user_role not in ('approver', 'admin'):
        db.rollback()
        raise HTTPException(status_code=400, detail="Only draft records or approvers can modify")

    if update_data.current_content is not None:
        record.current_content = update_data.current_content
    if update_data.next_plan is not None:
        record.next_plan = update_data.next_plan

    db.commit()
    db.refresh(record)
    return ReportRecordResponse(
        id=record.id,
        measure_id=record.measure_id,
        submitter_id=record.submitter_id,
        submitter_name=record.submitter.username,
        month=record.month,
        current_content=record.current_content,
        next_plan=record.next_plan,
        status=record.status.value,
        submitted_at=record.submitted_at,
        reviewed_at=record.reviewed_at,
        reviewer_id=record.reviewer_id,
        reviewer_name=record.reviewer.username if record.reviewer else None,
        measure_content=record.measure.content,
        task_name=record.measure.task.name,
        task_sequence=record.measure.task.sequence
    )

@router.post("/records/{record_id}/submit", response_model=ReportRecordResponse)
async def submit_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(ReportRecord).filter(ReportRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.submitter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only submit your own records")

    record.status = StatusEnum.SUBMITTED
    record.submitted_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return ReportRecordResponse(
        id=record.id,
        measure_id=record.measure_id,
        submitter_id=record.submitter_id,
        submitter_name=current_user.username,
        month=record.month,
        current_content=record.current_content,
        next_plan=record.next_plan,
        status=record.status.value,
        submitted_at=record.submitted_at,
        reviewed_at=record.reviewed_at,
        reviewer_id=record.reviewer_id,
        reviewer_name=None,
        measure_content=record.measure.content,
        task_name=record.measure.task.name,
        task_sequence=record.measure.task.sequence
    )

def _check_approver_permission(user: User, record: ReportRecord, db: Session) -> None:
    """审批者权限检查：检查该记录对应的任务序号是否在审批者的可审批序号列表中"""
    user_role = user.roles.value if hasattr(user.roles, 'value') else str(user.roles)
    if user_role != 'approver':
        return

    task = db.query(Task).filter(Task.id == record.measure.task_id).first()
    task_sequence = task.sequence

    # 检查该序号是否在审批者的可审批序号列表中
    user_sequences = [seq.sequence for seq in user.approver_sequences]
    if task_sequence not in user_sequences:
        raise HTTPException(status_code=403, detail="No permission to approve this record")

@router.post("/records/{record_id}/approve", response_model=ReportRecordResponse)
async def approve_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role = current_user.roles.value if hasattr(current_user.roles, 'value') else str(current_user.roles)
    if user_role not in ('approver', 'admin'):
        raise HTTPException(status_code=403, detail="Only approvers can approve records")

    record = db.query(ReportRecord).filter(ReportRecord.id == record_id).first()
    if not record:
        db.rollback()
        raise HTTPException(status_code=404, detail="Record not found")
    if record.status.value == StatusEnum.APPROVED.value:
        db.rollback()
        raise HTTPException(status_code=400, detail="该记录已审核，请勿重复操作")
    if record.status.value != StatusEnum.SUBMITTED.value:
        db.rollback()
        raise HTTPException(status_code=400, detail="只能审核已提交的记录")

    # 审批者权限检查：按序号检查
    _check_approver_permission(current_user, record, db)

    record.status = StatusEnum.APPROVED
    record.reviewed_at = datetime.utcnow()
    record.reviewer_id = current_user.id
    db.commit()
    db.refresh(record)
    return ReportRecordResponse(
        id=record.id,
        measure_id=record.measure_id,
        submitter_id=record.submitter_id,
        submitter_name=record.submitter.username,
        month=record.month,
        current_content=record.current_content,
        next_plan=record.next_plan,
        status=record.status.value,
        submitted_at=record.submitted_at,
        reviewed_at=record.reviewed_at,
        reviewer_id=record.reviewer_id,
        reviewer_name=current_user.username,
        reject_reason=record.reject_reason,
        measure_content=record.measure.content,
        task_name=record.measure.task.name,
        task_sequence=record.measure.task.sequence
    )

@router.post("/records/{record_id}/reject", response_model=ReportRecordResponse)
async def reject_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role = current_user.roles.value if hasattr(current_user.roles, 'value') else str(current_user.roles)
    if user_role not in ('approver', 'admin'):
        raise HTTPException(status_code=403, detail="Only approvers can reject records")

    record = db.query(ReportRecord).filter(ReportRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.status.value != StatusEnum.SUBMITTED.value:
        raise HTTPException(status_code=400, detail="Can only reject submitted records")

    # 审批者权限检查：按序号检查
    _check_approver_permission(current_user, record, db)

    # 退回后恢复为草稿状态
    record.status = StatusEnum.DRAFT
    record.submitted_at = None
    db.commit()
    db.refresh(record)
    return ReportRecordResponse(
        id=record.id,
        measure_id=record.measure_id,
        submitter_id=record.submitter_id,
        submitter_name=current_user.username,
        month=record.month,
        current_content=record.current_content,
        next_plan=record.next_plan,
        status=record.status.value,
        submitted_at=record.submitted_at,
        reviewed_at=record.reviewed_at,
        reviewer_id=record.reviewer_id,
        reviewer_name=current_user.username,
        reject_reason=record.reject_reason,
        measure_content=record.measure.content,
        task_name=record.measure.task.name,
        task_sequence=record.measure.task.sequence
    )

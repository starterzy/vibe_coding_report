from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import datetime
from backend.models import get_db, User, Task, Measure, ReportRecord, Department, RoleEnum, StatusEnum
from backend.models.schemas import (
    TaskResponse, MeasureResponse, ReportRecordCreate, ReportRecordUpdate,
    ReportRecordResponse, RejectRequest
)
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/api/report", tags=["报表"])

def task_to_response(task: Task) -> TaskResponse:
    dept_name = task.department.name if task.department else ""
    return TaskResponse(
        id=task.id,
        sequence=task.sequence,
        name=task.name,
        target=task.target,
        leader=task.leader or "",
        department_name=dept_name,
        partner_depts=task.partner_depts or "",
        deadline=task.deadline or "",
        measures=[
            MeasureResponse(
                id=m.id,
                content=m.content,
                task_id=m.task_id
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

    # 权限控制：管理能看到所有记录，审批者能看到所有记录，填报者只能看自己的
    if current_user.roles == RoleEnum.FILLER:
        query = query.filter(ReportRecord.submitter_id == current_user.id)

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
            current_progress=r.current_progress or 0,
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
        current_progress=record.current_progress or 0,
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
        current_progress=new_record.current_progress or 0,
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

    if record.submitter_id != current_user.id and current_user.roles != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Cannot modify this record")

    # 草稿才能修改
    if record.status != StatusEnum.DRAFT and record.status.value != "draft":
        raise HTTPException(status_code=400, detail="Only draft records can be modified")

    if update_data.current_content is not None:
        record.current_content = update_data.current_content
    if update_data.next_plan is not None:
        record.next_plan = update_data.next_plan
    if update_data.current_progress is not None:
        record.current_progress = update_data.current_progress
    if update_data.status == StatusEnum.SUBMITTED and record.status == StatusEnum.DRAFT:
        record.status = StatusEnum.SUBMITTED
        record.submitted_at = datetime.utcnow()
    if update_data.status == StatusEnum.APPROVED and current_user.roles == RoleEnum.APPROVER:
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
        current_progress=record.current_progress or 0,
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
        current_progress=record.current_progress or 0,
        status=record.status.value,
        submitted_at=record.submitted_at,
        reviewed_at=record.reviewed_at,
        reviewer_id=record.reviewer_id,
        reviewer_name=None,
        measure_content=record.measure.content,
        task_name=record.measure.task.name,
        task_sequence=record.measure.task.sequence
    )

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
        raise HTTPException(status_code=404, detail="Record not found")
    if record.status.value != StatusEnum.SUBMITTED.value:
        raise HTTPException(status_code=400, detail="Can only approve submitted records")

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
        current_progress=record.current_progress or 0,
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

    # 退回后恢复为草稿状态
    record.status = StatusEnum.DRAFT
    record.submitted_at = None
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
        current_progress=record.current_progress or 0,
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

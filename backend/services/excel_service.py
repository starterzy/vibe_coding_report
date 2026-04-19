import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session
from backend.models.database import Task, Measure, Department, User, UserDepartment, RoleEnum, ReportRecord, StatusEnum
from backend.services.auth_service import get_password_hash
import re

def clean_text(text):
    if pd.isna(text):
        return None
    return str(text).strip()

def import_excel_to_db(db: Session, excel_path: str) -> dict:
    """导入Excel数据到数据库，返回导入统计"""
    df = pd.read_excel(excel_path, header=2)
    df.columns = [
        "序号", "重点工作", "主要目标任务", "牵头领导",
        "牵头部门", "配合部门", "完成时间", "年度工作措施",
        "责任人", "具体举措", "本月工作内容", "下月工作计划"
    ]
    df = df.dropna(subset=["序号"])
    df["序号"] = df["序号"].astype(int)

    stats = {"tasks": 0, "measures": 0, "departments": set()}

    current_task = None
    for _, row in df.iterrows():
        seq = int(row["序号"])
        task_name = clean_text(row["重点工作"])
        target = clean_text(row["主要目标任务"])
        leader = clean_text(row["牵头领导"])
        dept_name = clean_text(row["牵头部门"])
        partner_depts = clean_text(row["配合部门"])
        deadline = clean_text(row["完成时间"])
        measure_content = clean_text(row["年度工作措施"])
        person_liable = clean_text(row["责任人"])

        if pd.isna(seq) or pd.isna(task_name):
            continue

        # 获取或创建部门
        dept = db.query(Department).filter(Department.name == dept_name).first()
        if not dept:
            dept = Department(name=dept_name)
            db.add(dept)
            db.flush()
            stats["departments"].add(dept_name)

        # 创建或更新任务
        if current_task is None or current_task.sequence != seq:
            current_task = Task(
                sequence=seq,
                name=task_name,
                target=target or "",
                leader=leader or "",
                department_id=dept.id,
                partner_depts=partner_depts or "",
                deadline=deadline or "",
                year=2026
            )
            db.add(current_task)
            db.flush()
            stats["tasks"] += 1

        # 创建措施
        if measure_content:
            measure = Measure(
                task_id=current_task.id,
                content=measure_content,
                person_liable=person_liable or ""
            )
            db.add(measure)
            stats["measures"] += 1

    db.commit()
    stats["departments"] = len(stats["departments"])
    return stats

def create_default_users(db: Session):
    """创建默认用户用于测试"""
    # 管理者
    if not db.query(User).filter(User.username == "admin").first():
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            roles=RoleEnum.ADMIN
        )
        db.add(admin)

    # 填报者
    if not db.query(User).filter(User.username == "filler").first():
        filler = User(
            username="filler",
            password_hash=get_password_hash("filler123"),
            roles=RoleEnum.FILLER
        )
        db.add(filler)

    # 审批者
    if not db.query(User).filter(User.username == "approver").first():
        approver = User(
            username="approver",
            password_hash=get_password_hash("approver123"),
            roles=RoleEnum.APPROVER
        )
        db.add(approver)

    db.commit()

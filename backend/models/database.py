from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import enum

SQLALCHEMY_DATABASE_URL = "sqlite:///./report.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RoleEnum(enum.Enum):
    FILLER = "filler"      # 填报者
    APPROVER = "approver"  # 审批者
    ADMIN = "admin"        # 管理者

class StatusEnum(enum.Enum):
    DRAFT = "draft"        # 草稿
    SUBMITTED = "submitted"  # 已提交
    APPROVED = "approved"    # 已审核

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    users = relationship("UserDepartment", back_populates="department")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    roles = Column(SQLEnum(RoleEnum), default=RoleEnum.FILLER)
    user_departments = relationship("UserDepartment", back_populates="user")
    submitted_records = relationship("ReportRecord", back_populates="submitter", foreign_keys="ReportRecord.submitter_id")
    reviewed_records = relationship("ReportRecord", back_populates="reviewer", foreign_keys="ReportRecord.reviewer_id")

class UserDepartment(Base):
    __tablename__ = "user_departments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    user = relationship("User", back_populates="user_departments")
    department = relationship("Department", back_populates="users")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    sequence = Column(Integer, nullable=False)  # 序号
    name = Column(String(100), nullable=False)     # 重点工作名称
    target = Column(Text, nullable=False)         # 主要目标任务
    leader = Column(String(100))                  # 牵头领导
    department_id = Column(Integer, ForeignKey("departments.id"))  # 牵头部门
    partner_depts = Column(String(200))            # 配合部门
    deadline = Column(String(50))                  # 完成时间
    year = Column(Integer, default=2026)
    measures = relationship("Measure", back_populates="task")
    department = relationship("Department")

class Measure(Base):
    __tablename__ = "measures"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    content = Column(Text, nullable=False)        # 年度工作措施
    person_liable = Column(String(100))             # 责任人
    task = relationship("Task", back_populates="measures")
    report_records = relationship("ReportRecord", back_populates="measure")

class ReportRecord(Base):
    __tablename__ = "report_records"
    id = Column(Integer, primary_key=True, index=True)
    measure_id = Column(Integer, ForeignKey("measures.id"), nullable=False)
    submitter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    month = Column(Integer, nullable=False)        # 填报月份 1-12
    year = Column(Integer, default=2026)
    current_content = Column(Text)                 # 本月工作内容
    next_plan = Column(Text)                       # 下月工作计划
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.DRAFT)
    submitted_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    measure = relationship("Measure", back_populates="report_records")
    submitter = relationship("User", back_populates="submitted_records", foreign_keys=[submitter_id])
    reviewer = relationship("User", back_populates="reviewed_records", foreign_keys=[reviewer_id])

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.models.database import init_db
from backend.routers import auth, report, department, wework
from backend.services.excel_service import import_excel_to_db, create_default_users
from pathlib import Path

@asynccontextmanager
async def lifespan(app: FastAPI):
    from backend.models.database import SessionLocal
    init_db()
    db = SessionLocal()
    try:
        create_default_users(db)
        from backend.models.database import Task
        if db.query(Task).count() == 0:
            excel_path = Path(__file__).parent.parent / "2026年度集团总部重点工作任务分解表（填写责任人和举措）.xlsx"
            if excel_path.exists():
                stats = import_excel_to_db(db, str(excel_path))
                print(f"Imported: {stats['tasks']} tasks, {stats['measures']} measures, {stats['departments']} departments")
    finally:
        db.close()
    yield

app = FastAPI(title="报表系统 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(report.router)
app.include_router(department.router)
app.include_router(wework.router)

@app.get("/")
def root():
    return {"message": "报表系统 API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

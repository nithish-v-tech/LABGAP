from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.connection import engine, Base, SessionLocal
from app.database.models import User
from seed import seed_database

# Import routers
from app.api.auth import router as auth_router
from app.api.laboratories import router as labs_router
from app.api.experiments import router as experiments_router
from app.api.equipment import router as equipment_router
from app.api.batches import router as batches_router
from app.api.faculty import router as faculty_router
from app.api.students import router as students_router
from app.api.analysis import router as analysis_router
from app.api.verification import router as verification_router
from app.api.schedule import router as schedule_router
from app.api.repairs import router as repairs_router
from app.api.csv_import import router as csv_router
from app.api.reports import router as reports_router
from app.api.demo import router as demo_router

# Create database tables
Base.metadata.create_all(bind=engine)

# Auto seed if users table is empty
db = SessionLocal()
try:
    if db.query(User).count() == 0:
        print("[LABGAP Startup] Database empty, seeding synthetic demo dataset...")
        seed_database()
finally:
    db.close()

app = FastAPI(
    title="LABGAP API",
    description="Practical Learning Coverage and Resource Optimization System - Round 1 Working Prototype",
    version=settings.PROJECT_VERSION
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(labs_router, prefix=settings.API_V1_STR)
app.include_router(experiments_router, prefix=settings.API_V1_STR)
app.include_router(equipment_router, prefix=settings.API_V1_STR)
app.include_router(batches_router, prefix=settings.API_V1_STR)
app.include_router(faculty_router, prefix=settings.API_V1_STR)
app.include_router(students_router, prefix=settings.API_V1_STR)
app.include_router(analysis_router, prefix=settings.API_V1_STR)
app.include_router(verification_router, prefix=settings.API_V1_STR)
app.include_router(schedule_router, prefix=settings.API_V1_STR)
app.include_router(repairs_router, prefix=settings.API_V1_STR)
app.include_router(csv_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(demo_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "system": "LABGAP",
        "name": "Practical Learning Coverage and Resource Optimization System",
        "track": "Track 5 — Civic Engagement & Campus Community",
        "status": "Online",
        "version": settings.PROJECT_VERSION,
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "LABGAP Core API"}

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine
from app.models.models import Base
from app.api import auth, analyze, report
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    # Startup
    logger.info("Starting AIVisibility.pro API...")

    # Start background worker thread
    try:
        from background_worker import start_background_worker
        start_background_worker()
        logger.info("Background worker started successfully")
    except Exception as e:
        logger.warning(f"Could not start background worker: {e}")

    # Initialize database with correct enum types
    try:
        # Use separate transaction for enum fix
        async with engine.connect() as conn:
            try:
                # Check if checkstatus enum exists and has correct values
                result = await conn.execute(text("""
                    SELECT enumlabel
                    FROM pg_enum
                    WHERE enumtypid = (
                        SELECT oid FROM pg_type WHERE typname = 'checkstatus'
                    )
                    ORDER BY enumsortorder;
                """))

                current_values = [row[0] for row in result]
                logger.info(f"Current checkstatus enum values: {current_values}")

                # If 'pass' is not in the enum, add it
                if current_values and 'pass' not in current_values:
                    logger.warning("CheckStatus enum missing 'pass' value, adding it...")

                    # PostgreSQL 9.1+ supports ALTER TYPE ... ADD VALUE
                    await conn.execute(text("""
                        ALTER TYPE checkstatus ADD VALUE IF NOT EXISTS 'pass';
                    """))
                    await conn.commit()
                    logger.info("Added 'pass' value to CheckStatus enum!")

            except Exception as enum_error:
                logger.info(f"Enum check result: {enum_error}")
                # If adding value fails, try recreating the enum
                try:
                    async with engine.begin() as tx_conn:
                        logger.info("Attempting to recreate enum with correct values...")

                        # Check if table exists
                        table_check = await tx_conn.execute(text("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables
                                WHERE table_name = 'analysis_results'
                            );
                        """))
                        table_exists = table_check.scalar()

                        if table_exists:
                            # Drop the column temporarily
                            await tx_conn.execute(text("""
                                ALTER TABLE analysis_results DROP COLUMN IF EXISTS status;
                            """))

                        # Drop and recreate the enum
                        await tx_conn.execute(text("""
                            DROP TYPE IF EXISTS checkstatus CASCADE;
                            CREATE TYPE checkstatus AS ENUM ('pass', 'warn', 'fail');
                        """))

                        if table_exists:
                            # Re-add the column
                            await tx_conn.execute(text("""
                                ALTER TABLE analysis_results
                                ADD COLUMN status checkstatus NOT NULL DEFAULT 'warn';
                            """))

                        logger.info("Enum recreated successfully!")
                except Exception as recreate_error:
                    logger.error(f"Failed to recreate enum: {recreate_error}")

        # Now create/verify tables in a new transaction
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created/verified")

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Continue anyway - the app might still work

    yield

    # Shutdown
    logger.info("Shutting down AIVisibility.pro API...")
    await engine.dispose()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Visibility Analysis Platform - Analyze why your website doesn't appear in AI search results",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "https://aivis ability.pro"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(report.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "auth": "/api/auth",
            "analyze": "/api/analyze",
            "report": "/api/report",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        # Get worker status
        try:
            from background_worker import get_worker_status
            worker_status = get_worker_status()
        except:
            worker_status = {"healthy": False, "running": False}

        return {
            "status": "healthy",
            "database": "connected",
            "worker": worker_status,
            "version": settings.APP_VERSION
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.get("/api/worker/status")
async def worker_status():
    """Get detailed worker status"""
    try:
        from background_worker import get_worker_status
        return get_worker_status()
    except Exception as e:
        logger.error(f"Failed to get worker status: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get worker status"}
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again later."
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
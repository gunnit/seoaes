from celery import Task, chain, group
from app.workers.celery_app import celery_app
from app.services.analyzer import WebsiteAnalyzer
from app.core.database import AsyncSessionLocal
from app.models.models import AnalysisRun, AnalysisStatus
from typing import Dict, Any, List
from uuid import UUID
import asyncio
import logging

logger = logging.getLogger(__name__)

class AnalysisTask(Task):
    """Base task class for analysis tasks"""
    autoretry_for = (Exception,)
    max_retries = 3
    retry_backoff = True

@celery_app.task(bind=True, base=AnalysisTask, name="analyze_website_task")
def analyze_website_task(self, url: str, analysis_run_id: str, user_id: str = None):
    """Main task to orchestrate website analysis"""
    try:
        # Create task chain for progressive analysis
        analysis_chain = chain(
            instant_checks_task.s(url, analysis_run_id),
            technical_checks_task.s(url, analysis_run_id),
            content_analysis_task.s(url, analysis_run_id),
            ai_analysis_task.s(url, analysis_run_id, user_id),
            finalize_analysis_task.s(analysis_run_id)
        )

        # Execute chain
        result = analysis_chain.apply_async()
        return {"status": "started", "task_id": result.id}

    except Exception as e:
        logger.error(f"Analysis task failed: {e}")
        # Update analysis status to failed
        asyncio.run(mark_analysis_failed(analysis_run_id, str(e)))
        raise

@celery_app.task(name="instant_checks_task")
def instant_checks_task(previous_result: Any, url: str, analysis_run_id: str):
    """Stage 1: Instant checks (0-5 seconds)"""
    try:
        result = asyncio.run(run_instant_checks_async(url, analysis_run_id))
        return {"stage": "instant", "results": result}
    except Exception as e:
        logger.error(f"Instant checks failed: {e}")
        raise

@celery_app.task(name="technical_checks_task")
def technical_checks_task(previous_result: Any, url: str, analysis_run_id: str):
    """Stage 2: Technical analysis (5-15 seconds)"""
    try:
        result = asyncio.run(run_technical_checks_async(url, analysis_run_id))
        return {"stage": "technical", "results": result}
    except Exception as e:
        logger.error(f"Technical checks failed: {e}")
        raise

@celery_app.task(name="content_analysis_task")
def content_analysis_task(previous_result: Any, url: str, analysis_run_id: str):
    """Stage 3: Content analysis (15-30 seconds)"""
    try:
        result = asyncio.run(run_content_analysis_async(url, analysis_run_id))
        return {"stage": "content", "results": result}
    except Exception as e:
        logger.error(f"Content analysis failed: {e}")
        raise

@celery_app.task(name="ai_analysis_task")
def ai_analysis_task(previous_result: Any, url: str, analysis_run_id: str, user_id: str = None):
    """Stage 4: AI-powered analysis (30-60 seconds)"""
    try:
        result = asyncio.run(run_ai_analysis_async(url, analysis_run_id, user_id))
        return {"stage": "ai", "results": result}
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        raise

@celery_app.task(name="finalize_analysis_task")
def finalize_analysis_task(previous_result: Any, analysis_run_id: str):
    """Finalize analysis and calculate overall score"""
    try:
        result = asyncio.run(finalize_analysis_async(analysis_run_id))
        return {"stage": "complete", "result": result}
    except Exception as e:
        logger.error(f"Finalization failed: {e}")
        raise

# Async helper functions
async def run_instant_checks_async(url: str, analysis_run_id: str) -> Dict[str, Any]:
    """Run instant checks asynchronously"""
    async with AsyncSessionLocal() as db:
        analyzer = WebsiteAnalyzer(db)
        try:
            # Update progress
            await update_analysis_progress(db, analysis_run_id, 5, "Running instant checks...")

            # Run checks
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            results = await analyzer.run_instant_checks(url, base_url)

            # Save results
            await analyzer.save_results(UUID(analysis_run_id), results)

            # Update progress
            await update_analysis_progress(db, analysis_run_id, 20, "Instant checks complete")

            return {"checks_run": len(results), "status": "complete"}
        finally:
            await analyzer.close()

async def run_technical_checks_async(url: str, analysis_run_id: str) -> Dict[str, Any]:
    """Run technical analysis asynchronously"""
    async with AsyncSessionLocal() as db:
        analyzer = WebsiteAnalyzer(db)
        try:
            # Update progress
            await update_analysis_progress(db, analysis_run_id, 25, "Running technical analysis...")

            # Run checks
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            results = await analyzer.run_technical_analysis(url, base_url)

            # Save results
            await analyzer.save_results(UUID(analysis_run_id), results)

            # Update progress
            await update_analysis_progress(db, analysis_run_id, 45, "Technical analysis complete")

            return {"checks_run": len(results), "status": "complete"}
        finally:
            await analyzer.close()

async def run_content_analysis_async(url: str, analysis_run_id: str) -> Dict[str, Any]:
    """Run content analysis asynchronously"""
    async with AsyncSessionLocal() as db:
        analyzer = WebsiteAnalyzer(db)
        try:
            # Update progress
            await update_analysis_progress(db, analysis_run_id, 50, "Analyzing content structure...")

            # Run checks
            results = await analyzer.run_content_analysis(url)

            # Save results
            await analyzer.save_results(UUID(analysis_run_id), results)

            # Update progress
            await update_analysis_progress(db, analysis_run_id, 70, "Content analysis complete")

            return {"checks_run": len(results), "status": "complete"}
        finally:
            await analyzer.close()

async def run_ai_analysis_async(url: str, analysis_run_id: str, user_id: str = None) -> Dict[str, Any]:
    """Run AI-powered analysis asynchronously"""
    async with AsyncSessionLocal() as db:
        analyzer = WebsiteAnalyzer(db)
        try:
            # Update progress
            await update_analysis_progress(db, analysis_run_id, 75, "Running AI-powered analysis...")

            # Run checks
            results = await analyzer.run_ai_analysis(url, UUID(analysis_run_id))

            # Save results
            await analyzer.save_results(UUID(analysis_run_id), results)

            # Update progress
            await update_analysis_progress(db, analysis_run_id, 95, "AI analysis complete")

            return {"checks_run": len(results), "status": "complete"}
        finally:
            await analyzer.close()

async def finalize_analysis_async(analysis_run_id: str) -> Dict[str, Any]:
    """Finalize analysis and calculate overall score"""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from app.models.models import AnalysisResult
        from datetime import datetime

        # Get all results
        result = await db.execute(
            select(AnalysisResult).where(AnalysisResult.analysis_run_id == UUID(analysis_run_id))
        )
        all_results = result.scalars().all()

        # Calculate overall score
        analyzer = WebsiteAnalyzer(db)
        results_dicts = [
            {
                "check_category": r.check_category,
                "score": r.score,
                "status": r.status
            }
            for r in all_results
        ]
        overall_score = await analyzer.calculate_overall_score(results_dicts)

        # Update analysis run
        analysis = await db.get(AnalysisRun, UUID(analysis_run_id))
        if analysis:
            analysis.status = AnalysisStatus.complete
            analysis.overall_score = overall_score
            analysis.progress = 100
            analysis.completed_at = datetime.utcnow()
            analysis.total_checks_run = len(all_results)
            analysis.total_issues_found = sum(1 for r in all_results if r.status.value != "pass")
            await db.commit()

        await analyzer.close()

        return {
            "overall_score": overall_score,
            "total_checks": len(all_results),
            "status": "complete"
        }

async def update_analysis_progress(db, analysis_run_id: str, progress: int, message: str):
    """Update analysis progress in database"""
    analysis = await db.get(AnalysisRun, UUID(analysis_run_id))
    if analysis:
        analysis.progress = progress
        await db.commit()

async def mark_analysis_failed(analysis_run_id: str, error_message: str):
    """Mark analysis as failed"""
    async with AsyncSessionLocal() as db:
        analysis = await db.get(AnalysisRun, UUID(analysis_run_id))
        if analysis:
            analysis.status = AnalysisStatus.failed
            analysis.error_message = error_message
            await db.commit()
"""
Background worker that runs in a separate thread
"""
import os
import json
import asyncio
import logging
import threading
from uuid import UUID
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# Global variable to track worker status
WORKER_STATUS = {
    'running': False,
    'last_heartbeat': None,
    'tasks_processed': 0,
    'last_task': None,
    'started_at': None
}

async def update_analysis_in_db(analysis_id: str, status: str, progress: int, score: int = None):
    """Update analysis status directly in database"""
    from app.core.database import AsyncSessionLocal
    from app.models.models import AnalysisRun, AnalysisStatus, AnalysisResult, CheckStatus

    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select
            result = await db.execute(
                select(AnalysisRun).where(AnalysisRun.id == UUID(analysis_id))
            )
            analysis = result.scalar_one_or_none()

            if analysis:
                analysis.status = AnalysisStatus[status] if isinstance(status, str) else status
                analysis.progress = progress
                if score is not None:
                    analysis.overall_score = score
                    analysis.total_issues_found = 2  # Sample value
                if progress == 100:
                    analysis.completed_at = datetime.utcnow()

                # Add sample results when complete
                if progress == 100:
                    # Add sample analysis results
                    sample_checks = [
                        ('ai_access', 'robots_txt_check', CheckStatus.pass_check, 100,
                         'Robots.txt allows AI crawlers', 'No action needed', 'critical', 'easy', '5 minutes'),
                        ('technical_seo', 'ssl_check', CheckStatus.pass_check, 100,
                         'SSL certificate is valid', 'No action needed', 'high', 'easy', '0 minutes'),
                        ('content_quality', 'headings_check', CheckStatus.warn, 70,
                         'Missing H1 tag on some pages', 'Add H1 tags to all pages', 'medium', 'easy', '30 minutes'),
                        ('site_structure', 'sitemap_check', CheckStatus.fail, 40,
                         'No sitemap.xml found', 'Create and submit sitemap.xml', 'high', 'medium', '1 hour')
                    ]

                    for category, check_name, status, score, details, recommendations, impact, difficulty, time_est in sample_checks:
                        result = AnalysisResult(
                            analysis_run_id=UUID(analysis_id),
                            check_category=category,
                            check_name=check_name,
                            status=status,
                            score=score,
                            details=details,
                            recommendations=recommendations,
                            impact_level=impact,
                            fix_difficulty=difficulty,
                            fix_time_estimate=time_est
                        )
                        db.add(result)

                await db.commit()
                logger.info(f"Updated analysis {analysis_id}: status={status}, progress={progress}")
        except Exception as e:
            logger.error(f"Failed to update analysis: {e}")

async def process_analysis(url: str, analysis_id: str):
    """Simulate analysis processing"""
    try:
        logger.info(f"Starting analysis for {url} (ID: {analysis_id})")

        # Simulate stages with progress updates
        stages = [
            (10, 'in_progress', None, 2),
            (25, 'in_progress', None, 3),
            (40, 'in_progress', None, 3),
            (60, 'in_progress', None, 3),
            (80, 'in_progress', None, 3),
            (100, 'complete', 77, 2),
        ]

        for progress, status, score, delay in stages:
            await update_analysis_in_db(analysis_id, status, progress, score)
            await asyncio.sleep(delay)

        logger.info(f"Analysis completed for {url}")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        await update_analysis_in_db(analysis_id, 'failed', 0)

def worker_thread():
    """Worker thread that processes tasks from Redis"""
    import redis

    global WORKER_STATUS
    WORKER_STATUS['started_at'] = datetime.utcnow()
    WORKER_STATUS['running'] = True

    logger.info("Background worker thread started")
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        logger.info(f"Connected to Redis at {redis_url}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        WORKER_STATUS['running'] = False
        return

    while WORKER_STATUS['running']:
        try:
            # Update heartbeat
            WORKER_STATUS['last_heartbeat'] = datetime.utcnow()

            # Check for tasks in Redis queue
            task_data = redis_client.lpop('analysis_queue')

            if task_data:
                task = json.loads(task_data) if isinstance(task_data, str) else task_data
                url = task.get('url')
                analysis_id = task.get('analysis_id')

                logger.info(f"Processing task from queue: {url} ({analysis_id})")
                WORKER_STATUS['last_task'] = {'url': url, 'id': analysis_id, 'time': datetime.utcnow()}

                # Run async processing
                asyncio.run(process_analysis(url, analysis_id))
                WORKER_STATUS['tasks_processed'] += 1
            else:
                # No tasks, wait a bit
                time.sleep(5)

        except Exception as e:
            logger.error(f"Error in worker thread: {e}")
            time.sleep(10)

def start_background_worker():
    """Start the background worker in a separate thread"""
    thread = threading.Thread(target=worker_thread, daemon=True)
    thread.start()
    logger.info("Background worker thread launched")

def get_worker_status():
    """Get the current status of the background worker"""
    global WORKER_STATUS
    status = WORKER_STATUS.copy()

    # Convert datetime objects to strings for JSON serialization
    if status['last_heartbeat']:
        status['last_heartbeat'] = status['last_heartbeat'].isoformat()
    if status['started_at']:
        status['started_at'] = status['started_at'].isoformat()
    if status['last_task'] and 'time' in status['last_task']:
        status['last_task']['time'] = status['last_task']['time'].isoformat()

    # Check if worker is healthy (heartbeat within last 30 seconds)
    if WORKER_STATUS['last_heartbeat']:
        time_since_heartbeat = (datetime.utcnow() - WORKER_STATUS['last_heartbeat']).total_seconds()
        status['healthy'] = time_since_heartbeat < 30
    else:
        status['healthy'] = False

    return status
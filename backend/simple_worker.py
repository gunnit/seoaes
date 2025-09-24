#!/usr/bin/env python
"""
Simple worker for processing analysis tasks without complex dependencies
"""
import os
import time
import json
import asyncio
import logging
from uuid import UUID
from datetime import datetime
import redis
import asyncpg
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

async def get_db_connection():
    """Create database connection"""
    database_url = os.getenv('DATABASE_URL', '')
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

    # Remove query parameters for asyncpg
    if '?' in database_url:
        database_url = database_url.split('?')[0]

    # For asyncpg, we need the raw URL without the protocol prefix
    if database_url.startswith('postgresql+asyncpg://'):
        database_url = database_url.replace('postgresql+asyncpg://', '', 1)

    return await asyncpg.connect(f'postgresql://{database_url}')

async def update_analysis_status(analysis_id: str, status: str, progress: int = 0):
    """Update analysis status in database"""
    try:
        conn = await get_db_connection()
        await conn.execute(
            """
            UPDATE analysis_runs
            SET status = $1, progress = $2, updated_at = $3
            WHERE id = $4
            """,
            status, progress, datetime.utcnow(), UUID(analysis_id)
        )
        await conn.close()
        logger.info(f"Updated analysis {analysis_id}: status={status}, progress={progress}")
    except Exception as e:
        logger.error(f"Failed to update analysis status: {e}")

async def simulate_analysis(url: str, analysis_id: str):
    """Simulate website analysis with progress updates"""
    try:
        logger.info(f"Starting analysis for {url} (ID: {analysis_id})")

        # Stage 1: Instant checks (0-25%)
        await update_analysis_status(analysis_id, 'in_progress', 5)
        await asyncio.sleep(2)

        await update_analysis_status(analysis_id, 'in_progress', 15)
        await asyncio.sleep(2)

        await update_analysis_status(analysis_id, 'in_progress', 25)

        # Stage 2: Technical analysis (25-50%)
        await asyncio.sleep(3)
        await update_analysis_status(analysis_id, 'in_progress', 35)

        await asyncio.sleep(3)
        await update_analysis_status(analysis_id, 'in_progress', 50)

        # Stage 3: Content analysis (50-75%)
        await asyncio.sleep(3)
        await update_analysis_status(analysis_id, 'in_progress', 60)

        await asyncio.sleep(3)
        await update_analysis_status(analysis_id, 'in_progress', 75)

        # Stage 4: AI analysis (75-100%)
        await asyncio.sleep(3)
        await update_analysis_status(analysis_id, 'in_progress', 90)

        await asyncio.sleep(2)
        await update_analysis_status(analysis_id, 'complete', 100)

        logger.info(f"Analysis completed for {url}")

        # Store some sample results
        conn = await get_db_connection()

        # Add sample analysis results
        sample_checks = [
            ('ai_access', 'robots_txt_check', 'pass', 100, 'Robots.txt allows AI crawlers'),
            ('technical_seo', 'ssl_check', 'pass', 100, 'SSL certificate is valid'),
            ('content_quality', 'headings_check', 'warn', 70, 'Missing H1 tag on some pages'),
            ('site_structure', 'sitemap_check', 'fail', 40, 'No sitemap.xml found')
        ]

        for category, check_name, status, score, details in sample_checks:
            await conn.execute(
                """
                INSERT INTO analysis_results
                (analysis_run_id, check_category, check_name, status, score, details, recommendations)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                UUID(analysis_id), category, check_name, status, score,
                details, 'Fix this issue to improve AI visibility'
            )

        # Update final score
        await conn.execute(
            """
            UPDATE analysis_runs
            SET overall_score = 77, total_issues_found = 2, completed_at = $1
            WHERE id = $2
            """,
            datetime.utcnow(), UUID(analysis_id)
        )

        await conn.close()

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        await update_analysis_status(analysis_id, 'failed', 0)

async def process_queue():
    """Process analysis tasks from Redis queue"""
    logger.info("Simple worker started, waiting for tasks...")

    while True:
        try:
            # Check for tasks in Redis queue
            task_data = redis_client.lpop('analysis_queue')

            if task_data:
                task = json.loads(task_data)
                url = task.get('url')
                analysis_id = task.get('analysis_id')

                logger.info(f"Processing task: {url} ({analysis_id})")
                await simulate_analysis(url, analysis_id)
            else:
                # No tasks, wait a bit
                await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error processing queue: {e}")
            await asyncio.sleep(10)

def main():
    """Main entry point"""
    logger.info("Starting simple analysis worker...")
    asyncio.run(process_queue())

if __name__ == "__main__":
    main()
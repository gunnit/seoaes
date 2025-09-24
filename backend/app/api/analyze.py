from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db, engine
from app.api.auth import get_current_user
from app.models.models import User, Website, AnalysisRun, AnalysisResult, AnalysisStatus, CheckStatus
from app.schemas.schemas import (
    AnalysisRequest, AnalysisRunResponse, FreeAnalysisResponse,
    AnalysisProgressUpdate, SSEEvent, AnalysisResultSchema
)
from app.services.analyzer import WebsiteAnalyzer
from app.workers.tasks import analyze_website_task
from typing import Optional, List, AsyncGenerator
from uuid import UUID
from datetime import datetime
import asyncio
import json
from urllib.parse import urlparse

router = APIRouter(prefix="/api/analyze", tags=["Analysis"])

# In-memory storage for SSE connections (replace with Redis in production)
active_connections = {}

@router.post("/free", response_model=FreeAnalysisResponse)
async def analyze_free(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start free analysis without authentication.
    Shows first 3 issues to demonstrate value.
    """
    url = str(request.url)
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    # Check if website exists or create new one
    result = await db.execute(
        select(Website).where(Website.domain == domain)
    )
    website = result.scalar_one_or_none()

    if not website:
        website = Website(
            url=url,
            domain=domain,
            user_id=None,  # Anonymous user
            created_at=datetime.utcnow()
        )
        db.add(website)
        await db.commit()
        await db.refresh(website)

    # Create analysis run
    analysis_run = AnalysisRun(
        website_id=website.id,
        user_id=None,  # Anonymous
        status=AnalysisStatus.pending,
        progress=0,
        started_at=datetime.utcnow()
    )
    db.add(analysis_run)
    await db.commit()
    await db.refresh(analysis_run)

    # Queue analysis task
    try:
        # Try Celery first
        from app.workers.tasks import analyze_website_task
        task_result = analyze_website_task.delay(url, str(analysis_run.id), None)
    except:
        # Fallback to Redis queue for simple worker
        import redis
        import json
        import os
        redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        task = {'url': url, 'analysis_id': str(analysis_run.id)}
        redis_client.rpush('analysis_queue', json.dumps(task))

    # Return initial response
    return FreeAnalysisResponse(
        id=analysis_run.id,
        url=url,
        status=analysis_run.status,
        progress=0,
        preview_results=[],
        total_issues_found=0,
        signup_required=True,
        message="Analysis started. Connect to progress endpoint for real-time updates."
    )

@router.post("", response_model=AnalysisRunResponse)
async def analyze_authenticated(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start full analysis for authenticated users.
    Checks scan limits based on plan.
    """
    # Check scan limits
    if current_user.plan.value == "free" and current_user.scans_used >= current_user.scans_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Monthly scan limit reached ({current_user.scans_limit} scans). Upgrade to Professional plan for unlimited scans."
        )

    url = str(request.url)
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    # Check if website exists or create new one
    result = await db.execute(
        select(Website).where(
            and_(
                Website.domain == domain,
                Website.user_id == current_user.id
            )
        )
    )
    website = result.scalar_one_or_none()

    if not website:
        website = Website(
            url=url,
            domain=domain,
            user_id=current_user.id,
            created_at=datetime.utcnow()
        )
        db.add(website)
        await db.commit()
        await db.refresh(website)

    # Create analysis run
    analysis_run = AnalysisRun(
        website_id=website.id,
        user_id=current_user.id,
        status=AnalysisStatus.pending,
        progress=0,
        started_at=datetime.utcnow()
    )
    db.add(analysis_run)

    # Increment user's scan count
    current_user.scans_used += 1
    await db.commit()
    await db.refresh(analysis_run)

    # Start analysis with Celery
    task_result = analyze_website_task.delay(url, str(analysis_run.id), str(current_user.id))

    # Return initial response
    return AnalysisRunResponse(
        id=analysis_run.id,
        website_id=website.id,
        url=url,
        domain=domain,
        status=analysis_run.status,
        overall_score=None,
        progress=0,
        started_at=analysis_run.started_at,
        completed_at=None,
        total_checks_run=0,
        total_issues_found=0,
        results=[]
    )

@router.get("/{analysis_id}/progress")
async def get_analysis_progress(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Server-Sent Events endpoint for real-time analysis progress.
    Streams updates as analysis progresses.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for analysis progress"""
        last_progress = 0
        last_status = None

        while True:
            # Get current analysis state
            analysis = await db.get(AnalysisRun, analysis_id)
            if not analysis:
                yield f"data: {json.dumps({'error': 'Analysis not found'})}\n\n"
                break

            # Check if progress changed
            if analysis.progress != last_progress or analysis.status != last_status:
                # Get partial results
                result = await db.execute(
                    select(AnalysisResult)
                    .where(AnalysisResult.analysis_run_id == analysis_id)
                    .limit(10)  # Send latest 10 results
                )
                results = result.scalars().all()

                # Prepare progress update
                update = {
                    "analysis_id": str(analysis_id),
                    "status": analysis.status.value,
                    "progress": analysis.progress,
                    "overall_score": analysis.overall_score,
                    "partial_results": [
                        {
                            "check_name": r.check_name,
                            "status": r.status.value,
                            "score": r.score,
                            "category": r.check_category.value
                        }
                        for r in results
                    ]
                }

                # Send SSE event
                yield f"event: progress\ndata: {json.dumps(update)}\n\n"

                last_progress = analysis.progress
                last_status = analysis.status

                # Check if analysis is complete
                if analysis.status in [AnalysisStatus.complete, AnalysisStatus.failed]:
                    yield f"event: complete\ndata: {json.dumps({'analysis_id': str(analysis_id), 'status': analysis.status.value})}\n\n"
                    break

            # Wait before next check
            await asyncio.sleep(2)
            await db.commit()  # Refresh session

    return EventSourceResponse(event_generator())

@router.get("/{analysis_id}/preview", response_model=FreeAnalysisResponse)
async def get_analysis_preview(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get limited analysis results for free users.
    Shows only 3 critical issues to encourage signup.
    """
    # Get analysis run
    analysis = await db.get(AnalysisRun, analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # Get website
    website = await db.get(Website, analysis.website_id)

    # Get top 3 critical issues
    result = await db.execute(
        select(AnalysisResult)
        .where(AnalysisResult.analysis_run_id == analysis_id)
        .where(AnalysisResult.status != CheckStatus.pass_check)
        .order_by(AnalysisResult.impact_level.asc())  # Critical first
        .limit(3)
    )
    preview_results = result.scalars().all()

    # Convert to response schema
    preview_results_schema = [
        AnalysisResultSchema(
            id=r.id,
            check_category=r.check_category,
            check_name=r.check_name,
            status=r.status,
            score=r.score,
            details=r.details,
            recommendations=r.recommendations,
            impact_level=r.impact_level,
            fix_difficulty=r.fix_difficulty,
            fix_time_estimate=r.fix_time_estimate
        )
        for r in preview_results
    ]

    return FreeAnalysisResponse(
        id=analysis.id,
        url=website.url,
        status=analysis.status,
        progress=analysis.progress,
        preview_results=preview_results_schema,
        total_issues_found=analysis.total_issues_found or 0,
        signup_required=True,
        message=f"Found {analysis.total_issues_found} issues. Sign up to see all recommendations and fixes."
    )

@router.get("", response_model=List[AnalysisRunResponse])
async def list_user_analyses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """List all analyses for the authenticated user"""
    result = await db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.user_id == current_user.id)
        .order_by(AnalysisRun.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    analyses = result.scalars().all()

    responses = []
    for analysis in analyses:
        website = await db.get(Website, analysis.website_id)

        # Get results if analysis is complete
        results = []
        if analysis.status == AnalysisStatus.complete:
            result = await db.execute(
                select(AnalysisResult)
                .where(AnalysisResult.analysis_run_id == analysis.id)
            )
            analysis_results = result.scalars().all()
            results = [
                AnalysisResultSchema(
                    id=r.id,
                    check_category=r.check_category,
                    check_name=r.check_name,
                    status=r.status,
                    score=r.score,
                    details=r.details,
                    recommendations=r.recommendations,
                    impact_level=r.impact_level,
                    fix_difficulty=r.fix_difficulty,
                    fix_time_estimate=r.fix_time_estimate
                )
                for r in analysis_results
            ]

        responses.append(
            AnalysisRunResponse(
                id=analysis.id,
                website_id=website.id,
                url=website.url,
                domain=website.domain,
                status=analysis.status,
                overall_score=analysis.overall_score,
                progress=analysis.progress,
                started_at=analysis.started_at,
                completed_at=analysis.completed_at,
                total_checks_run=analysis.total_checks_run or 0,
                total_issues_found=analysis.total_issues_found or 0,
                chatgpt_score=analysis.chatgpt_score,
                perplexity_score=analysis.perplexity_score,
                claude_score=analysis.claude_score,
                google_ai_score=analysis.google_ai_score,
                bing_chat_score=analysis.bing_chat_score,
                results=results
            )
        )

    return responses

@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an analysis (only owner can delete)"""
    # Get analysis
    analysis = await db.get(AnalysisRun, analysis_id)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    if analysis.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own analyses"
        )

    await db.delete(analysis)
    await db.commit()

    return {"message": "Analysis deleted successfully"}
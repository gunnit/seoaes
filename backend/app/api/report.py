from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Website, AnalysisRun, AnalysisResult, AnalysisStatus
from app.schemas.schemas import (
    ReportResponse, RecommendationSchema, ScoreBreakdown,
    AIEngineCompatibility, AnalysisRunResponse, AnalysisResultSchema
)
from typing import List
from uuid import UUID
from datetime import datetime
import os
import tempfile
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas

router = APIRouter(prefix="/api/report", tags=["Reports"])

@router.get("/{analysis_id}", response_model=ReportResponse)
async def get_full_report(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete analysis report with all checks, scores, and recommendations.
    Only available for authenticated users.
    """
    # Get analysis run
    analysis = await db.get(AnalysisRun, analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # Check ownership for non-free analyses
    if analysis.user_id and analysis.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own analysis reports"
        )

    # Get website
    website = await db.get(Website, analysis.website_id)

    # Get all analysis results
    result = await db.execute(
        select(AnalysisResult)
        .where(AnalysisResult.analysis_run_id == analysis_id)
        .order_by(AnalysisResult.impact_level.asc())  # Critical issues first
    )
    all_results = result.scalars().all()

    # Convert to response schemas
    results_schema = [
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
        for r in all_results
    ]

    # Calculate score breakdown
    score_breakdown = calculate_score_breakdown(all_results)

    # Get AI engine compatibility
    ai_compatibility = AIEngineCompatibility(
        chatgpt=analysis.chatgpt_score or 0,
        perplexity=analysis.perplexity_score or 0,
        claude=analysis.claude_score or 0,
        google_ai=analysis.google_ai_score or 0,
        bing_chat=analysis.bing_chat_score or 0
    )

    # Generate recommendations
    recommendations = generate_recommendations(all_results)

    # Get critical issues
    critical_issues = [r for r in results_schema if r.impact_level.value == "critical"]

    # Prepare analysis response
    analysis_response = AnalysisRunResponse(
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
        results=results_schema
    )

    return ReportResponse(
        analysis=analysis_response,
        score_breakdown=score_breakdown,
        ai_engine_compatibility=ai_compatibility,
        recommendations=recommendations,
        critical_issues=critical_issues,
        export_url=f"/api/report/{analysis_id}/export"
    )

def calculate_score_breakdown(results: List[AnalysisResult]) -> ScoreBreakdown:
    """Calculate weighted score breakdown by category"""
    category_scores = {
        "ai_readiness": [],
        "content": [],
        "structure": [],
        "technical": []
    }

    for result in results:
        category = result.check_category.value
        if category in category_scores:
            category_scores[category].append(result.score)

    # Calculate averages and apply weights
    ai_access_score = sum(category_scores["ai_readiness"]) / len(category_scores["ai_readiness"]) if category_scores["ai_readiness"] else 100
    content_score = sum(category_scores["content"]) / len(category_scores["content"]) if category_scores["content"] else 100
    structure_score = sum(category_scores["structure"]) / len(category_scores["structure"]) if category_scores["structure"] else 100
    technical_score = sum(category_scores["technical"]) / len(category_scores["technical"]) if category_scores["technical"] else 100

    return ScoreBreakdown(
        ai_access=int(ai_access_score * 0.4),  # 40% weight
        content_quality=int(content_score * 0.35),  # 35% weight
        structural_optimization=int(structure_score * 0.15),  # 15% weight
        technical_performance=int(technical_score * 0.10)  # 10% weight
    )

def generate_recommendations(results: List[AnalysisResult]) -> List[RecommendationSchema]:
    """Generate actionable recommendations from analysis results"""
    recommendations = []

    for result in results:
        # Skip passed checks
        if result.status.value == "pass":
            continue

        # Generate recommendation based on the issue
        if result.recommendations:
            impact_points = {
                "critical": "+30-40 points",
                "high": "+20-30 points",
                "medium": "+10-20 points",
                "low": "+5-10 points"
            }

            effort_time = {
                "easy": result.fix_time_estimate or "5 minutes",
                "medium": result.fix_time_estimate or "30 minutes",
                "hard": result.fix_time_estimate or "2 hours"
            }

            # Parse instructions from recommendations text
            instructions = result.recommendations.split("\n")
            if len(instructions) == 1:
                instructions = [
                    f"1. Identify the issue: {result.check_name}",
                    f"2. {result.recommendations}",
                    "3. Test the changes",
                    "4. Monitor improvements"
                ]

            recommendation = RecommendationSchema(
                title=result.check_name,
                priority=result.impact_level,
                impact=impact_points.get(result.impact_level.value, "+10 points"),
                effort=effort_time.get(result.fix_difficulty.value, "30 minutes"),
                category=result.check_category,
                instructions=instructions[:10],  # Limit to 10 steps
                why_it_matters=f"This issue affects your {result.check_category.value} score",
                expected_outcome=f"Fixing this will improve your overall score by {impact_points.get(result.impact_level.value, '+10 points')}"
            )

            recommendations.append(recommendation)

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    recommendations.sort(key=lambda x: priority_order.get(x.priority.value, 4))

    return recommendations[:20]  # Return top 20 recommendations

@router.post("/{analysis_id}/export")
async def export_report_pdf(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate and download PDF report.
    Creates a professional PDF with all analysis results and recommendations.
    """
    # Get full report data
    report = await get_full_report(analysis_id, current_user, db)

    # Create temporary PDF file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        pdf_path = tmp_file.name

        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Container for PDF elements
        story = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=12,
            spaceBefore=12
        )

        # Title Page
        story.append(Paragraph("AI Visibility Analysis Report", title_style))
        story.append(Spacer(1, 20))

        # Website info
        story.append(Paragraph(f"<b>Website:</b> {report.analysis.url}", styles['Normal']))
        story.append(Paragraph(f"<b>Analysis Date:</b> {report.analysis.started_at.strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Paragraph(f"<b>Overall Score:</b> {report.analysis.overall_score}/100", styles['Normal']))
        story.append(Spacer(1, 30))

        # Score Breakdown Section
        story.append(Paragraph("Score Breakdown", heading_style))

        score_data = [
            ["Category", "Score", "Weight", "Weighted Score"],
            ["AI Access & Crawlability", f"{report.score_breakdown.ai_access}/40", "40%", f"{report.score_breakdown.ai_access}"],
            ["Content Quality", f"{report.score_breakdown.content_quality}/35", "35%", f"{report.score_breakdown.content_quality}"],
            ["Structural Optimization", f"{report.score_breakdown.structural_optimization}/15", "15%", f"{report.score_breakdown.structural_optimization}"],
            ["Technical Performance", f"{report.score_breakdown.technical_performance}/10", "10%", f"{report.score_breakdown.technical_performance}"],
        ]

        score_table = Table(score_data, colWidths=[3*inch, 1.5*inch, 1*inch, 1.5*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        story.append(score_table)
        story.append(Spacer(1, 30))

        # AI Engine Compatibility
        story.append(Paragraph("AI Engine Compatibility", heading_style))

        ai_data = [
            ["AI Engine", "Compatibility Score", "Status"],
            ["ChatGPT", f"{report.ai_engine_compatibility.chatgpt}%", get_status_text(report.ai_engine_compatibility.chatgpt)],
            ["Perplexity", f"{report.ai_engine_compatibility.perplexity}%", get_status_text(report.ai_engine_compatibility.perplexity)],
            ["Claude", f"{report.ai_engine_compatibility.claude}%", get_status_text(report.ai_engine_compatibility.claude)],
            ["Google AI", f"{report.ai_engine_compatibility.google_ai}%", get_status_text(report.ai_engine_compatibility.google_ai)],
            ["Bing Chat", f"{report.ai_engine_compatibility.bing_chat}%", get_status_text(report.ai_engine_compatibility.bing_chat)],
        ]

        ai_table = Table(ai_data, colWidths=[2*inch, 2*inch, 2*inch])
        ai_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        story.append(ai_table)
        story.append(PageBreak())

        # Critical Issues
        if report.critical_issues:
            story.append(Paragraph("Critical Issues", heading_style))
            for issue in report.critical_issues[:5]:
                story.append(Paragraph(f"<b>• {issue.check_name}</b>", styles['Normal']))
                if issue.recommendations:
                    story.append(Paragraph(f"  Fix: {issue.recommendations[:200]}...", styles['Normal']))
                story.append(Spacer(1, 10))
            story.append(Spacer(1, 20))

        # Top Recommendations
        story.append(Paragraph("Priority Recommendations", heading_style))
        for i, rec in enumerate(report.recommendations[:10], 1):
            story.append(Paragraph(f"<b>{i}. {rec.title}</b>", styles['Normal']))
            story.append(Paragraph(f"   Priority: {rec.priority.value.upper()}", styles['Normal']))
            story.append(Paragraph(f"   Impact: {rec.impact}", styles['Normal']))
            story.append(Paragraph(f"   Effort: {rec.effort}", styles['Normal']))
            story.append(Paragraph(f"   Why: {rec.why_it_matters}", styles['Normal']))
            story.append(Spacer(1, 15))

        # Build PDF
        doc.build(story)

    # Return PDF file
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"ai-visibility-report-{analysis_id}.pdf"
    )

def get_status_text(score: int) -> str:
    """Get status text based on score"""
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Needs Work"
    else:
        return "Critical"
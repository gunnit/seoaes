from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

# Enums
class PlanType(str, Enum):
    free = "free"
    professional = "professional"
    agency = "agency"

class AnalysisStatus(str, Enum):
    pending = "pending"
    analyzing = "analyzing"
    complete = "complete"
    failed = "failed"

class CheckCategory(str, Enum):
    technical = "technical"
    structure = "structure"
    content = "content"
    ai_readiness = "ai_readiness"

class CheckStatus(str, Enum):
    pass_check = "pass"
    warn = "warn"
    fail = "fail"

class ImpactLevel(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class FixDifficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

# User Schemas
class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    plan: PlanType
    scans_used: int
    scans_limit: int
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

# Analysis Schemas
class AnalysisRequest(BaseModel):
    url: HttpUrl
    depth: Optional[int] = 1

    @field_validator('url')
    def validate_url(cls, v):
        return str(v)

class AnalysisProgressUpdate(BaseModel):
    analysis_id: UUID
    status: AnalysisStatus
    progress: int
    message: Optional[str] = None
    partial_results: Optional[List[Dict[str, Any]]] = None

class AnalysisResultSchema(BaseModel):
    id: UUID
    check_category: CheckCategory
    check_name: str
    status: CheckStatus
    score: int
    details: Optional[Dict[str, Any]] = None
    recommendations: Optional[str] = None
    impact_level: ImpactLevel
    fix_difficulty: FixDifficulty
    fix_time_estimate: Optional[str] = None

    class Config:
        from_attributes = True

class AnalysisRunResponse(BaseModel):
    id: UUID
    website_id: UUID
    url: str
    domain: str
    status: AnalysisStatus
    overall_score: Optional[int] = None
    progress: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_checks_run: int
    total_issues_found: int
    chatgpt_score: Optional[int] = None
    perplexity_score: Optional[int] = None
    claude_score: Optional[int] = None
    google_ai_score: Optional[int] = None
    bing_chat_score: Optional[int] = None
    results: Optional[List[AnalysisResultSchema]] = None

    class Config:
        from_attributes = True

class FreeAnalysisResponse(BaseModel):
    id: UUID
    url: str
    status: AnalysisStatus
    progress: int
    preview_results: List[AnalysisResultSchema]  # Limited to 3 issues
    total_issues_found: int
    signup_required: bool = True
    message: str = "Sign up to see all issues and recommendations"

# Recommendation Schemas
class RecommendationSchema(BaseModel):
    title: str
    priority: ImpactLevel
    impact: str  # e.g., "+30-40 points"
    effort: str  # e.g., "5 minutes"
    category: CheckCategory
    instructions: List[str]
    why_it_matters: str
    expected_outcome: str

# Report Schemas
class ReportRequest(BaseModel):
    analysis_id: UUID

class ScoreBreakdown(BaseModel):
    ai_access: int  # 0-40
    content_quality: int  # 0-35
    structural_optimization: int  # 0-15
    technical_performance: int  # 0-10

class AIEngineCompatibility(BaseModel):
    chatgpt: int
    perplexity: int
    claude: int
    google_ai: int
    bing_chat: int

class ReportResponse(BaseModel):
    analysis: AnalysisRunResponse
    score_breakdown: ScoreBreakdown
    ai_engine_compatibility: AIEngineCompatibility
    recommendations: List[RecommendationSchema]
    critical_issues: List[AnalysisResultSchema]
    export_url: Optional[str] = None

# Payment Schemas
class SubscriptionPlan(BaseModel):
    name: PlanType
    price: int
    scans_per_month: Optional[int] = None  # None means unlimited
    page_depth: int
    features: List[str]

class CreateSubscriptionRequest(BaseModel):
    plan: PlanType

class SubscriptionResponse(BaseModel):
    subscription_id: str
    plan: PlanType
    status: str
    next_billing_date: datetime

# Website Schemas
class WebsiteResponse(BaseModel):
    id: UUID
    url: str
    domain: str
    last_analysis_score: Optional[int] = None
    last_analysis_date: Optional[datetime] = None
    total_analyses: int = 0

    class Config:
        from_attributes = True

# SSE Event Schema
class SSEEvent(BaseModel):
    event: str
    data: Dict[str, Any]
    id: Optional[str] = None
    retry: Optional[int] = None
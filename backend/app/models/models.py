from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Enum, Boolean, JSON, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class PlanType(enum.Enum):
    free = "free"
    professional = "professional"
    agency = "agency"

class AnalysisStatus(enum.Enum):
    pending = "pending"
    analyzing = "analyzing"
    complete = "complete"
    failed = "failed"

class CheckCategory(enum.Enum):
    technical = "technical"
    structure = "structure"
    content = "content"
    ai_readiness = "ai_readiness"

class CheckStatus(enum.Enum):
    pass_check = "pass"
    warn = "warn"
    fail = "fail"

class ImpactLevel(enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class FixDifficulty(enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    plan = Column(Enum(PlanType), default=PlanType.free, nullable=False)
    scans_used = Column(Integer, default=0, nullable=False)
    scans_limit = Column(Integer, default=10, nullable=False)
    paypal_subscription_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    websites = relationship("Website", back_populates="user", cascade="all, delete-orphan")
    analysis_runs = relationship("AnalysisRun", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"

class Website(Base):
    __tablename__ = "websites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    url = Column(Text, nullable=False)
    domain = Column(Text, nullable=False, index=True)
    last_analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_runs.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="websites")
    analysis_runs = relationship("AnalysisRun", back_populates="website", foreign_keys="AnalysisRun.website_id")
    last_analysis = relationship("AnalysisRun", foreign_keys=[last_analysis_id], post_update=True)

    def __repr__(self):
        return f"<Website {self.domain}>"

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    website_id = Column(UUID(as_uuid=True), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.pending, nullable=False)
    overall_score = Column(Integer, nullable=True)
    progress = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    crawled_content = Column(Text, nullable=True)  # Stores markdown
    total_checks_run = Column(Integer, default=0)
    total_issues_found = Column(Integer, default=0)

    # AI Engine Scores
    chatgpt_score = Column(Integer, nullable=True)
    perplexity_score = Column(Integer, nullable=True)
    claude_score = Column(Integer, nullable=True)
    google_ai_score = Column(Integer, nullable=True)
    bing_chat_score = Column(Integer, nullable=True)

    # Relationships
    website = relationship("Website", back_populates="analysis_runs", foreign_keys=[website_id])
    user = relationship("User", back_populates="analysis_runs")
    results = relationship("AnalysisResult", back_populates="analysis_run", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_analysis_runs_website_created', 'website_id', 'started_at'),
        Index('idx_analysis_runs_user_created', 'user_id', 'started_at'),
    )

    def __repr__(self):
        return f"<AnalysisRun {self.id} - {self.status.value}>"

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_run_id = Column(UUID(as_uuid=True), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    check_category = Column(Enum(CheckCategory), nullable=False)
    check_name = Column(String(100), nullable=False)
    status = Column(Enum(CheckStatus), nullable=False)
    score = Column(Integer, nullable=False)  # 0-100
    details = Column(JSON, nullable=True)
    recommendations = Column(Text, nullable=True)
    impact_level = Column(Enum(ImpactLevel), nullable=False)
    fix_difficulty = Column(Enum(FixDifficulty), nullable=False)
    fix_time_estimate = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="results")

    def __repr__(self):
        return f"<AnalysisResult {self.check_name} - {self.status.value}>"

class AnalysisCache(Base):
    __tablename__ = "analysis_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url_hash = Column(String(64), nullable=False, index=True)
    check_type = Column(String(100), nullable=False)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint('url_hash', 'check_type', name='uq_url_check'),
        Index('idx_cache_expires', 'expires_at'),
    )

    def __repr__(self):
        return f"<AnalysisCache {self.url_hash} - {self.check_type}>"
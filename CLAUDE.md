# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AIVisibility.pro is a SaaS platform that analyzes websites for AI search visibility. It performs 50+ technical checks across 4 progressive analysis stages (0-60 seconds) to determine why websites don't appear in AI search results from ChatGPT, Perplexity, Claude, and other LLMs.

## Deployment Instructions

**IMPORTANT**: Always work on Render.com for deployment. Never deploy, install, or test locally. All deployments must be done through Render.com services.

### Render Services
- **Frontend**: https://aivisibility.onrender.com (srv-d39d2bggjchc73dlsqug)
- **Backend API**: https://aivisibility-backend.onrender.com (srv-d39d28uuk2gs73fpbn6g)
- **Database**: PostgreSQL on Render (dpg-d39cvvogjchc73dlraq0-a)
- **Redis**: Cache service on Render (red-d39d08je5dus73aqbg7g)

## Key Commands

### Frontend Development
```bash
cd frontend
npm run dev      # Development server (port 3000)
npm run build    # Production build
npm run lint     # Run ESLint
npm start        # Production server
```

### Backend Development
```bash
cd backend
uvicorn main:app --reload                    # Development server (port 8000)
uvicorn main:app --host 0.0.0.0 --port $PORT # Production server
playwright install chromium                    # Install browser for scraping
celery -A app.workers.celery_app worker      # Start Celery worker
```

### Database Operations
```bash
# Alembic migrations (from backend directory)
alembic init alembic                  # Initialize migrations
alembic revision --autogenerate -m "message"  # Create migration
alembic upgrade head                   # Apply migrations
```

## Architecture & Core Components

### Backend Architecture

**FastAPI Application Structure**:
- `main.py` - Application entry point with lifespan management
- `app/api/` - API routers (auth, analyze, report)
- `app/services/analyzer.py` - Core analysis engine implementing 4-stage progressive analysis
- `app/workers/` - Celery tasks for background processing
- `app/core/database.py` - AsyncPG database configuration with SSL handling for Render

**Database Connection Handling**:
The backend uses asyncpg with SQLAlchemy. The database URL must be converted from `postgresql://` to `postgresql+asyncpg://` format. SSL is handled via context for Render.com PostgreSQL.

**Progressive Analysis Pipeline**:
1. Instant checks (0-5s): robots.txt, SSL, headings
2. Technical analysis (5-15s): speed, mobile, schema
3. Content analysis (15-30s): structure, E-E-A-T
4. AI analysis (30-60s): GPT-4 evaluation

### Frontend Architecture

**Next.js 14 App Directory Structure**:
- `app/page.tsx` - Landing page with analysis form
- `app/analyze/[id]/page.tsx` - Analysis results page
- `components/AnalysisProgress.tsx` - Real-time SSE progress updates
- `lib/api.ts` - API client with axios

**Real-time Updates**:
Uses Server-Sent Events (SSE) for streaming analysis progress from `/api/analyze/{id}/progress` endpoint.

## Critical Configuration

### Database URL Format
When setting DATABASE_URL on Render, use the plain PostgreSQL format:
```
postgresql://user:password@host/database
```
The application automatically converts this to asyncpg format.

### Required Environment Variables
```env
DATABASE_URL        # PostgreSQL connection (auto-provided by Render)
REDIS_URL          # Redis connection (auto-provided by Render)
JWT_SECRET         # Authentication secret
OPENAI_API_KEY     # GPT-4 API access
FIRECRAWL_API_KEY  # Web scraping service
PAYPAL_CLIENT_ID   # Payment processing
PAYPAL_CLIENT_SECRET
```

### API Integration Points

**OpenAI GPT-4**: Used in `app/services/ai_analysis.py` for content evaluation
**Firecrawl**: Primary web scraping in `app/services/crawler.py`
**Playwright**: Fallback scraping for JS-heavy sites

## Analysis Scoring System

The overall score is calculated with weighted components:
- AI Access: 40% (robots.txt checks for 15 AI bots)
- Content Quality: 35% (structure, E-E-A-T, direct answers)
- Technical SEO: 15% (schema, meta tags, performance)
- Site Structure: 10% (navigation, internal linking)

## Deployment Process

1. Push changes to GitHub main branch
2. Render auto-deploys from GitHub webhook
3. Backend builds with: `pip install -r requirements.txt && playwright install chromium`
4. Frontend builds with: `npm install && npm run build`

## Known Issues & Solutions

**AsyncPG Connection Errors**: Ensure DATABASE_URL doesn't include `?sslmode=` parameter
**Frontend CSS Build Errors**: Use `.mjs` extension for PostCSS/Tailwind configs
**Python Version**: Must specify exact version (e.g., "3.11.0" not "3.11")

## User Tiers & Limits

- **Free**: 10 scans/month, 1 page depth, `/api/analyze/free` endpoint
- **Professional ($397)**: Unlimited scans, 50 pages, full API access
- **Agency ($1,497)**: White-label, 100 pages, priority queue
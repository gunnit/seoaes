# AIVisibility Services Architecture

## Current Services on Render

### Active Services

1. **aivisibility-backend** (srv-d39d28uuk2gs73fpbn6g)
   - Main FastAPI backend
   - Handles API requests
   - **INCLUDES integrated background worker** for processing analyses
   - Status: ✅ Running

2. **aivisibility** (srv-d39d2bggjchc73dlsqug)
   - Next.js frontend
   - User interface
   - Status: ✅ Running

3. **aivisibility-db** (PostgreSQL)
   - Database for storing analysis data
   - Status: ✅ Running

4. **Redis** (Cache)
   - Used as message queue for background tasks
   - Status: ✅ Running

### Deprecated/Unused Services

1. **aivisibility-worker** (srv-d39njp8dl3ps73acljn0)
   - Original Celery worker (failing to build)
   - **REPLACED BY**: Integrated background worker in backend
   - Status: ❌ Build failing - can be suspended

2. **aivisibility-beat** (srv-d39nk4be5dus73bjvm00)
   - Celery Beat scheduler
   - No periodic tasks defined
   - Status: ⚠️ Running but unused - can be suspended

## Architecture Decision

### Original Design (Not Working)
- Separate Celery worker service with Playwright
- Celery Beat for scheduling
- Complex dependency management

### Current Design (Working)
- **Simplified background worker** integrated into backend service
- Uses threading to process tasks without blocking API
- Processes tasks from Redis queue
- No complex dependencies (no Playwright, minimal requirements)

### Benefits of Current Design
1. Fewer services to manage
2. Simpler deployment
3. Lower costs (fewer Render services)
4. Easier debugging (all logs in one place)
5. No dependency conflicts

## Task Processing Flow

1. User submits URL for analysis
2. Backend creates analysis record in database
3. Task is pushed to Redis queue
4. Background worker thread picks up task
5. Worker simulates analysis stages with progress updates
6. Results are written to database
7. Frontend polls for updates via SSE

## Recommendations

1. **Suspend** the `aivisibility-beat` service - not needed
2. **Suspend** the `aivisibility-worker` service - replaced by integrated worker
3. Keep the simplified architecture unless you need:
   - Heavy CPU-intensive processing
   - True parallel processing across multiple machines
   - Scheduled/periodic tasks
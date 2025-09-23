# AIVisibility.pro - LLM Optimization SaaS Platform

A comprehensive SaaS platform that analyzes websites for AI search visibility and provides actionable recommendations to improve discoverability in ChatGPT, Perplexity, Claude, and other AI search engines.

## Features

### Core Analysis Capabilities
- **AI Bot Access Check**: Verifies if 15+ AI crawlers can access your site
- **50+ Technical Checks**: Comprehensive analysis across 4 dimensions
- **Progressive Analysis**: Results stream in real-time (10-second first insight)
- **Multi-LLM Scoring**: Compatibility scores for ChatGPT, Perplexity, Claude, Google AI, and Bing Chat
- **Actionable Recommendations**: Specific, step-by-step fixes for every issue

### Analysis Stages
1. **Instant Checks (0-5s)**: robots.txt, llms.txt, SSL, headings
2. **Technical Analysis (5-15s)**: Page speed, mobile, schema, sitemap
3. **Content Analysis (15-30s)**: Structure, E-E-A-T, direct answers
4. **AI Analysis (30-60s)**: GPT-4 powered content evaluation

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **SQLAlchemy** - ORM
- **Celery + Redis** - Background task processing
- **Playwright** - Web scraping
- **OpenAI API** - AI-powered analysis
- **JWT** - Authentication

### Frontend
- **Next.js 14** - React framework
- **Tailwind CSS** - Styling
- **React Query** - Data fetching
- **Framer Motion** - Animations
- **Server-Sent Events** - Real-time updates

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/llm-optimization-saas.git
cd llm-optimization-saas
```

2. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Start with Docker Compose:
```bash
docker-compose up
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup (Without Docker)

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

#### Start Celery Workers
```bash
celery -A app.workers.celery_app worker --loglevel=info
```

## Deployment

### Deploy to Render

1. Fork this repository
2. Connect your GitHub account to Render
3. Create a new Blueprint:
   - Go to Render Dashboard
   - Click "Blueprints" → "New Blueprint"
   - Connect your forked repo
   - Select the `render.yaml` file

4. Set environment variables in Render:
   - `OPENAI_API_KEY`
   - `FIRECRAWL_API_KEY`
   - `PAYPAL_CLIENT_ID`
   - `PAYPAL_CLIENT_SECRET`

5. Deploy the blueprint

The services will be automatically created:
- Web service (backend API)
- Web service (frontend)
- Background workers (Celery)
- PostgreSQL database
- Redis instance

## API Endpoints

### Public Endpoints
- `POST /api/analyze/free` - Start free analysis (no auth)
- `GET /api/analyze/{id}/progress` - Real-time progress (SSE)
- `GET /api/analyze/{id}/preview` - Limited results

### Authentication
- `POST /api/auth/signup` - Create account
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token

### Protected Endpoints
- `POST /api/analyze` - Full analysis
- `GET /api/report/{id}` - Complete report
- `POST /api/report/{id}/export` - PDF export

## Project Structure

```
llm-optimization-saas/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core configuration
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── workers/      # Celery tasks
│   └── main.py
├── frontend/
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   └── lib/              # Utilities
├── docker-compose.yml
├── render.yaml           # Render deployment
└── README.md
```

## Pricing Tiers

- **Free**: 10 scans/month, 1 page depth
- **Professional ($397/mo)**: Unlimited scans, 50 pages
- **Agency ($1,497/mo)**: White-label, 100 pages

## Environment Variables

Required environment variables:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET=your-secret-key

# APIs
OPENAI_API_KEY=sk-...
FIRECRAWL_API_KEY=fc-...
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...

# URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is proprietary software. All rights reserved.

## Support

For support, email support@aivisibility.pro
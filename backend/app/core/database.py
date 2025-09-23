from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings
import re

# Convert sync DATABASE_URL to async and handle SSL
DATABASE_URL = settings.DATABASE_URL

# Remove any existing driver specification
if DATABASE_URL.startswith("postgresql+"):
    DATABASE_URL = re.sub(r"^postgresql\+[^:]+://", "postgresql://", DATABASE_URL)

# Convert to asyncpg
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Remove sslmode parameter if present (asyncpg doesn't support it in the URL)
DATABASE_URL = re.sub(r'[?&]sslmode=[^&]*', '', DATABASE_URL)

# For Render.com PostgreSQL, we need to add SSL context
connect_args = {}
if "render.com" in DATABASE_URL:
    import ssl
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args = {"ssl": ssl_context}

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
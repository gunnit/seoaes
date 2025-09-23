from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings
import re

# Convert sync DATABASE_URL to async and handle SSL
DATABASE_URL = settings.DATABASE_URL

# Debug print
print(f"Original DATABASE_URL: {DATABASE_URL}")

# Ensure we're using asyncpg driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif not DATABASE_URL.startswith("postgresql+asyncpg://"):
    # If it has another driver, replace it
    DATABASE_URL = re.sub(r"^postgresql\+[^:]+://", "postgresql+asyncpg://", DATABASE_URL)

print(f"Modified DATABASE_URL: {DATABASE_URL}")

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
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Load environment variables
load_dotenv()

# Retrieve database URL from environment variable, falling back to local PostgreSQL URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://admin:secret_vault_password_2026@localhost:5432/streamsync_prod"
)

# Ensure the scheme is postgresql+asyncpg for the async engine
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine with pool_size=20 and max_overflow=10
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10
)

# Create async sessionmaker
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Helper async generator dependency function
async def get_async_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

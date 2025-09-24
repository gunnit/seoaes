#!/usr/bin/env python3
"""
Database initialization script for AI Visibility backend.
This script ensures the database is properly initialized with correct enum types.

Usage:
    python init_database.py

This should be run on deployment to ensure database schema is correct.
"""

import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, inspect
import re
import ssl
from app.models.models import Base
from app.core.config import settings


async def init_database():
    """Initialize database with proper schema and enum types"""

    # Get database URL
    DATABASE_URL = settings.DATABASE_URL

    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not configured")
        sys.exit(1)

    print(f"Connecting to database...")

    # Convert to async URL
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

    # Remove sslmode parameter if present
    DATABASE_URL = re.sub(r'[?&]sslmode=[^&]*', '', DATABASE_URL)

    # Setup SSL for Render.com
    connect_args = {}
    if "render.com" in DATABASE_URL:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connect_args = {"ssl": ssl_context}

    # Create engine
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        connect_args=connect_args
    )

    try:
        async with engine.begin() as conn:
            print("\n🔍 Checking existing database state...")

            # Check if tables exist
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE';
            """))

            existing_tables = [row[0] for row in result]
            print(f"Existing tables: {existing_tables}")

            # Check if checkstatus enum exists and has correct values
            result = await conn.execute(text("""
                SELECT typname
                FROM pg_type
                WHERE typname = 'checkstatus';
            """))

            if result.rowcount > 0:
                # Enum exists, check its values
                result = await conn.execute(text("""
                    SELECT enumlabel
                    FROM pg_enum
                    WHERE enumtypid = (
                        SELECT oid FROM pg_type WHERE typname = 'checkstatus'
                    )
                    ORDER BY enumsortorder;
                """))

                current_values = [row[0] for row in result]
                print(f"Current checkstatus enum values: {current_values}")

                # Check if we need to fix the enum
                if 'pass' not in current_values:
                    print("\n⚠️  Enum values need updating...")

                    # Drop and recreate all enum types with correct values
                    print("Recreating enum types with correct values...")

                    # First, drop dependent objects if they exist
                    if 'analysis_results' in existing_tables:
                        await conn.execute(text("""
                            ALTER TABLE analysis_results DROP COLUMN IF EXISTS status;
                        """))

                    # Drop old enums if they exist
                    for enum_name in ['checkstatus', 'checkcategory', 'impactlevel', 'fixdifficulty', 'analysisstatus', 'plantype']:
                        await conn.execute(text(f"""
                            DROP TYPE IF EXISTS {enum_name} CASCADE;
                        """))

            # Create all enum types with correct values
            print("\n📦 Creating enum types...")

            await conn.execute(text("""
                DO $$
                BEGIN
                    -- PlanType enum
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'plantype') THEN
                        CREATE TYPE plantype AS ENUM ('free', 'professional', 'agency');
                    END IF;

                    -- AnalysisStatus enum
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'analysisstatus') THEN
                        CREATE TYPE analysisstatus AS ENUM ('pending', 'analyzing', 'complete', 'failed');
                    END IF;

                    -- CheckCategory enum
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'checkcategory') THEN
                        CREATE TYPE checkcategory AS ENUM ('technical', 'structure', 'content', 'ai_readiness');
                    END IF;

                    -- CheckStatus enum - THIS IS THE CRITICAL ONE
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'checkstatus') THEN
                        CREATE TYPE checkstatus AS ENUM ('pass', 'warn', 'fail');
                    END IF;

                    -- ImpactLevel enum
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'impactlevel') THEN
                        CREATE TYPE impactlevel AS ENUM ('critical', 'high', 'medium', 'low');
                    END IF;

                    -- FixDifficulty enum
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'fixdifficulty') THEN
                        CREATE TYPE fixdifficulty AS ENUM ('easy', 'medium', 'hard');
                    END IF;
                END
                $$;
            """))

            print("✅ Enum types created successfully")

            # Now create tables using SQLAlchemy metadata
            print("\n🏗️  Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully")

            # Verify final state
            print("\n📋 Verifying final database state...")

            # Check tables
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """))

            tables = [row[0] for row in result]
            print(f"Tables: {', '.join(tables)}")

            # Check checkstatus enum values
            result = await conn.execute(text("""
                SELECT enumlabel
                FROM pg_enum
                WHERE enumtypid = (
                    SELECT oid FROM pg_type WHERE typname = 'checkstatus'
                )
                ORDER BY enumsortorder;
            """))

            values = [row[0] for row in result]
            print(f"CheckStatus enum values: {values}")

            # Verify the critical 'pass' value is present
            if 'pass' in values:
                print("\n✅ Database initialized successfully! The 'pass' value is present in checkstatus enum.")
            else:
                print("\n⚠️  Warning: 'pass' value not found in checkstatus enum!")
                return False

            return True

    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        return False
    finally:
        await engine.dispose()


async def test_enum_insert():
    """Test that we can insert all enum values"""

    DATABASE_URL = settings.DATABASE_URL

    # Convert to async URL
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

    DATABASE_URL = re.sub(r'[?&]sslmode=[^&]*', '', DATABASE_URL)

    connect_args = {}
    if "render.com" in DATABASE_URL:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connect_args = {"ssl": ssl_context}

    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args=connect_args
    )

    try:
        async with engine.connect() as conn:
            print("\n🧪 Testing enum value inserts...")

            # Test inserting each CheckStatus value
            for status_value in ['pass', 'warn', 'fail']:
                try:
                    # We'll just test the enum cast, not actual insert
                    result = await conn.execute(text(f"""
                        SELECT '{status_value}'::checkstatus;
                    """))
                    print(f"  ✅ Can use '{status_value}' value")
                except Exception as e:
                    print(f"  ❌ Cannot use '{status_value}' value: {e}")
                    return False

            print("\n✅ All enum values work correctly!")
            return True

    except Exception as e:
        print(f"\n❌ Error testing enum values: {e}")
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("AI Visibility Database Initialization")
    print("=" * 60)

    # Run initialization
    success = asyncio.run(init_database())

    if success:
        # Test enum values
        asyncio.run(test_enum_insert())
        print("\n🎉 Database initialization complete!")
        sys.exit(0)
    else:
        print("\n❌ Database initialization failed!")
        sys.exit(1)
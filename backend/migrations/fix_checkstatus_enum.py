#!/usr/bin/env python3
"""
Migration script to fix CheckStatus enum values in the database.
This script updates the checkstatus enum type to match the Python model values.

Run this script on the Render PostgreSQL database to fix the enum mismatch.
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import re
import ssl


async def fix_checkstatus_enum():
    """Fix the checkstatus enum in the database"""

    # Get database URL from environment or use the Render connection string
    DATABASE_URL = os.environ.get('DATABASE_URL', '')

    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Please set it to your Render PostgreSQL connection string")
        return False

    # Convert to async URL if needed
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

    # Remove sslmode parameter if present (asyncpg doesn't support it in the URL)
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
            # First, check current enum values
            result = await conn.execute(text("""
                SELECT enumlabel
                FROM pg_enum
                WHERE enumtypid = (
                    SELECT oid FROM pg_type WHERE typname = 'checkstatus'
                )
                ORDER BY enumsortorder;
            """))

            current_values = [row[0] for row in result]
            print(f"Current enum values: {current_values}")

            # Check if 'pass' is already in the enum
            if 'pass' in current_values:
                print("'pass' value already exists in checkstatus enum")
                return True

            # Begin transaction to update enum
            # This is a complex operation that requires careful handling

            # Step 1: Create a new temporary enum type with correct values
            print("Creating temporary enum type...")
            await conn.execute(text("""
                CREATE TYPE checkstatus_new AS ENUM ('pass', 'warn', 'fail');
            """))

            # Step 2: Update all columns using the old enum to use the new one
            print("Updating analysis_results table...")

            # First, update any existing values that might be using old enum values
            # We'll map old values to new ones if needed
            await conn.execute(text("""
                ALTER TABLE analysis_results
                ALTER COLUMN status TYPE checkstatus_new
                USING status::text::checkstatus_new;
            """))

            # Step 3: Drop the old enum type
            print("Dropping old enum type...")
            await conn.execute(text("""
                DROP TYPE checkstatus;
            """))

            # Step 4: Rename the new enum type to the original name
            print("Renaming new enum type...")
            await conn.execute(text("""
                ALTER TYPE checkstatus_new RENAME TO checkstatus;
            """))

            print("✅ Successfully updated checkstatus enum!")

            # Verify the update
            result = await conn.execute(text("""
                SELECT enumlabel
                FROM pg_enum
                WHERE enumtypid = (
                    SELECT oid FROM pg_type WHERE typname = 'checkstatus'
                )
                ORDER BY enumsortorder;
            """))

            new_values = [row[0] for row in result]
            print(f"New enum values: {new_values}")

            return True

    except Exception as e:
        print(f"❌ Error updating enum: {e}")

        # Try alternative approach if the above fails
        print("\nTrying alternative approach...")
        try:
            async with engine.begin() as conn:
                # Alternative: Add 'pass' value to existing enum
                await conn.execute(text("""
                    ALTER TYPE checkstatus ADD VALUE IF NOT EXISTS 'pass';
                """))
                print("✅ Added 'pass' value to existing enum")
                return True
        except Exception as e2:
            print(f"❌ Alternative approach also failed: {e2}")
            return False
    finally:
        await engine.dispose()


async def verify_database_state():
    """Verify the current database state"""

    DATABASE_URL = os.environ.get('DATABASE_URL', '')

    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable not set")
        return

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
            # Check if checkstatus type exists
            result = await conn.execute(text("""
                SELECT typname
                FROM pg_type
                WHERE typname = 'checkstatus';
            """))

            if result.rowcount == 0:
                print("❌ checkstatus enum type does not exist!")
                return

            # Get enum values
            result = await conn.execute(text("""
                SELECT enumlabel
                FROM pg_enum
                WHERE enumtypid = (
                    SELECT oid FROM pg_type WHERE typname = 'checkstatus'
                )
                ORDER BY enumsortorder;
            """))

            values = [row[0] for row in result]
            print(f"Current checkstatus enum values: {values}")

            # Check table structure
            result = await conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'analysis_results'
                AND column_name = 'status';
            """))

            for row in result:
                print(f"analysis_results.status column: {row[1]}")

    except Exception as e:
        print(f"Error checking database state: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("CheckStatus Enum Migration Script")
    print("=" * 50)

    # First verify current state
    print("\n📋 Checking current database state...")
    asyncio.run(verify_database_state())

    # Ask for confirmation
    print("\n" + "=" * 50)
    response = input("\n⚠️  This will modify the database enum type. Continue? (yes/no): ")

    if response.lower() == 'yes':
        print("\n🔧 Running migration...")
        success = asyncio.run(fix_checkstatus_enum())

        if success:
            print("\n✅ Migration completed successfully!")
            print("\n📋 Verifying new state...")
            asyncio.run(verify_database_state())
        else:
            print("\n❌ Migration failed. Please check the error messages above.")
    else:
        print("\n❌ Migration cancelled.")
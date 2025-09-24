-- Migration: Fix CheckStatus enum values
-- Issue: The application expects 'pass' but the database might have different values
-- This migration ensures the checkstatus enum has the correct values: 'pass', 'warn', 'fail'

-- Check current enum values
SELECT enumlabel
FROM pg_enum
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'checkstatus')
ORDER BY enumsortorder;

-- Start transaction
BEGIN;

-- Create new enum type with correct values
CREATE TYPE checkstatus_new AS ENUM ('pass', 'warn', 'fail');

-- Update the column to use the new enum type
-- This will map existing values to the new enum
ALTER TABLE analysis_results
ALTER COLUMN status TYPE checkstatus_new
USING status::text::checkstatus_new;

-- Drop the old enum type
DROP TYPE checkstatus CASCADE;

-- Rename the new enum type to the original name
ALTER TYPE checkstatus_new RENAME TO checkstatus;

-- Verify the changes
SELECT enumlabel
FROM pg_enum
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'checkstatus')
ORDER BY enumsortorder;

COMMIT;

-- If the above fails, you can try this simpler approach:
-- ALTER TYPE checkstatus ADD VALUE IF NOT EXISTS 'pass';
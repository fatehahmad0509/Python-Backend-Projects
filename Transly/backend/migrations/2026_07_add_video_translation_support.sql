-- Manual migration: adds video translation support.
--
-- This project has no Alembic / migration runner (see README) -
-- AUTO_CREATE_TABLES only creates tables that don't exist yet, it never
-- alters existing ones. Run this by hand against any environment that
-- already has a `translations` / `daily_usages` table from before this
-- feature was added (fresh databases don't need it - SQLAlchemy will
-- create both tables with these columns already present).
--
-- Safe to run multiple times.

BEGIN;

-- 1. New enum type + column distinguishing image vs video translations.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'media_type_enum') THEN
        CREATE TYPE media_type_enum AS ENUM ('IMAGE', 'VIDEO');
    END IF;
END$$;

ALTER TABLE translations
    ADD COLUMN IF NOT EXISTS media_type media_type_enum NOT NULL DEFAULT 'IMAGE';

-- 2. Separate daily counter for video translations.
ALTER TABLE daily_usages
    ADD COLUMN IF NOT EXISTS video_usage_count INTEGER NOT NULL DEFAULT 0;

COMMIT;

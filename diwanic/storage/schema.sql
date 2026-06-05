-- Schema for Diwanic Poetry Database

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Poets Table (Metadata about authors)
CREATE TABLE IF NOT EXISTS poets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(255) UNIQUE NOT NULL,
    name_ar VARCHAR(255) NOT NULL,
    era VARCHAR(255),
    bio_ar TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Poems Table
CREATE TABLE IF NOT EXISTS poems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    poet_id UUID REFERENCES poets(id) ON DELETE CASCADE,
    title VARCHAR(512) NOT NULL,
    title_searchable VARCHAR(512),
    original_text TEXT NOT NULL,
    searchable_text TEXT NOT NULL,
    meter VARCHAR(128),
    rhyme VARCHAR(128),
    category VARCHAR(255),
    source_url TEXT UNIQUE,
    website VARCHAR(50) DEFAULT 'aldiwan',
    scraped_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Verses Table (Optional - for fine-grained search)
CREATE TABLE IF NOT EXISTS verses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    poem_id UUID REFERENCES poems(id) ON DELETE CASCADE,
    verse_index INTEGER NOT NULL,
    original_text TEXT NOT NULL,
    searchable_text TEXT NOT NULL
);

-- 4. Full Text Search Index (Arabic)
-- We add a generated column for high-speed keyword search
ALTER TABLE poems ADD COLUMN IF NOT EXISTS fts_doc tsvector 
    GENERATED ALWAYS AS (
        to_tsvector('simple', title_searchable || ' ' || searchable_text)
    ) STORED;

CREATE INDEX IF NOT EXISTS idx_poems_fts ON poems USING GIN (fts_doc);
CREATE INDEX IF NOT EXISTS idx_poems_poet_id ON poems(poet_id);
CREATE INDEX IF NOT EXISTS idx_poems_meter ON poems(meter);
CREATE INDEX IF NOT EXISTS idx_poems_category ON poems(category);

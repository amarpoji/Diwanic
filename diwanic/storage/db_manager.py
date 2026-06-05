"""
PostgreSQL / Supabase manager for Diwanic.
Handles data ingestion and relational queries.
"""
import psycopg2
from psycopg2.extras import execute_values
from diwanic.core.config import config
from diwanic.core.logger import get_logger

logger = get_logger(__name__)

class DiwanicDB:
    def __init__(self):
        """Initialize connection to Postgres."""
        if not config.DATABASE_URL:
            logger.error("DATABASE_URL not found in environment!")
            raise ValueError("DATABASE_URL is required")
            
        try:
            self.conn = psycopg2.connect(config.DATABASE_URL)
            self.conn.autocommit = True
            logger.info("✅ Connected to Postgres database.")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def init_schema(self, schema_path: str = None):
        """Execute the SQL schema to create tables."""
        if schema_path is None:
            # Default to schema.sql in the same folder as this file
            from pathlib import Path
            schema_path = Path(__file__).parent / "schema.sql"
            schema_path = str(schema_path)
        
        logger.info(f"Initializing schema from {schema_path}...")
        with open(schema_path, 'r') as f:
            sql = f.read()
            
        with self.conn.cursor() as cur:
            cur.execute(sql)
        logger.info("✅ Schema initialized.")

    def ingest_poem(self, poem_data: dict):
        """
        Ingest a single poem and its poet into the database.
        Returns the poem's UUID.
        """
        with self.conn.cursor() as cur:
            # 1. Upsert Poet
            cur.execute("""
                INSERT INTO poets (slug, name_ar, era)
                VALUES (%s, %s, %s)
                ON CONFLICT (slug) DO UPDATE SET
                    name_ar = EXCLUDED.name_ar,
                    era = EXCLUDED.era
                RETURNING id;
            """, (
                poem_data.get('poet_slug', 'unknown'), 
                poem_data.get('poet'), 
                poem_data.get('era')
            ))
            poet_id = cur.fetchone()[0]

            # 2. Upsert Poem
            cur.execute("""
                INSERT INTO poems (
                    poet_id, title, title_searchable, original_text, 
                    searchable_text, meter, rhyme, category, source_url, scraped_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_url) DO UPDATE SET
                    original_text = EXCLUDED.original_text,
                    searchable_text = EXCLUDED.searchable_text
                RETURNING id;
            """, (
                poet_id,
                poem_data.get('title'),
                poem_data.get('title_searchable'),
                poem_data.get('original_text'),
                poem_data.get('searchable_text'),
                poem_data.get('meter'),
                poem_data.get('rhyme'),
                poem_data.get('category'),
                poem_data.get('source_url'),
                poem_data.get('scraped_at')
            ))
            poem_id = cur.fetchone()[0]
            
            return poem_id

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")

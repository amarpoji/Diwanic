"""Prefect task for ingesting cleaned poems into Postgres and Qdrant."""
from prefect import task
from diwanic.storage.repository import DiwanicRepository
from diwanic.app.database import SessionLocal
import json

from prefect import task
from diwanic.storage.repository import DiwanicRepository
from diwanic.app.database import SessionLocal
from diwanic.vectorstore.verse_store import DiwanicVerseStore
import json

@task
def ingest_poems_task(input_path: str = "data/embeddings/poems_with_embeddings.jsonl"):
    """
    Ingest poems from JSONL into DB and Qdrant.
    Uses Postgres as source of truth and Qdrant as stateless index.
    """
    db = SessionLocal()
    repo = DiwanicRepository(db)
    verse_store = DiwanicVerseStore()
    
    # Process file
    count = 0
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            poem_data = json.loads(line)
            
            # 1. Authoritative metadata in Postgres
            poet_name = poem_data["poet"]
            slug = poet_name.lower().replace(" ", "_")
            poet = repo.get_poet_by_slug(slug)
            if not poet:
                poet = repo.create_poet(slug=slug, name_ar=poet_name, era=poem_data.get("era"))
            
            poem = repo.get_poem_by_source_url(poem_data.get("source_url"))
            if not poem:
                # searchable_text is derived using our centralized utility in the repository layer
                poem = repo.create_poem(
                    poet_id=poet.id, 
                    title=poem_data["title"], 
                    title_searchable=poem_data["title_searchable"],
                    original_text=poem_data["original_text"], 
                    searchable_text=poem_data["searchable_text"],
                    meter=poem_data.get("meter"), 
                    rhyme=poem_data.get("rhyme"), 
                    category=poem_data.get("category"),
                    source_url=poem_data.get("source_url")
                )
                
                # Create verses in Postgres
                searchable_verses = poem_data["searchable_text"].split("\n")
                verse_objs = repo.create_verses(
                    poem_id=poem.id, 
                    verses=poem_data["verses"], 
                    searchable_verses=searchable_verses
                )
            else:
                # If poem exists, fetch its verses
                from diwanic.models import Verse
                verse_objs = db.query(Verse).filter(Verse.poem_id == poem.id).order_by(Verse.verse_index).all()
            
            # 2. Derived Index in Qdrant (Stateless)
            # We assume poem_data contains 'verse_embeddings' list matching 'verses'
            # If not present (legacy format), we skip Qdrant ingestion for this turn
            if "verse_embeddings" in poem_data:
                verses_to_upsert = []
                for idx, (v_obj, v_emb) in enumerate(zip(verse_objs, poem_data["verse_embeddings"])):
                    verses_to_upsert.append({
                        "vector": v_emb,
                        "payload": {
                            "poem_id": str(poem.id),
                            "verse_index": v_obj.verse_index,
                            "poet": poet.name_ar,
                            "era": poet.era,
                            "text": v_obj.original_text
                        }
                    })
                
                if verses_to_upsert:
                    verse_store.upsert_verses(verses_to_upsert)
            
            count += 1
            
    db.close()
    return count

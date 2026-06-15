"""Prefect task for scraping poems from Aldiwan.net."""
from prefect import task
from diwanic.scraper.pipeline import scrape_all_poets, save_poems

@task
def scrape_poets_task(config_path: str = "configs/poets.yaml", max_poems_per_poet: int = 30, output_path: str = "data/raw/poems_all.jsonl"):
    """
    Scrape poems for all poets defined in the config file and save to JSONL.
    """
    poems = scrape_all_poets(config_path=config_path, max_poems_per_poet=max_poems_per_poet)
    save_poems(poems, output_path)
    return len(poems)

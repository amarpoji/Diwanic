import gradio as gr
import logfire
from diwanic.core.observability import setup_observability
from diwanic.search.engine import HybridSearchEngineV2
from diwanic.search.router import IntentRouter
from diwanic.storage.repository import DiwanicRepository
from diwanic.app.database import SessionLocal
import pandas as pd

setup_observability()

# Initialize components
router = IntentRouter()
engine = HybridSearchEngineV2()
db = SessionLocal()
repo = DiwanicRepository(db)

def search_poems(query: str) -> pd.DataFrame:
    if not query or len(query.strip()) < 2:
        return pd.DataFrame(columns=["ID", "عنوان القصيدة", "الشاعر"])
    
    plan = router.analyze_query(query)
    results = engine.search(plan, limit=10)
    
    data = [
        {"ID": r.poem_id, "عنوان القصيدة": r.title, "الشاعر": r.poet, "النص": r.original_text}
        for r in results
    ]
    return pd.DataFrame(data)

def on_select(evt: gr.SelectData):
    poem_id = evt.value if evt.index[1] == 0 else evt.table_data[evt.index[0]][0]
    
    # Fetch full poem
    poem = repo.get_poem_by_id(poem_id)
    if not poem:
        return "القصيدة غير موجودة", "غير متوفر", "غير متوفر"
        
    full_text = f"<div class='detail-text'>{poem.original_text.replace(chr(10), '<br>')}</div>"
    poet = repo.get_poet_by_id(poem.poet_id)
    poet_name = poet.name if poet else "غير معروف"
    
    insight = "هذه القصيدة تُظهر جماليات العصر، وتعتبر من أجمل ما قيل في هذا الموضوع."
    
    return gr.update(visible=True), full_text, f"**الشاعر:** {poet_name}", f"**لمحة:** {insight}"

with gr.Blocks(title="📖 ديوانك") as demo:
    gr.Markdown("# 📖 ديوانك")
    with gr.Row():
        search_input = gr.Textbox(placeholder="ابحث عن قصيدتك...")
        btn = gr.Button("بحث")
    
    results_df = gr.Dataframe(headers=["ID", "عنوان القصيدة", "الشاعر"], interactive=False)
    
    with gr.Group(visible=False) as detail_group:
        detail_text = gr.HTML()
        poet_md = gr.Markdown()
        insight_md = gr.Markdown()
    
    btn.click(search_poems, inputs=search_input, outputs=results_df)
    results_df.select(on_select, outputs=[detail_group, detail_text, poet_md, insight_md])

if __name__ == "__main__":
    demo.launch()

"""Diwanic - Arabic Poetry Discovery UI (Gradio 6.0 + Wired to Engine)"""

import gradio as gr
import logfire
from diwanic.core.observability import setup_observability
from diwanic.app.portal import (
    perform_semantic_search,
    get_poem_detail,
    get_poem_of_the_day,
)

setup_observability()

def format_card(poem: dict) -> str:
    """Build HTML for one poem card."""
    score_pct = int(poem.get("score", 0) * 100)
    pid = poem.get("id", "")
    return f"""
    <div class="poem-card" style="border:1px solid #ddd; padding:20px; border-radius:12px; background:white;">
        <h4 style="margin:0;">{poem.get('title', '')} <span style="font-size:0.8em; color:#777;">({score_pct}% match)</span></h4>
        <p>{poem.get('poet', '')} | {poem.get('era', 'غير محدد')}</p>
        <p style="font-style:italic;">{poem.get('snippet', '')}...</p>
        <button class="detail-btn" onclick="trigger_detail('{pid}')">📖 عرض التفاصيل</button>
    </div>
    """

def on_search(query, era, poet, mood):
    poems = perform_semantic_search(query, era, poet)
    if not poems:
        return "<div style='text-align:center;'>لم يتم العثور على نتائج</div>"
    cards = "".join(format_card(p) for p in poems)
    return f'<div style="display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:20px;">{cards}</div>'

def on_detail_click(poem_id):
    data = get_poem_detail(poem_id)
    return (
        gr.update(visible=True),
        f"<div class='detail-poem-text'>{data['full_text']}</div>",
        f"**الشاعر:** {data['poet']}<br>**نبذة:** {data['bio']}<br>**لمحة:** {data['insight']}",
        f"<div>{data['similar_ids']}</div>"
    )

with gr.Blocks(title="📖 ديوانك") as demo:
    gr.Markdown("# 📖 ديوانك")
    
    with gr.Row():
        search_input = gr.Textbox(placeholder="ابحث عن قصيدة...", scale=8)
        search_btn = gr.Button("بحث", variant="primary", scale=1)
    
    # Hidden state to store clicked ID
    selected_id = gr.State("")
    
    feed_html = gr.HTML()
    
    with gr.Group(visible=False) as detail_group:
        detail_text = gr.HTML()
        detail_info = gr.HTML()
        similar_html = gr.HTML()
        btn_close = gr.Button("✕ إغلاق")

    # Wire events
    search_btn.click(on_search, inputs=[search_input, gr.State("الكل"), gr.State("الكل"), gr.State("الكل")], outputs=[feed_html])
    
    # Detail modal logic would use the selected_id and on_detail_click
    btn_close.click(lambda: gr.update(visible=False), outputs=detail_group)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)

"""Diwanic – Simple Arabic Poetry Search Demo (Gradio 6.0)

Features:
  • Single-page search box
  • Controls: number of results, confidence threshold
  • Results list with expandable full poem
"""

import gradio as gr
from diwanic.core.observability import setup_observability
from diwanic.app.portal import (
    perform_semantic_search,
    get_poem_detail,
)

setup_observability()


def format_results_html(poems, min_confidence):
    """Return HTML list of result cards filtered by min_confidence."""
    if not poems:
        return "<div style='padding:20px;text-align:center;color:#999;'>لا توجد نتائج</div>"
    
    # Filter by confidence (score is 0-1)
    filtered = [p for p in poems if p.get("score", 0) >= min_confidence / 100.0]
    if not filtered:
        return f"<div style='padding:20px;text-align:center;color:#999;'>لا توجد نتائج بحد أدنى ثقة {min_confidence}%</div>"
    
    # Build a simple vertical list — no JS, just clean HTML
    cards = []
    for i, p in enumerate(filtered, 1):
        score_pct = int(p.get("score", 0) * 100)
        title = p.get("title", "")
        poet = p.get("poet", "")
        era = p.get("era", "")
        snippet = p.get("snippet", "")
        
        score_color = "#4CAF50" if score_pct >= 80 else "#FF9800" if score_pct >= 60 else "#f44336"
        
        card = f"""
        <div style="
            border:1px solid #ddd;
            margin:10px 0;
            padding:15px;
            border-radius:8px;
            background:#fafafa;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div style="flex:1;">
                    <div style="font-weight:bold; font-size:1.1em; margin-bottom:4px;">
                        {i}. {title}
                    </div>
                    <div style="color:#666; font-size:0.9em; margin-bottom:4px;">
                        {poet} | {era}
                    </div>
                    <div style="color:#2c3e50; padding:8px; border-radius:4px; border-right:3px solid #2196F3;">
                        {snippet[:200]}{'...' if len(snippet) > 200 else ''}
                    </div>
                </div>
                <div style="text-align:right; min-width:80px; padding-left:12px;">
                    <div style="
                        background:{score_color};
                        color:white;
                        padding:4px 8px;
                        border-radius:12px;
                        font-size:0.9em;
                        font-weight:bold;">
                        {score_pct}%
                    </div>
                </div>
            </div>
        </div>
        """
        cards.append(card)
    
    return "".join(cards)


def search_and_display(query, num_results, confidence_threshold):
    """Perform search and return HTML of results."""
    if not query or len(query.strip()) < 2:
        return "<div style='padding:20px;text-align:center;color:#999;'>أدخل مصطلح بحث مكون من حرفين على الأقل</div>"
    
    try:
        poems = perform_semantic_search(query, limit=int(num_results))
        return format_results_html(poems, float(confidence_threshold))
    except Exception as e:
        return f"<div style='padding:20px;text-align:center;color:#f44336;'>خطأ: {str(e)}</div>"


# ----------------------------------------------------------------------
# Build UI – Simple Search
# ----------------------------------------------------------------------
def build_ui():
    with gr.Blocks(title="📖 ديوانك – بحث بسيط في الشعر العربي") as ui:
        gr.Markdown("# 🔍 ديوانك – بحث بسيط في الشعر العربي")
        gr.Markdown("ابحث عن أبيات أو مواضيع وضبط عدد النتائج وحد أدنى الثقة.")
        
        with gr.Row():
            with gr.Column(scale=4):
                search_input = gr.Textbox(
                    label="",
                    placeholder="🔍 ابحث عن بيت، شاعر أو موضوع...",
                    lines=1,
                )
            with gr.Column(scale=1):
                search_btn = gr.Button("بحث", variant="primary")
        
        with gr.Row():
            with gr.Column(scale=1):
                num_results = gr.Dropdown(
                    choices=[5, 10, 20, 50],
                    value=10,
                    label="عدد النتائج",
                )
            with gr.Column(scale=1):
                confidence_threshold = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=60,
                    step=5,
                    label="حد أدنى الثقة (%)",
                    info="إظهار النتائج التي لها ثقة أكبر من أو يساوي هذا القيمة",
                )
        
        results_html = gr.HTML()
        
        # Wire up
        search_btn.click(
            fn=search_and_display,
            inputs=[search_input, num_results, confidence_threshold],
            outputs=results_html,
        )
        search_input.submit(
            fn=search_and_display,
            inputs=[search_input, num_results, confidence_threshold],
            outputs=results_html,
        )
    
    return ui

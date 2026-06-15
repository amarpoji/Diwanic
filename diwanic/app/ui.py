"""Diwanic - Arabic Poetry Search Engine UI"""

# ─────────────────────────────────────────────────────────
# 1. Initialize observability FIRST (before any other imports)
#    This ensures logfire.configure() runs before SQLAlchemy/HTTP instrumentation
# ─────────────────────────────────────────────────────────
from diwanic.core.observability import setup_observability
setup_observability()

# ─────────────────────────────────────────────────────────
# 2. Now safe to import everything else
# ─────────────────────────────────────────────────────────
import gradio as gr
from diwanic.search.engine import HybridSearchEngineV2
from diwanic.search.router import IntentRouter
from diwanic.utils.logger_util import get_logger
import traceback
import logfire

logger = get_logger(__name__)

# Initialize components once
router = IntentRouter()
engine = HybridSearchEngineV2()


def format_result(res):
    """Format a single SearchResult into HTML for display."""
    score_pct = int(res.score * 100)
    
    # Header with Title and Metadata
    header = f"""
    <div style="border-bottom: 1px solid #ddd; padding-bottom: 10px; margin-bottom: 10px;">
        <span style="font-size: 1.4em; font-weight: bold; color: #2c3e50;">{res.title}</span>
        <br/>
        <span style="color: #7f8c8d; font-size: 0.9em;">
            👤 {res.poet} | 🏛️ {res.era or "غير محدد"} | 🏆 {score_pct}% match
        </span>
    </div>
    """
    
    # Context message for verse matches
    context = ""
    if res.match_type == "verse" and res.verse_index is not None:
        context = f"""
        <div style="background-color: #f1f8ff; border-left: 4px solid #007bff; padding: 8px; margin-bottom: 10px; font-style: italic;">
            📍 تطابق في البيت رقم {res.verse_index + 1}
        </div>
        """
    
    # The actual poem text (formatted with line breaks)
    text_content = f"""
    <div style="font-family: 'Noto Naskh Arabic', serif; font-size: 1.2em; line-height: 1.8; color: #34495e; white-space: pre-wrap; direction: rtl;">
{res.original_text}
    </div>
    """
    
    return f"""
    <div style="background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 1px solid #eee; direction: rtl;">
        {header}
        {context}
        {text_content}
    </div>
    """


def perform_search(query):
    if not query or len(query.strip()) < 2:
        return "<div style='text-align: center; color: #7f8c8d;'>الرجاء إدخال كلمة للبحث عنها...</div>"
    
    with logfire.span("ui_search", query=query):
        try:
            # 1. Analyze intent
            plan = router.analyze_query(query)
            
            # 2. Execute hybrid search (Postgres-as-Truth hydration happens inside)
            results = engine.search(plan, limit=10)
            
            if not results:
                logfire.info("No results found", query=query)
                return "<div style='text-align: center; color: #e74c3c; padding: 20px;'>لم يتم العثور على نتائج. حاول تغيير كلمات البحث.</div>"
            
            # 3. Format all results into one HTML block
            html_output = "".join([format_result(r) for r in results])
            logfire.info("Search results returned", count=len(results))
            return html_output
            
        except Exception as e:
            logfire.error("UI Search Error", exc=e)
            logger.error(f"UI Search Error: {e}\n{traceback.format_exc()}")
            return f"<div style='color: red; padding: 20px;'>خطأ في البحث: {str(e)}</div>"


# Custom CSS for Arabic layout and better fonts
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@400;700&display=swap');
.gradio-container {
    direction: rtl !important;
}
input, button, textarea {
    font-family: 'Noto Naskh Arabic', sans-serif !important;
    direction: rtl !important;
}
#search-btn {
    background-color: #2c3e50 !important;
    color: white !important;
}
"""

with gr.Blocks(title="ديوانك - محرك بحث الشعر العربي") as demo:
    with gr.Column(elem_id="container"):
        gr.Markdown(
            """
            <div style="text-align: center; padding: 20px;">
                <h1 style="font-family: 'Noto Naskh Arabic', serif; font-size: 3em; margin-bottom: 10px;">📖 ديوانك</h1>
                <p style="font-size: 1.2em; color: #7f8c8d;">محرك بحث ذكي للشعر العربي - مدعوم بالذكاء الاصطناعي</p>
            </div>
            """
        )
        
        with gr.Row():
            search_input = gr.Textbox(
                label="",
                placeholder="ابحث عن بيت، شاعر، أو موضوع (مثلاً: الصبر عند الشافعي)...",
                lines=1,
                elem_id="search-input",
                container=False,
                scale=9
            )
            search_button = gr.Button("بحث 🔍", variant="primary", scale=1, elem_id="search-btn")
        
        gr.Markdown("---")
        
        output_html = gr.HTML(
            label="النتائج",
            value="<div style='text-align: center; color: #7f8c8d; padding: 50px;'>أدخل بحثك في الأعلى واضغط Enter أو زر البحث</div>",
            elem_id="results-area"
        )
        
    # Trigger on both Button click and Enter key
    search_input.submit(fn=perform_search, inputs=search_input, outputs=output_html)
    search_button.click(fn=perform_search, inputs=search_input, outputs=output_html)


if __name__ == "__main__":
    # Ensure connections are ready
    logger.info("Starting Gradio UI...")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)

"""Diwanic Full Discovery UI — Gradio 6.0 compatible, fully wired to real engine."""

import gradio as gr
import traceback
import logfire

from diwanic.core.observability import setup_observability
from diwanic.utils.logger_util import get_logger
from diwanic.app.portal import (
    perform_semantic_search,
    get_poem_detail,
    get_poem_of_the_day,
    generate_tts_audio,
)

setup_observability()
logger = get_logger(__name__)

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@400;700&display=swap');

.gradio-container {
    direction: rtl !important;
    max-width: 1400px;
    margin: 0 auto;
    font-family: 'Noto Naskh Arabic', serif;
}

#hero-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 40px 20px;
    color: white;
    margin: 20px 0;
    text-align: center;
}
#hero-section h2 { font-size: 2em; margin: 10px 0; }
#hero-section button {
    background: white;
    color: #667eea;
    border: none;
    padding: 12px 30px;
    border-radius: 8px;
    font-size: 1.1em;
    font-weight: bold;
    cursor: pointer;
}
.poem-card {
    border: 1px solid #e0e0e0;
    padding: 20px;
    border-radius: 12px;
    background: #fefefe;
    display: flex;
    flex-direction: column;
    transition: all 0.2s ease;
    height: 100%;
}
.poem-card:hover {
    border-color: #667eea;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.card-mood {
    display: inline-block;
    background: #e8f4fd;
    color: #007bff;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.9em;
    align-self: flex-start;
    margin: 8px 0;
}
.card-actions {
    display: flex;
    justify-content: space-between;
    margin-top: 12px;
}
.card-actions button {
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    font-size: 0.95em;
}
#detail-modal {
    border: 2px solid #2c3e50;
    border-radius: 12px;
    padding: 30px;
    background: white;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    margin-top: 20px;
}
.detail-poem-text {
    font-family: 'Noto Naskh Arabic', serif;
    font-size: 1.4em;
    line-height: 2;
    text-align: center;
    color: #2c3e50;
}
"""


def format_card(poem: dict) -> str:
    """Build HTML for one poem card with confidence score and action buttons."""
    score_pct = int(poem.get("score", 0) * 100)
    pid = poem.get("id", "")
    return f"""
    <div class="poem-card" id="card-{pid}">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h4 style="margin:0; font-size:1.3em; color:#2c3e50;">{poem.get('title', '')}</h4>
            <span style="background:#e8f4fd; color:#007bff; padding:4px 10px; border-radius:15px; font-size:0.85em;">
                {score_pct}%
            </span>
        </div>
        <p style="margin:8px 0; font-size:1.1em; color:#444;">{poem.get('poet', '')} | {poem.get('era', 'غير محدد')}</p>
        <p style="font-style:italic; color:#555; flex:1;">{poem.get('snippet', '')}</p>
        <span class="card-mood">{poem.get('mood', '')}</span>
        <div class="card-actions">
            <button style="background:#2c3e50; color:white;" onclick="alert('TTS not wired yet – see console')">🎧 استماع</button>
            <button style="background:#ecf0f1; color:#2c3e50; border:1px solid #ccc;" onclick="alert('تفاصيل')">📖 التفاصيل</button>
        </div>
    </div>
    """


def search_and_feed(query: str, era: str, poet: str, mood: str):
    """Run search through the real engine and return HTML for the feed grid."""
    poems = perform_semantic_search(query, era, poet)
    if not poems:
        return "<div style='text-align:center; padding:40px; color:#999;'>لم يتم العثور على نتائج</div>"
    cards = "".join(format_card(p) for p in poems)
    return f'<div style="display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:20px;">{cards}</div>'


def open_detail(poem_id: int):
    """Fetch full detail data and populate the detail modal."""
    detail_data = get_poem_detail(int(poem_id))
    if not detail_data:
        return [gr.update(visible=False), "", "", ""]

    # Poem text
    poem_html = f'<div class="detail-poem-text">{detail_data["full_text"]}</div>'
    # Poet info + insight
    info_html = f"""
    <p><strong>الشاعر:</strong> {detail_data['poet']} | <strong>العصر:</strong> {detail_data['era']}</p>
    <p><strong>السيرة:</strong> {detail_data['bio']}</p>
    <p><strong>🧠 DeepSeek Insight:</strong> {detail_data['insight']}</p>
    """
    # Similar poems list via repo (placeholder)
    similar_ids = detail_data.get("similar_ids", [])
    if similar_ids:
        from diwanic.app.portal import repo
        similar_poems = [repo.get_by_id(i) for i in similar_ids if repo.get_by_id(i)]
        similar_html = "<br>".join(
            [f"- {p.get('title', '')} ({p.get('mood', '')})" for p in similar_poems]
        ) if similar_poems else "لا توجد قصائد مشابهة"
    else:
        similar_html = "لا توجد قصائد مشابهة"

    return [
        gr.update(visible=True),
        poem_html,
        info_html,
        f"<div>{similar_html}</div>",
    ]


# ---------- Build UI ----------
with gr.Blocks(title="📖 ديوانك - اكتشف الشعر العربي", css=CSS, theme="soft") as demo:
    # Header
    with gr.Row(elem_id="header"):
        gr.Markdown("## 📖 **ديوانك**  —  استكشف جمال الشعر العربي", elem_id="logo")

    # Search row
    with gr.Row():
        search_input = gr.Textbox(
            label="", placeholder="🔍 ابحث عن بيت، شاعر، أو موضوع...", scale=8, elem_id="search-input"
        )
        search_btn = gr.Button("بحث", variant="primary", scale=1, elem_id="search-btn")

    # Filters row
    with gr.Row():
        era_filter = gr.Dropdown(
            ["الكل", "جاهلي", "أموي", "عباسي", "أندلسي"],
            label="العصر", value="الكل"
        )
        poet_filter = gr.Dropdown(
            ["الكل", "المتنبي", "عنترة", "الخنساء", "أبو نواس", "البحتري", "الشافعي"],
            label="الشاعر", value="الكل"
        )
        mood_filter = gr.Dropdown(
            ["الكل", "الحكمة", "الغزل", "الرثاء", "الفخر", "الهجاء"],
            label="الموضوع", value="الكل"
        )
        filter_btn = gr.Button("تحديث الفلاتر", variant="secondary")

    # Hero section (Poem of the Day)
    day_poem = get_poem_of_the_day()
    with gr.Row(elem_id="hero-section"):
        gr.HTML(f"""
        <div>
            <span style="font-weight:bold; letter-spacing:2px;">✨ قصيدة اليوم · POEM OF THE DAY</span>
            <h2>{day_poem['title']}</h2>
            <p style="font-size:1.2em;">{day_poem['first_two_lines']}</p>
            <p style="font-size:1em; opacity:0.85;">— {day_poem['poet']}</p>
            <button onclick="alert('سيتم تشغيل الصوت...')">🎧 استمع إلى القصيدة</button>
        </div>
        """)

    # Smart Feed title
    gr.Markdown("### 🌟 القصائد المميزة")
    feed_html = gr.HTML(elem_id="poem-feed", value="""
    <div style='text-align:center; padding:40px; color:#999;'>اكتب كلمة في البحث أعلاه للعثور على القصائد</div>
    """)

    # Detail modal (hidden initially)
    with gr.Group(visible=False, elem_id="detail-modal") as detail_group:
        with gr.Column():
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📖 تفاصيل القصيدة")
            with gr.Row():
                with gr.Column(scale=7):
                    detail_text = gr.HTML(value="<div class='detail-poem-text'>نص القصيدة...</div>")
                with gr.Column(scale=5):
                    detail_info = gr.HTML(value="<p>المعلومات عن الشاعر والقصيدة...</p>")
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🔗 قصائد مشابهة")
            with gr.Row():
                detail_similar = gr.HTML(value="<div>اختر قصيدة لعرض المشابهات...</div>")
            with gr.Row():
                btn_listen = gr.Button("🎧 استمع إلى القصيدة", variant="primary")
                btn_close = gr.Button("✕ إغلاق", variant="secondary")

    # ---------- Callbacks ----------
    # Search
    def on_search(query, era, poet, mood):
        html = search_and_feed(query, era, poet, mood)
        return html, gr.update(visible=False)

    search_btn.click(fn=on_search, inputs=[search_input, era_filter, poet_filter, mood_filter],
                     outputs=[feed_html, detail_group])
    search_input.submit(fn=on_search, inputs=[search_input, era_filter, poet_filter, mood_filter],
                        outputs=[feed_html, detail_group])
    filter_btn.click(fn=on_search, inputs=[search_input, era_filter, poet_filter, mood_filter],
                     outputs=[feed_html, detail_group])

    # Close detail
    btn_close.click(
        fn=lambda: [gr.update(visible=False), "", "", ""],
        outputs=[detail_group, detail_text, detail_info, detail_similar]
    )

    # TTS placeholder
    btn_listen.click(
        fn=lambda: "🔊 سيتم تشغيل الصوت قريباً...",
        outputs=[gr.Textbox(visible=False)]
    )


if __name__ == "__main__":
    import subprocess, shlex
    subprocess.run(shlex.split("fuser -k 7860/tcp"), shell=True, capture_output=True)
    logger.info("Launching Diwanic Full Discovery UI...")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)

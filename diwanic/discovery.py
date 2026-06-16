"""Diwanic Full Discovery Page — a curated, library‑grade Poetry Discovery experience.

Features:
- Hero section with ``Poem of the Day`` and TTS
- Era / Poet / Mood filter controls
- Dynamic poem card feed (grid)
- Immersive detail modal (poem text, poet bio, semantic insights, similar poems)
- TTS placeholder
- Responsive CSS with Noto Naskh Arabic font
"""

import gradio as gr
import json, os, datetime
import traceback
import logfire
from diwanic.core.observability import setup_observability
from diwanic.search.engine import HybridSearchEngineV2
from diwanic.search.router import IntentRouter
from diwanic.utils.logger_util import get_logger
from diwanic.storage.repository import DiwanicRepository

setup_observability()
logger = get_logger(__name__)

router = IntentRouter()
engine = HybridSearchEngineV2()
repo = DiwanicRepository()          # future: hydrate detail pages

# ---------- helpers ----------
def load_similar_poems(poem_id: int) -> list:
    """Return a placeholder list of similar poem dicts."""
    return [
        {"id": poem_id + 1, "title": "قصيدة مشابهة ١", "snippet": "بيت مشهور...", "mood": "حكمة"},
        {"id": poem_id + 2, "title": "قصيدة مشابهة ٢", "snippet": "بيت آخر...",    "mood": "غزل"},
        {"id": poem_id + 3, "title": "قصيدة مشابهة ٣", "snippet": "بيت ثالث...",  "mood": "حكمة"},
    ]

def get_poem_of_the_day() -> dict:
    """Return a hardcoded Poem of the Day."""
    return {
        "id": 1,
        "title": "هل غادر الشعراء من متردم",
        "first_two_lines": "من أعماق التاريخ: هل غادر الشعراء من متردم...",
        "mood": "حكمة",
        "poet": "عنترة بن شداد",
        "era": "الجاهلي",
        "full_text": "<center><p style='font-size:1.1em;'>هل غادر الشعراء من متردم<br>أم هل عرفت الدار بعد توهم</p><p>...</p></center>",
        "insight": "هذه القصيدة تُظهر قوة الفخر الجاهلي وتُعتبر من روائع عنترة بن شداد. تتحدث عن الحب والشجاعة والفخر.",
    }

def search_poems(query: str, poet: str, era: str) -> list:
    """Call the engine and return a list of poem dicts for the feed."""
    if not query or len(query.strip()) < 2:
        return []
    plan = router.analyze_query(query)
    results = engine.search(plan, limit=10)
    feed = []
    for i, r in enumerate(results):
        feed.append({
            "id": getattr(r, 'poem_id', i),
            "title": getattr(r, 'title', f'نتيجة {i+1}'),
            "first_two_lines": getattr(r, 'original_text', '')[:120],
            "mood": "حكمة",
            "poet": getattr(r, 'poet', '???'),
            "era": getattr(r, 'era', '???'),
        })
    return feed

def build_card_html(poem: dict) -> str:
    return f"""
    <div class="poem-card" data-id="{poem['id']}" style="
        border:1px solid #e0e0e0; padding:20px; border-radius:12px;
        background:#fefefe; display:flex; flex-direction:column;
        transition:all .2s ease; cursor:default;
    ">
        <h5 style="margin:0 0 10px; font-size:1.3em; color:#2c3e50;">{poem['title']}</h5>
        <span style="display:inline-block; background:#e8f4fd; color:#007bff; padding:4px 12px; border-radius:20px; font-size:0.9em; align-self:flex-start; margin-bottom:10px;">{poem['mood']}</span>
        <p style="flex:1; font-size:1.1em; line-height:1.6; color:#444;">{poem['first_two_lines']}</p>
        <div style="display:flex; justify-content:space-between;">
            <button class="tts-btn" style="background:#2c3e50; color:white; border:none; padding:8px 16px; border-radius:6px;">🎧 استماع</button>
            <button class="detail-btn" style="background:#ecf0f1; color:#2c3e50; border:1px solid #ccc; padding:8px 16px; border-radius:6px;">📖 التفاصيل</button>
        </div>
    </div>
    """

# ---------- Gradio page ----------
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@400;700&display=swap');
* { font-family: 'Noto Naskh Arabic', serif; box-sizing:border-box; }
.gradio-container { direction:rtl !important; max-width:1400px; margin:0 auto; }
#hero-row { background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); border-radius:16px; padding:40px; margin:20px 0; color:white; }
#hero-row h2 { font-size:2em; }
.detail-container { background:white; border-radius:12px; padding:30px; box-shadow:0 4px 15px rgba(0,0,0,.15); margin-top:20px; }
.detail-text { font-size:1.4em; line-height:2; text-align:center; color:#2c3e50; }
button { cursor:pointer; }
"""

def make_discovery_page():
    with gr.Blocks(title="📖 Diwanic – إكتشف الشعر العربي", css=CSS, theme="soft") as demo:
        # ---------- 1. Header / Navigation ----------
        with gr.Row(elem_id="header"):
            with gr.Column(scale=2):
                gr.Markdown("## 📖 **ديوانك**   *استكشف جمال الشعر العربي عبر العصور*")
            with gr.Column(scale=1):
                pass  # placeholder for future user/profile button

        # ---------- 2. Hero ----------
        with gr.Row(elem_id="hero-row"):
            gr.HTML("""
            <div style="text-align:center;">
                <h2>📍 قصيدة اليوم</h2>
                <p style="font-size:1.3em; margin:10px 0 20px;">
                    من أعماق التاريخ: هل غادر الشعراء من متردم...  
                </p>
                <p style="font-size:1.1em; opacity:.85; margin-bottom:20px;">
                    — عنترة بن شداد
                </p>
                <button style="background:white; color:#667eea; border:none; padding:12px 30px; border-radius:8px; font-size:1.1em; font-weight:bold;">
                    🎧 استمع إلى القصيدة
                </button>
            </div>
            """)

        # ---------- 3. Search & Filters ----------
        with gr.Row():
            with gr.Column(scale=8):
                search_input = gr.Textbox(label="", placeholder="🔍 ابحث عن بيت، شاعر، أو موضوع...", elem_id="search-input")
            with gr.Column(scale=1):
                search_btn = gr.Button("بحث", variant="primary", elem_id="search-btn")

        with gr.Row():
            with gr.Column(scale=1):
                era_filter = gr.Dropdown(
                    ["الكل", "جاهلي", "أموي", "عباسي", "أندلسي"],
                    label="العصر", value="الكل"
                )
            with gr.Column(scale=1):
                poet_filter = gr.Dropdown(
                    ["الكل", "المتنبي", "عنترة", "الخنساء", "أبو نواس", "البحتري", "الشافعي"],
                    label="الشاعر", value="الكل"
                )
            with gr.Column(scale=1):
                mood_filter = gr.Dropdown(
                    ["الكل", "الحكمة", "الغزل", "الرثاء", "الفخر", "الهجاء"],
                    label="الموضوع", value="الكل"
                )

        # ---------- 4. Smart Feed (Cards) ----------
        gr.Markdown("### 🌟 القصائد المميزة")
        feed_html = gr.HTML(elem_id="poem-feed", value="""
        <div style="display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:20px;">
            {}
        </div>
        """.format(build_card_html(get_poem_of_the_day())))

        # ---------- 5. Detail Modal (hidden initially) ----------
        with gr.Group(visible=False, elem_id="detail-modal") as detail:
            with gr.Column(elem_id="detail-container"):
                detail_title = gr.Markdown("### 📖 تفاصيل القصيدة")
                detail_text = gr.HTML(value="<div class='detail-text'>نص القصيدة يظهر هنا...</div>")
                # Poet info & insight row
                with gr.Row():
                    with gr.Column(scale=1):
                        poet_info = gr.Markdown("**الشاعر:** &#8203;")
                    with gr.Column(scale=2):
                        insight = gr.Markdown("**لمحة:** &#8203;")
                # Actions
                with gr.Row():
                    btn_listen = gr.Button("🎧 استمع إلى القصيدة", variant="primary")
                    btn_close = gr.Button("✕ إغلاق")
                # Similar poems
                gr.Markdown("### 🔗 قصائد مشابهة")
                similar_feed = gr.HTML(value="<div>اختر قصيدة لعرض المشابهات...</div>")

        # ---------- Callbacks ----------
        def do_search(query, era, poet, mood):
            if not query or query.strip() == "":
                return feed_html, detail  # no-op
            poems = search_poems(query, poet, era)
            if not poems:
                return "<div style='text-align:center;padding:40px;color:#999;'>لم يتم العثور على نتائج</div>", detail
            cards = "".join(build_card_html(p) for p in poems)
            html = f"<div style='display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:20px;'>{cards}</div>"
            return html, gr.update(visible=False)

        search_btn.click(fn=do_search, inputs=[search_input, era_filter, poet_filter, mood_filter], outputs=[feed_html])
        search_input.submit(fn=do_search, inputs=[search_input, era_filter, poet_filter, mood_filter], outputs=[feed_html])

        # Detail toggling placeholders (real logic needs JS or a stored state)
        btn_close.click(
            fn=lambda: gr.update(visible=False),
            outputs=[detail]
        )

        btn_listen.click(
            fn=lambda: "🔊 سيتم تشغيل الصوت قريباً...",
            outputs=[gr.Textbox(visible=False)]
        )

    return demo


demo = make_discovery_page()

if __name__ == "__main__":
    logger.info("Launching Diwanic Discovery Page…")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)

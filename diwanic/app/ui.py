"""Diwanic – Arabic Poetry Discovery UI (Gradio 6.0)

Features:
  • Main page: semantic search box + list of all poets.
  • Click a poet → Poet Detail page (poet name + list of poems).
  • Click a poem → Poem Detail page (full poem, meta, similar poems).
  • Fully wired to the real Diwanic engine via portal.py.
"""

import gradio as gr
from diwanic.core.observability import setup_observability
from diwanic.app.portal import (
    perform_semantic_search,
    get_all_poets,
    get_poems_by_poet,
    get_poem_detail,
)

setup_observability()


def build_poet_dropdown() -> list:
    """Return [(name, id_str), ...] choices for the poet dropdown."""
    poets = get_all_poets()
    return [(f"{p['name']} ({p['era']})", p["id"]) for p in poets]


def search_and_render(query: str) -> str:
    """Perform search and return HTML of result cards."""
    poems = perform_semantic_search(query)
    if not poems:
        return "<div style='padding:20px;text-align:center;color:#999;'>لا توجد نتائج</div>"
    cards = ""
    for p in poems:
        score = int(p.get("score", 0) * 100)
        cards += f"""
        <div style="border:1px solid #ddd;padding:12px;margin:6px 0;border-radius:8px;background:white;">
            <div style="display:flex;justify-content:space-between;">
                <strong style="font-size:1.1em;">{p['title']}</strong>
                <span style="font-size:0.8em;color:#888;">{score}%</span>
            </div>
            <span style="color:#555;">{p.get('poet','')} | {p.get('era','')}</span>
            <p style="font-style:italic;color:#777;margin:4px 0;">{p.get('snippet','')}</p>
        </div>
        """
    return cards


def render_poets_html() -> str:
    """Return HTML list of all poets."""
    poets = get_all_poets()
    items = ""
    for i, p in enumerate(poets):
        items += f"""
        <div style="
            border:1px solid #ddd;padding:8px 12px;margin:3px 0;
            border-radius:6px;background:#f9f9f9;
            display:flex;justify-content:space-between;align-items:center;">
            <div>
                <strong>{p['name']}</strong><br>
                <span style="color:#666;font-size:0.9em;">{p.get('era','')}</span>
            </div>
            <span style="color:#888;font-size:0.8em;">پ{poets.index(p)+1}</span>
        </div>
        """
    return items


def render_poems_for_poet(poet_name: str) -> str:
    """Return HTML list of poems for a given poet name."""
    poems = get_poems_by_poet(poet_name)
    if not poems:
        return "<p style='color:#999;'>لا توجد قصائد لهذا الشاعر</p>"
    items = ""
    for p in poems:
        items += f"""
        <div style="
            border:1px solid #eee;padding:10px;margin:4px 0;
            border-radius:6px;background:#fafafa;cursor:pointer;">
            <strong>{p['title']}</strong><br>
            <span style="color:#555;font-size:0.9em;">{p.get('snippet','')}</span>
        </div>
        """
    return items


def render_poem_detail_view(poem_id: str) -> str:
    """Return full HTML for the poem detail view."""
    data = get_poem_detail(poem_id)
    if not data:
        return "<div style='padding:20px;color:#999;'>لم يتم العثور على القصيدة</div>"
    return f"""
    <div style="line-height:1.8;padding:20px;">
        <h2 style="margin-bottom:8px;">{data['title']}</h2>
        <p><strong>الشاعر:</strong> {data['poet']}</p>
        <p><strong>العصر:</strong> {data['era']}</p>
        <p><strong>التصنيف:</strong> {data.get('category','')}</p>
        <hr>
        <div style="white-space:pre-line;font-size:1.1em;color:#2c3e50;">
            {data['full_text']}
        </div>
        <hr>
    </div>
    """


# ----------------------------------------------------------------------
# Build UI
# ----------------------------------------------------------------------
with gr.Blocks(title="📖 ديوانك – اكتشف الشعر العربي", theme="soft") as ui:
    # --- State ---
    current_view = gr.State("main")
    selected_poet_id = gr.State("")
    selected_poem_id = gr.State("")
    selected_poet_name = gr.State("")

    # =================== MAIN VIEW ===================
    with gr.Column(visible=True) as main_panel:
        gr.Markdown("## 📖 ديوانك – اكتشف الشعر العربي")

        # Search
        with gr.Row():
            search_input = gr.Textbox(label="", placeholder="🔍 ابحث عن بيت، شاعر أو موضوع...", scale=8)
            search_btn = gr.Button("بحث", variant="primary", scale=1)

        search_results = gr.HTML()

        gr.Markdown("---")
        gr.Markdown("### 📜 كل الشعراء")

        # Poet dropdown selector
        poet_selector = gr.Dropdown(
            choices=build_poet_dropdown(),
            label="اختر شاعرا",
            value=None,
            interactive=True,
        )
        go_to_poet_btn = gr.Button("عرض قصائد الشاعر", variant="primary", visible=False)

        # Also render full poet list as HTML
        poet_list_html = gr.HTML(value=render_poets_html())

    # =================== POET VIEW ===================
    with gr.Column(visible=False) as poet_panel:
        gr.Markdown("### 📜 قصائد الشاعر")
        poet_name_display = gr.Markdown()
        poem_list_html = gr.HTML()
        with gr.Row():
            back_to_main_btn = gr.Button("← العودة للقائمة الرئيسية", variant="secondary")
            poem_selector = gr.Dropdown(label="اختر قصيدة", value=None, interactive=True)
            view_poem_btn = gr.Button("عرض القصيدة", variant="primary", visible=False)

    # =================== POEM VIEW ===================
    with gr.Column(visible=False) as poem_panel:
        gr.Markdown("### 📖 القصيدة")
        poem_detail_display = gr.HTML()
        back_to_poet_btn = gr.Button("← العودة للشاعر", variant="secondary")

    # =================== NAVIGATION LOGIC ===================

    # ---- Main → Poet ----
    def on_poet_selected(poet_id):
        """Called when dropdown value changes or button is pressed."""
        if not poet_id:
            return tuple([gr.update(visible=True)] + [gr.update()]*5)
        # Look up the poet name from the full list
        all_poets = get_all_poets()
        poet_name = ""
        for p in all_poets:
            if p["id"] == poet_id:
                poet_name = p["name"]
                break
        if not poet_name:
            return tuple([gr.update(visible=True)] + [gr.update()]*5)

        poems = get_poems_by_poet(poet_name)
        poems_display = render_poems_for_poet(poet_name)
        poem_choices = [(f"{p['title'][:40]}", p["id"]) for p in poems]

        return (
            # Toggle main off, poet on
            gr.update(visible=False),
            gr.update(visible=True),
            # Set poet name display
            f"**{poet_name}**",
            # Poem list HTML
            poems_display,
            # Update poem dropdown
            gr.update(choices=poem_choices, value=None),
        )

    def go_to_poet(poet_id):
        if not poet_id:
            return (gr.update(),) * 6
        return on_poet_selected(poet_id)

    # Wire poet selection
    def on_poet_btn_click(poet_id):
        if not poet_id:
            # Try to read from dropdown
            return go_to_poet(poet_id)
        return go_to_poet(poet_id)

    # ---- Back to Main ----
    def back_to_main():
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
        )

    back_to_main_btn.click(fn=back_to_main, outputs=[main_panel, poet_panel, poem_panel])

    # ---- Poet → Poem ----
    def on_view_poem(poem_id):
        if not poem_id:
            return (gr.update(),) * 3
        html = render_poem_detail_view(poem_id)
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            html,
        )

    # ---- Back to Poet ----
    def back_to_poet():
        return (
            gr.update(visible=True),
            gr.update(visible=False),
        )

    back_to_poet_btn.click(fn=back_to_poet, outputs=[poet_panel, poem_panel])

    # ---- Wire search ----
    search_btn.click(fn=lambda q: search_and_render(q), inputs=search_input, outputs=search_results)
    search_input.submit(fn=lambda q: search_and_render(q), inputs=search_input, outputs=search_results)

    # ---- Wire poet dropdown ----
    # We need to detect when the dropdown changes and show the "View" button
    def on_dropdown_change(value):
        return gr.update(visible=bool(value))
    poet_selector.change(fn=on_dropdown_change, inputs=poet_selector, outputs=go_to_poet_btn)

    # ---- Wire "View Poet" button ----
    def handle_poet_go(poet_id):
        return go_to_poet(poet_id)

    go_to_poet_btn.click(fn=handle_poet_go, inputs=poet_selector, outputs=[
        main_panel, poet_panel, poet_name_display, poem_list_html, poem_selector, view_poem_btn,
    ])

    # ---- Wire poem dropdown ----
    def on_poem_dropdown_change(value):
        return gr.update(visible=bool(value))
    poem_selector.change(fn=on_poem_dropdown_change, inputs=poem_selector, outputs=view_poem_btn)

    # ---- Wire "View Poem" button ----
    view_poem_btn.click(fn=on_view_poem, inputs=poem_selector, outputs=[
        poet_panel, poem_panel, poem_detail_display,
    ])

    # ---- Wire "Show Details" buttons inside search results ----
    # These require JS; we skip for now. Search results show title + poet.
    # Adding click-through from search results is a future enhancement.

# ----------------------------------------------------------------------
# Launch
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import subprocess, shlex
    subprocess.run(shlex.split("fuser -k 7860/tcp"), shell=True, capture_output=True)
    ui.launch(server_name="0.0.0.0", server_port=7860, share=True)

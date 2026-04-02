import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
import io, re, os, datetime, base64, json
import requests
from docx import Document
import markdown as md_lib

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
APP_URL = os.getenv("APP_URL", "https://your-app.streamlit.app")
APP_PIN  = os.getenv("APP_PIN", "18808")

def load_css(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f"<style>{f.read()}</style>"

st.set_page_config(page_title="VidBlog AI", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")

# ── PIN LOCK ──
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

if not st.session_state.unlocked:
    st.markdown("""<style>
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { max-width: 420px !important; margin: 80px auto !important; padding: 0 20px !important; }
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;margin-bottom:32px">
      <div style="font-size:52px;margin-bottom:16px">🎬</div>
      <div style="font-size:22px;font-weight:800;background:linear-gradient(90deg,#7c3aed,#3b82f6);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px">
        YouTube to Blog Post
      </div>
      <div style="font-size:13px;color:#94a3b8">🔒 Enter PIN to access</div>
    </div>
    """, unsafe_allow_html=True)

    pin = st.text_input("PIN", placeholder="Enter PIN", type="password",
                        label_visibility="collapsed", key="pin_input")
    if st.button("🔓 Unlock", use_container_width=True, type="primary", key="unlock_btn"):
        if pin == APP_PIN:
            st.session_state.unlocked = True
            st.rerun()
        else:
            st.error("❌ Incorrect PIN. Please try again.")
    st.stop()

for k, v in [
    ("dark_mode", False), ("page", "generate"),
    ("blog_content", None), ("cover_bytes", None),
    ("blog_filename", None), ("img_filename", None),
    ("word_count", 0), ("blog_language", "English"), ("blog_tone", "Professional"),
    ("view_blog", None),
]:
    if k not in st.session_state:
        st.session_state[k] = v

dark = st.session_state.dark_mode

# ── THEME TOKENS ──
if dark:
    BG, CARD, BORDER = "#0d0d1a", "#13132e", "rgba(255,255,255,0.08)"
    TEXT, TEXT2, MUTED = "#f1f5f9", "#cbd5e1", "#64748b"
    INPUT_BG, CHIP, CHIP_B = "#0a0a1e", "rgba(255,255,255,0.05)", "rgba(255,255,255,0.09)"
    SCROLL_TH = "rgba(139,92,246,0.45)"
else:
    BG, CARD, BORDER = "#f0f2fa", "#ffffff", "rgba(0,0,0,0.07)"
    TEXT, TEXT2, MUTED = "#0f172a", "#475569", "#94a3b8"
    INPUT_BG, CHIP, CHIP_B = "#ffffff", "rgba(0,0,0,0.04)", "rgba(0,0,0,0.09)"
    SCROLL_TH = "rgba(124,58,237,0.35)"

st.markdown(load_css("style.css"), unsafe_allow_html=True)

st.markdown(f"""<style>
::-webkit-scrollbar-thumb {{ background:{SCROLL_TH}; border-radius:99px; }}
.stApp {{ background:{BG} !important; }}
.stTextInput > div > div > input {{ background:{INPUT_BG} !important; border:1.5px solid {BORDER} !important; color:{TEXT} !important; }}
.stTextInput > div > div > input::placeholder {{ color:{MUTED} !important; }}
[data-baseweb="select"] > div {{ background:{INPUT_BG} !important; border:1.5px solid {BORDER} !important; color:{TEXT} !important; }}
[data-baseweb="popover"] ul {{ background:{CARD} !important; border:1px solid {BORDER} !important; }}
[role="option"] {{ color:{TEXT2} !important; }}
div[data-testid="stRadio"] label {{ background:transparent !important; border:none !important; }}
div[data-testid="stRadio"] label p {{ color:{TEXT2} !important; }}
.stButton > button {{ background:{CARD} !important; border:1.5px solid {BORDER} !important; color:{TEXT} !important; }}
.stButton > button p {{ color:{TEXT} !important; -webkit-text-fill-color:{TEXT} !important; }}
.stButton > button:hover {{ background:rgba(124,58,237,.12) !important; border-color:#7c3aed !important; }}
.stButton > button:hover p {{ color:#5b21b6 !important; -webkit-text-fill-color:#5b21b6 !important; }}
.stDownloadButton > button {{ background:{CHIP} !important; border:1.5px solid {CHIP_B} !important; color:{TEXT2} !important; }}
.stTabs [data-baseweb="tab-list"] {{ background:{CARD} !important; border:1px solid {BORDER} !important; }}
.stTabs [data-baseweb="tab"] {{ color:{TEXT2} !important; }}
.stSpinner p {{ color:{TEXT2} !important; }}
.blog {{ color:{TEXT2} !important; }}
.blog h1, .blog h2, .blog h3 {{ color:{TEXT} !important; }}
.blog p, .blog li, .blog td {{ color:{TEXT2} !important; }}
.blog h2 {{ border-bottom:1px solid {BORDER} !important; }}
.blog blockquote {{ background:rgba(124,58,237,.06) !important; color:{MUTED} !important; }}
.blog strong {{ color:{TEXT} !important; }}
.steps-card {{ background:{CARD}; border:1px solid {BORDER}; }}
.steps-line {{ background:{BORDER}; }}
.step-dot {{ background:{CHIP}; border:1.5px solid {CHIP_B}; color:{MUTED}; }}
.step.active .step-dot {{ background:rgba(124,58,237,.2); border-color:#7c3aed; color:#c4b5fd; }}
.step.done .step-dot {{ background:rgba(52,211,153,.15); border-color:#34d399; color:#34d399; }}
.step-lbl {{ color:{MUTED}; }}
.step.active .step-lbl {{ color:#a78bfa; }}
.step.done .step-lbl {{ color:#6ee7b7; }}
.hcard {{ background:{CARD}; border:1px solid {BORDER}; }}
.hcard-title {{ color:{TEXT}; }}
.hcard-chip {{ background:{CHIP}; border:1px solid {CHIP_B}; color:{MUTED}; }}
.hcard-preview {{ color:{TEXT2}; }}
.hcard-img-placeholder {{ background:rgba(124,58,237,.08); }}
</style>""", unsafe_allow_html=True)

# ── HELPERS ──
SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
os.makedirs(SAVE_DIR, exist_ok=True)

def md_to_html(md_text, title="Blog"):
    body = md_lib.markdown(md_text, extensions=["extra", "nl2br"])
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:Georgia,serif;max-width:800px;margin:40px auto;padding:0 20px;line-height:1.8;color:#1a1a1a}}
h1{{font-size:2em}}h2{{font-size:1.4em;margin-top:1.5em}}blockquote{{border-left:4px solid #7c3aed;padding:8px 16px;color:#555}}
code{{background:#f3f0ff;padding:2px 6px;border-radius:4px}}</style></head><body>{body}</body></html>""".encode("utf-8")

def md_to_docx(md_text, title="Blog"):
    doc = Document()
    doc.core_properties.title = title
    for line in md_text.split("\n"):
        line = line.strip()
        if line.startswith("### "): doc.add_heading(line[4:], level=3)
        elif line.startswith("## "): doc.add_heading(line[3:], level=2)
        elif line.startswith("# "): doc.add_heading(line[2:], level=1)
        elif line.startswith(("- ", "* ")): doc.add_paragraph(line[2:], style="List Bullet")
        else: doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def extract_video_id(url):
    for p in [r"(?:v=)([a-zA-Z0-9_-]{11})", r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
              r"(?:embed/)([a-zA-Z0-9_-]{11})", r"(?:shorts/)([a-zA-Z0-9_-]{11})"]:
        m = re.search(p, url)
        if m: return m.group(1)
    return None

def get_thumbnail_url(vid):
    return f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg"

def fetch_transcript(vid):
    ytt = YouTubeTranscriptApi()
    tlist = ytt.list(vid)
    try:
        transcript = tlist.find_transcript(['en','en-US','en-GB','hi','ur'])
    except NoTranscriptFound:
        transcript = next(iter(tlist))
    return transcript.fetch()

def render_steps(active=None, done=None):
    done = done or []
    items = [("1","Transcript"),("2","Context"),("3","Blog"),("4","Cover"),("5","Done")]
    dots = ""
    for num, lbl in items:
        if lbl in done:     cls, sym = "step done",   "✓"
        elif lbl == active: cls, sym = "step active", num
        else:               cls, sym = "step",         num
        dots += f'<div class="{cls}"><div class="step-dot">{sym}</div><div class="step-lbl">{lbl}</div></div>'
    return f'<div class="steps-card"><div class="steps-inner"><div class="steps-line"></div>{dots}</div></div>'

@st.cache_data(ttl=60, show_spinner=False)
def load_history():
    items = []
    for fn in sorted(os.listdir(SAVE_DIR), reverse=True):
        if not fn.endswith(".md"): continue
        path = os.path.join(SAVE_DIR, fn)
        try:
            with open(path, "r", encoding="utf-8") as f: content = f.read()
            title = next((l.lstrip("# ").strip() for l in content.splitlines() if l.startswith("#")), fn)
            ts = fn.replace("blog_", "").replace(".md", "")
            try: ts_label = datetime.datetime.strptime(ts, "%Y%m%d_%H%M%S").strftime("%d %b %Y · %I:%M %p")
            except: ts_label = ts
            img_fn = fn.replace("blog_", "cover_").replace(".md", ".png")
            img_path = os.path.join(SAVE_DIR, img_fn)
            meta_fn = fn.replace("blog_", "meta_").replace(".md", ".json")
            meta_path = os.path.join(SAVE_DIR, meta_fn)
            meta = {}
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as mf: meta = json.load(mf)
            word_count = len(content.split())
            items.append({
                "fn": fn, "path": path, "title": title, "ts_label": ts_label, "ts_raw": ts,
                "content": content, "img_path": img_path if os.path.exists(img_path) else None,
                "img_fn": img_fn, "word_count": word_count,
                "language": meta.get("language", "English"),
                "tone": meta.get("tone", "Professional"),
                "read_time": max(1, word_count // 200),
            })
        except: pass
    return items

@st.cache_data(ttl=300, show_spinner=False)
def get_thumb_b64(img_path):
    try:
        img = Image.open(img_path)
        img.thumbnail((480, 270))
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=70)
        return base64.b64encode(buf.getvalue()).decode()
    except: return ""

def save_meta(ts, language, tone):
    with open(os.path.join(SAVE_DIR, f"meta_{ts}.json"), "w", encoding="utf-8") as f:
        json.dump({"language": language, "tone": tone}, f)

TONE_MAP = {
    "Professional": "formal, authoritative, and polished",
    "Casual & Friendly": "conversational, warm, and approachable",
    "Educational": "clear, informative, and easy to understand",
    "Storytelling": "narrative-driven, engaging, and vivid",
    "Technical": "precise, detailed, and technically accurate",
    "Persuasive": "compelling, motivating, and action-oriented",
}

# ── NAVBAR ──
if not GEMINI_API_KEY:
    st.error("⚠️ GEMINI_API_KEY not found in .env file.")
    st.stop()

hist_count = len([f for f in os.listdir(SAVE_DIR) if f.endswith(".md")])
is_gen  = st.session_state.page == "generate"
is_hist = st.session_state.page == "history"

logo_col, c_gen, c_hist, c_theme = st.columns([2.5, 1, 1, 1])

with logo_col:
    logo_path = os.path.join(os.path.dirname(__file__), "Prabisha_logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as lf:
            logo_b64 = base64.b64encode(lf.read()).decode()
        st.markdown(
            f'<div style="display:flex;align-items:center;height:38px">'
            f'<a href="https://www.prabisha.com/" target="_blank" style="display:inline-flex;align-items:center">'
            f'<img src="data:image/png;base64,{logo_b64}" style="height:48px;object-fit:contain;{"filter:brightness(0) invert(1)" if dark else ""}">'
            f'</a></div>',
            unsafe_allow_html=True)
    else:
        st.markdown('<span style="font-size:16px;font-weight:800;color:#7c3aed">VidBlog AI</span>', unsafe_allow_html=True)

with c_gen:
    if st.button("✨ Generate", key="nav_gen", use_container_width=True,
                 type="primary" if is_gen else "secondary"):
        st.session_state.page = "generate"; st.rerun()

with c_hist:
    if st.button(f"📂 History ({hist_count})", key="nav_hist", use_container_width=True,
                 type="primary" if is_hist else "secondary"):
        st.session_state.page = "history"; st.rerun()

with c_theme:
    label = "☀️ Light" if dark else "🌙 Dark"
    if st.button(label, key="nav_theme", use_container_width=True):
        st.session_state.dark_mode = not dark; st.rerun()

st.markdown(f'<div style="height:1px;background:{BORDER};margin:6px 0 16px"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════
#  PAGE: HISTORY
# ══════════════════════════════════════════
if st.session_state.page == "history":
    history = load_history()

    if not history:
        st.markdown(f'<div style="font-size:20px;font-weight:800;color:{TEXT};margin-bottom:4px">📂 Blog History</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center;padding:60px 24px;color:{MUTED};font-size:14px">📭 No blogs yet. Generate your first one!</div>', unsafe_allow_html=True)

    # ── DETAIL VIEW ──
    elif st.session_state.view_blog:
        vb = st.session_state.view_blog

        # reload content from disk in case it was edited
        if os.path.exists(vb["path"]):
            with open(vb["path"], "r", encoding="utf-8") as f:
                vb["content"] = f.read()

        col_back, col_title = st.columns([1, 5])
        with col_back:
            if st.button("← Back", key="back_hist", use_container_width=True):
                st.session_state.view_blog = None
                st.session_state.pop("edit_mode", None)
                st.rerun()
        with col_title:
            st.markdown(f'<div style="font-size:17px;font-weight:800;color:{TEXT};padding-top:6px">{vb["title"][:70]}</div>', unsafe_allow_html=True)

        st.markdown(f'<div style="display:flex;gap:5px;flex-wrap:wrap;margin:10px 0 16px">'
                    f'<span style="background:{CHIP};border:1px solid {CHIP_B};color:{MUTED};padding:2px 9px;border-radius:100px;font-size:10px">✍️ {vb["word_count"]:,} words</span>'
                    f'<span style="background:{CHIP};border:1px solid {CHIP_B};color:{MUTED};padding:2px 9px;border-radius:100px;font-size:10px">⏱️ ~{vb["read_time"]} min</span>'
                    f'<span style="background:{CHIP};border:1px solid {CHIP_B};color:{MUTED};padding:2px 9px;border-radius:100px;font-size:10px">🌐 {vb["language"]}</span>'
                    f'<span style="background:{CHIP};border:1px solid {CHIP_B};color:{MUTED};padding:2px 9px;border-radius:100px;font-size:10px">🕐 {vb["ts_label"]}</span>'
                    f'</div>', unsafe_allow_html=True)

        # action buttons row
        _hbase = vb["fn"].replace(".md", "")
        ba1, ba2, ba3, ba4, ba5 = st.columns([0.5, 1, 1, 1, 0.5])
        with ba1:
            edit_label = "💾" if st.session_state.get("edit_mode") else "✏️"
            if st.button(edit_label, key="btn_edit", use_container_width=True):
                if st.session_state.get("edit_mode"):
                    new_content = st.session_state.get("edit_content", vb["content"])
                    with open(vb["path"], "w", encoding="utf-8") as f:
                        f.write(new_content)
                    vb["content"] = new_content
                    st.session_state.view_blog = vb
                    load_history.clear()
                    st.session_state.edit_mode = False
                    st.success("Saved!")
                else:
                    st.session_state.edit_mode = True
                st.rerun()
        with ba2:
            if st.session_state.get("edit_mode"):
                if st.button("❌", key="btn_cancel", use_container_width=True):
                    st.session_state.edit_mode = False; st.rerun()
            else:
                st.download_button("📄 .md", data=vb["content"], file_name=vb["fn"],
                                   mime="text/markdown", use_container_width=True, key="hist_dl_md")
        with ba3:
            st.download_button("🌐 .html", data=md_to_html(vb["content"], _hbase),
                               file_name=_hbase+".html", mime="text/html",
                               use_container_width=True, key="hist_dl_html")
        with ba4:
            st.download_button("📝 .docx", data=md_to_docx(vb["content"], _hbase),
                               file_name=_hbase+".docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               use_container_width=True, key="hist_dl_docx")
        with ba5:
            if st.button("🗑️", key="btn_del", use_container_width=True):
                st.session_state.confirm_delete = True
                st.rerun()

        # confirm delete
        if st.session_state.get("confirm_delete"):
            st.warning("Are you sure you want to delete this blog?")
            cy, cn = st.columns(2)
            with cy:
                if st.button("Yes, delete", key="confirm_yes", use_container_width=True):
                    try:
                        os.remove(vb["path"])
                        if vb["img_path"] and os.path.exists(vb["img_path"]): os.remove(vb["img_path"])
                        meta_path = vb["path"].replace("blog_", "meta_").replace(".md", ".json")
                        if os.path.exists(meta_path): os.remove(meta_path)
                        load_history.clear(); get_thumb_b64.clear()
                        st.session_state.view_blog = None
                        st.session_state.confirm_delete = False
                        st.rerun()
                    except Exception as de:
                        st.error(f"Delete failed: {de}")
            with cn:
                if st.button("Cancel", key="confirm_no", use_container_width=True):
                    st.session_state.confirm_delete = False; st.rerun()

        st.markdown(f'<div style="height:1px;background:{BORDER};margin:10px 0 14px"></div>', unsafe_allow_html=True)

        if st.session_state.get("edit_mode"):
            edited = st.text_area("Edit Blog", value=vb["content"], height=600,
                                  label_visibility="collapsed", key="edit_content")
        else:
            if vb["img_path"] and os.path.exists(vb["img_path"]):
                st.image(vb["img_path"], use_container_width=True)
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            # copy + share buttons
            import urllib.parse
            share_title = urllib.parse.quote(vb["title"])
            blog_link = f"{APP_URL}?blog={urllib.parse.quote(vb['fn'])}"
            wa_url  = f"https://wa.me/?text={share_title}%20-%20{urllib.parse.quote(blog_link)}"
            tw_url  = f"https://twitter.com/intent/tweet?text={share_title}&url={urllib.parse.quote(blog_link)}"
            li_url  = f"https://www.linkedin.com/sharing/share-offsite/?url={urllib.parse.quote(blog_link)}"

            import streamlit.components.v1 as components
            components.html(f"""
            <script>
            function copyBlog() {{
                const text = {repr(vb["content"])};
                navigator.clipboard.writeText(text).then(() => {{
                    const btn = document.getElementById('copybtn');
                    btn.innerText = '✅ Copied!';
                    setTimeout(() => btn.innerText = '📋 Copy Blog', 2000);
                }});
            }}
            function copyLink() {{
                navigator.clipboard.writeText("{blog_link}").then(() => {{
                    const btn = document.getElementById('linkbtn');
                    btn.innerText = '✅ Link Copied!';
                    setTimeout(() => btn.innerText = '🔗 Copy Link', 2000);
                }});
            }}
            </script>
            <div style="display:flex;gap:8px;flex-wrap:wrap;font-family:Inter,sans-serif">
              <button id="copybtn" onclick="copyBlog()"
                style="background:#f1f5f9;border:1.5px solid #e2e8f0;color:#475569;padding:6px 14px;
                       border-radius:8px;font-size:12px;font-weight:600;cursor:pointer">
                📋 Copy Blog
              </button>
              <button id="linkbtn" onclick="copyLink()"
                style="background:#f1f5f9;border:1.5px solid #e2e8f0;color:#475569;padding:6px 14px;
                       border-radius:8px;font-size:12px;font-weight:600;cursor:pointer">
                🔗 Copy Link
              </button>
              <a href="{wa_url}" target="_blank"
                style="background:#25D366;color:#fff;padding:6px 14px;border-radius:8px;
                       font-size:12px;font-weight:600;text-decoration:none">
                💬 WhatsApp
              </a>
              <a href="{tw_url}" target="_blank"
                style="background:#1DA1F2;color:#fff;padding:6px 14px;border-radius:8px;
                       font-size:12px;font-weight:600;text-decoration:none">
                🐦 Twitter
              </a>
              <a href="{li_url}" target="_blank"
                style="background:#0A66C2;color:#fff;padding:6px 14px;border-radius:8px;
                       font-size:12px;font-weight:600;text-decoration:none">
                💼 LinkedIn
              </a>
            </div>
            """, height=55)

            tab_preview, tab_raw = st.tabs(["📖 Preview", "📝 Raw Markdown"])
            with tab_preview:
                st.markdown('<div class="blog">', unsafe_allow_html=True)
                st.markdown(vb["content"])
                st.markdown('</div>', unsafe_allow_html=True)
            with tab_raw:
                st.code(vb["content"], language="markdown")

    # ── GRID VIEW ──
    else:
        st.markdown(f'<div style="font-size:20px;font-weight:800;color:{TEXT};margin-bottom:4px">📂 Blog History</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:13px;color:{TEXT2};margin-bottom:16px">{len(history)} blog{"s" if len(history)!=1 else ""} saved in <code>outputs/</code></div>', unsafe_allow_html=True)

        # hide card buttons visually — show only on hover via CSS
        st.markdown(f"""<style>
        .card-btn-wrap {{ margin-top:-8px; }}
        .card-btn-wrap .stButton > button {{
            background:transparent !important; border:none !important;
            padding:0 !important; height:0 !important; overflow:hidden !important;
            position:absolute !important; opacity:0 !important;
        }}
        </style>""", unsafe_allow_html=True)

        HIST_PAGE_SIZE = 10
        if "hist_page" not in st.session_state: st.session_state.hist_page = 0
        total = len(history)
        total_pages = max(1, (total + HIST_PAGE_SIZE - 1) // HIST_PAGE_SIZE)
        if st.session_state.hist_page >= total_pages: st.session_state.hist_page = total_pages - 1
        page_items = history[st.session_state.hist_page * HIST_PAGE_SIZE:(st.session_state.hist_page + 1) * HIST_PAGE_SIZE]

        # render cards in 2-column grid using st.columns so buttons work
        for row_start in range(0, len(page_items), 2):
            row_items = page_items[row_start:row_start+2]
            cols = st.columns(2, gap="medium")
            for col, item in zip(cols, row_items):
                with col:
                    if item["img_path"]:
                        b64 = get_thumb_b64(item["img_path"])
                        img_html = f'<img class="hcard-img" src="data:image/webp;base64,{b64}" alt="cover">' if b64 else '<div class="hcard-img-placeholder">📝</div>'
                    else:
                        img_html = '<div class="hcard-img-placeholder">📝</div>'
                    short_title = (item["title"][:55] + "…") if len(item["title"]) > 55 else item["title"]
                    preview = item["content"][:140].replace('<','&lt;').replace('>','&gt;').replace('\n',' ')
                    st.markdown(f"""
                    <div class="hcard" style="margin-bottom:4px">
                      {img_html}
                      <div class="hcard-body">
                        <div class="hcard-title">{short_title}</div>
                        <div class="hcard-meta">
                          <span class="hcard-chip">🕐 {item["ts_label"]}</span>
                          <span class="hcard-chip">🌐 {item["language"]}</span>
                          <span class="hcard-chip">⏱️ {item["read_time"]}m</span>
                        </div>
                        <div class="hcard-preview">{preview}…</div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                    if st.button("Open", key=f"open_{item['fn']}", use_container_width=True):
                        st.session_state.view_blog = item
                        st.session_state.edit_mode = False
                        st.session_state.confirm_delete = False
                        st.rerun()

        if total_pages > 1:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            pg1, pg2, pg3 = st.columns([1, 2, 1])
            with pg1:
                if st.button("← Prev", disabled=st.session_state.hist_page == 0, use_container_width=True, key="hist_prev"):
                    st.session_state.hist_page -= 1; st.rerun()
            with pg2:
                st.markdown(f'<div style="text-align:center;color:{MUTED};font-size:12px;padding-top:8px">Page {st.session_state.hist_page+1} of {total_pages}</div>', unsafe_allow_html=True)
            with pg3:
                if st.button("Next →", disabled=st.session_state.hist_page >= total_pages-1, use_container_width=True, key="hist_next"):
                    st.session_state.hist_page += 1; st.rerun()

    st.stop()

# ══════════════════════════════════════════
#  PAGE: GENERATE
# ══════════════════════════════════════════
st.markdown(f'<div style="text-align:center;margin-bottom:20px">'
            f'<div style="font-size:26px;font-weight:900;margin-bottom:10px">'
            f'<span style="background:linear-gradient(90deg,#7c3aed,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent">YouTube</span>'
            f' <span style="color:{TEXT}">to Blog Post</span></div>'
            f'<div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap">'
            f'<span style="background:rgba(124,58,237,.1);border:1px solid rgba(124,58,237,.25);color:#7c3aed;padding:4px 12px;border-radius:100px;font-size:11px;font-weight:700">✍️ Auto Blog Generation</span>'
            f'<span style="background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.25);color:#3b82f6;padding:4px 12px;border-radius:100px;font-size:11px;font-weight:700">� 10+ Languages</span>'
            f'<span style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);color:#10b981;padding:4px 12px;border-radius:100px;font-size:11px;font-weight:700">🎨 AI Cover Image</span>'
            f'</div>'
            f'</div>', unsafe_allow_html=True)

left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    st.markdown(f'<div style="font-size:13px;font-weight:600;color:{TEXT};margin-bottom:6px">🔗 YouTube Video URL</div>', unsafe_allow_html=True)
    video_url = st.text_input("YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...",
                               label_visibility="collapsed", key="video_url_input")

    if video_url.strip():
        vid_preview = extract_video_id(video_url.strip())
        if vid_preview:
            st.markdown(f'<img src="{get_thumbnail_url(vid_preview)}" onerror="this.style.display=\'none\'" '
                        f'style="width:100%;border-radius:10px;margin:8px 0 14px;display:block">', unsafe_allow_html=True)

    st.markdown(f'<div style="color:{MUTED};font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin:16px 0 10px">⚙️ Customize</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:13px;font-weight:600;color:{TEXT};margin-bottom:6px">🌐 Language</div>', unsafe_allow_html=True)
    blog_language = st.radio("Language",
        ["English","Urdu","Hindi","French","Spanish","Arabic","German","Portuguese","Turkish","Bengali"],
        horizontal=True, label_visibility="collapsed", key="lang_radio")

    st.markdown(f'<div style="font-size:13px;font-weight:600;color:{TEXT};margin:14px 0 6px">🎨 Tone</div>', unsafe_allow_html=True)
    blog_tone = st.radio("Tone",
        ["Professional","Casual & Friendly","Educational","Storytelling","Technical","Persuasive"],
        horizontal=True, label_visibility="collapsed", key="tone_radio")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    generate_btn = st.button("🚀 Generate Blog Post", use_container_width=True, key="gen_btn", type="primary")

with right_col:
    steps_ph = st.empty()

    if generate_btn:
        if not video_url.strip():
            st.warning("⚠️ Please enter a video URL first.")
        else:
            vid = extract_video_id(video_url)
            if not vid:
                st.error("❌ Couldn't extract video ID. Please check the URL.")
            else:
                try:
                    with st.spinner("📥 Fetching transcript..."):
                        steps_ph.markdown(render_steps(active="Transcript"), unsafe_allow_html=True)
                        data = fetch_transcript(vid)
                        full_text = " ".join([e.text for e in data])

                    with st.spinner("🧠 Building semantic context..."):
                        steps_ph.markdown(render_steps(active="Context", done=["Transcript"]), unsafe_allow_html=True)
                        splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
                        docs = splitter.create_documents([full_text])
                        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=GEMINI_API_KEY)
                        vectorstore = FAISS.from_documents(docs, embeddings)
                        retriever = vectorstore.as_retriever(search_kwargs={"k": 6})

                    with st.spinner("✍️ Writing blog..."):
                        steps_ph.markdown(render_steps(active="Blog", done=["Transcript","Context"]), unsafe_allow_html=True)
                        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.75)
                        ctx_docs = retriever.invoke("main topics, key insights, important points")
                        context  = "\n\n".join([d.page_content for d in ctx_docs])
                        tone_desc = TONE_MAP.get(blog_tone, "professional")
                        prompt = f"""You are an expert blog writer. Write a high-quality blog post in **{blog_language}** with a **{tone_desc}** tone.

Source material:
---
{context}
---

Structure:
1. Compelling SEO-friendly title (# heading)
2. Hook introduction (2-3 paragraphs)
3. 4-5 sections with ## headings and ### sub-headings where needed
4. Key takeaways with bullet points
5. Strong conclusion with call-to-action

Requirements:
- Write entirely in {blog_language}
- Use proper Markdown formatting
- Minimum 700 words
- Do NOT mention this is based on a YouTube video
- Make it engaging and publication-ready
- At the very end, add a line of 5-7 relevant hashtags (e.g. #AI #Technology #Innovation)"""
                        response = llm.invoke(prompt)
                        blog_content = response.content

                    cover_image = None
                    with st.spinner("🎨 Generating cover image..."):
                        steps_ph.markdown(render_steps(active="Cover", done=["Transcript","Context","Blog"]), unsafe_allow_html=True)
                        try:
                            title_match = re.search(r'^#\s+(.+)', blog_content, re.MULTILINE)
                            blog_title = title_match.group(1) if title_match else "Blog Post"
                            gc = genai.Client(api_key=GEMINI_API_KEY)
                            img_resp = gc.models.generate_images(
                                model="imagen-4.0-generate-001",
                                prompt=f"Professional modern blog cover for: '{blog_title}'. Cinematic lighting, clean composition, no text.",
                                config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9")
                            )
                            cover_image = Image.open(io.BytesIO(img_resp.generated_images[0].image.image_bytes))
                        except Exception as ie:
                            st.warning(f"⚠️ Cover image skipped: {ie}")

                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    blog_fn = f"blog_{ts}.md"
                    with open(os.path.join(SAVE_DIR, blog_fn), "w", encoding="utf-8") as f:
                        f.write(blog_content)
                    save_meta(ts, blog_language, blog_tone)
                    load_history.clear()

                    cover_bytes, img_fn = None, None
                    if cover_image:
                        img_fn = f"cover_{ts}.png"
                        cover_image.save(os.path.join(SAVE_DIR, img_fn), format="PNG")
                        buf = io.BytesIO()
                        cover_image.save(buf, format="PNG")
                        cover_bytes = buf.getvalue()

                    st.session_state.blog_content  = blog_content
                    st.session_state.cover_bytes   = cover_bytes
                    st.session_state.blog_filename = blog_fn
                    st.session_state.img_filename  = img_fn
                    st.session_state.word_count    = len(blog_content.split())
                    st.session_state.blog_language = blog_language
                    st.session_state.blog_tone     = blog_tone
                    steps_ph.markdown(render_steps(done=["Transcript","Context","Blog","Cover","Done"]), unsafe_allow_html=True)

                except TranscriptsDisabled:
                    steps_ph.markdown(render_steps(), unsafe_allow_html=True)
                    st.error("🚫 Transcripts are disabled for this video.")
                except NoTranscriptFound:
                    steps_ph.markdown(render_steps(), unsafe_allow_html=True)
                    st.error("❌ No transcript found for this video.")
                except Exception as e:
                    steps_ph.markdown(render_steps(), unsafe_allow_html=True)
                    st.error(f"⚠️ Something went wrong: {e}")

    # ── RESULT ──
    if st.session_state.blog_content:
        bc  = st.session_state.blog_content
        cb  = st.session_state.cover_bytes
        bf  = st.session_state.blog_filename
        imf = st.session_state.img_filename
        bw  = len(bc.split())
        rt  = max(1, bw // 200)
        bl  = st.session_state.blog_language
        bt  = st.session_state.blog_tone

        # extract title + description
        lines = [l.strip() for l in bc.splitlines() if l.strip()]
        blog_title = next((l.lstrip("# ") for l in lines if l.startswith("#")), "Blog Post")
        desc_lines = [l for l in lines if not l.startswith("#") and len(l) > 40]
        description = desc_lines[0][:200] + "…" if desc_lines else ""

        # build html for new-tab preview
        _base = bf.replace(".md", "")
        html_bytes = md_to_html(bc, _base)
        html_b64 = base64.b64encode(html_bytes).decode()

        # cover image
        if cb:
            cover_src = f"data:image/png;base64,{base64.b64encode(cb).decode()}"
        elif st.session_state.get("video_url_input"):
            vid_id = extract_video_id(st.session_state.video_url_input)
            cover_src = get_thumbnail_url(vid_id) if vid_id else ""
        else:
            cover_src = ""

        st.markdown(f"""
        <div style="background:{CARD};border:1px solid {BORDER};border-radius:14px;overflow:hidden;margin-top:8px">
          {"" if not cover_src else f'<img src="{cover_src}" style="width:100%;aspect-ratio:16/9;object-fit:cover;display:block">'}
          <div style="padding:16px 18px 18px">
            <div style="font-size:16px;font-weight:800;color:{TEXT};line-height:1.35;margin-bottom:8px">{blog_title}</div>
            <div style="font-size:12px;color:{TEXT2};line-height:1.7;margin-bottom:12px">{description}</div>
            <div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:14px">
              <span style="background:{CHIP};border:1px solid {CHIP_B};color:{MUTED};padding:2px 9px;border-radius:100px;font-size:10px">✍️ {bw:,} words</span>
              <span style="background:{CHIP};border:1px solid {CHIP_B};color:{MUTED};padding:2px 9px;border-radius:100px;font-size:10px">⏱️ ~{rt} min read</span>
              <span style="background:{CHIP};border:1px solid {CHIP_B};color:{MUTED};padding:2px 9px;border-radius:100px;font-size:10px">🌐 {bl}</span>
              <span style="background:{CHIP};border:1px solid {CHIP_B};color:{MUTED};padding:2px 9px;border-radius:100px;font-size:10px">🎨 {bt}</span>
            </div>
            <a href="data:text/html;base64,{html_b64}" download="{_base}.html" target="_blank"
               style="display:inline-block;background:linear-gradient(135deg,#7c3aed,#4f46e5);color:#fff;
                      text-decoration:none;padding:9px 20px;border-radius:8px;font-size:13px;font-weight:700">
              📖 Read Full Blog
            </a>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div style="height:1px;background:{BORDER};margin:14px 0 10px"></div>', unsafe_allow_html=True)
        if cb:
            d1, d2, d3, d4 = st.columns(4)
            with d1: st.download_button("📄 .md",   data=bc,                    file_name=bf,           mime="text/markdown",  use_container_width=True, key="dl_blog")
            with d2: st.download_button("🌐 .html", data=html_bytes,            file_name=_base+".html", mime="text/html",       use_container_width=True, key="dl_html")
            with d3: st.download_button("📝 .docx", data=md_to_docx(bc, _base), file_name=_base+".docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True, key="dl_docx")
            with d4: st.download_button("🖼️ .png",  data=cb,                    file_name=imf,           mime="image/png",       use_container_width=True, key="dl_img")
        else:
            d1, d2, d3 = st.columns(3)
            with d1: st.download_button("📄 .md",   data=bc,                    file_name=bf,           mime="text/markdown",  use_container_width=True, key="dl_blog")
            with d2: st.download_button("🌐 .html", data=html_bytes,            file_name=_base+".html", mime="text/html",       use_container_width=True, key="dl_html")
            with d3: st.download_button("📝 .docx", data=md_to_docx(bc, _base), file_name=_base+".docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True, key="dl_docx")

    else:
        st.markdown(f"""
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
             min-height:480px;background:{CARD};border:1.5px dashed {BORDER};border-radius:14px;
             text-align:center;padding:32px">
          <div style="font-size:36px;margin-bottom:14px">📝</div>
          <div style="color:{TEXT};font-size:15px;font-weight:700;margin-bottom:8px">Your blog will appear here</div>
          <div style="color:{MUTED};font-size:12px;line-height:1.75;max-width:240px">
            Paste a YouTube URL, choose language &amp; tone, then hit Generate.
          </div>
        </div>""", unsafe_allow_html=True)

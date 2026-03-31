import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import re
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

st.set_page_config(
    page_title="VidBlog AI – YouTube to Blog",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    box-sizing: border-box;
}

.stApp {
    background: #0a0a0f;
    min-height: 100vh;
}

#MainMenu, footer, header { visibility: hidden; }

.block-container {
    padding: 0 1.5rem 5rem !important;
    max-width: 820px !important;
    margin: 0 auto;
}

/* ── HERO ── */
.hero {
    text-align: center;
    padding: 56px 0 40px;
}

.logo-wrap {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 100px;
    padding: 8px 22px 8px 8px;
    margin-bottom: 36px;
}

.logo-icon {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, #8b5cf6, #3b82f6);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 16px rgba(139,92,246,0.4);
}

.logo-text {
    font-size: 17px;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.3px;
}

.logo-text span {
    background: linear-gradient(90deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(139,92,246,0.1);
    border: 1px solid rgba(139,92,246,0.25);
    color: #c4b5fd;
    padding: 5px 16px;
    border-radius: 100px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-bottom: 28px;
}

.hero-title {
    font-size: 58px;
    font-weight: 900;
    color: #fff;
    line-height: 1.1;
    letter-spacing: -2px;
    margin-bottom: 20px;
}

.hero-title .g1 { background: linear-gradient(90deg, #a78bfa, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero-title .g2 { background: linear-gradient(90deg, #60a5fa, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

.hero-sub {
    color: #64748b;
    font-size: 16px;
    max-width: 480px;
    margin: 0 auto 12px;
    line-height: 1.8;
    font-weight: 400;
}

.model-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(52,211,153,0.08);
    border: 1px solid rgba(52,211,153,0.2);
    color: #6ee7b7;
    padding: 4px 14px;
    border-radius: 100px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-top: 8px;
}

/* ── STEPS ── */
.steps-row {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0;
    margin: 0 auto 40px;
    max-width: 520px;
}

.step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    flex: 1;
    position: relative;
}

.step-item:not(:last-child)::after {
    content: '';
    position: absolute;
    top: 16px;
    left: calc(50% + 16px);
    right: calc(-50% + 16px);
    height: 1px;
    background: rgba(255,255,255,0.08);
}

.step-item.done:not(:last-child)::after {
    background: rgba(52,211,153,0.4);
}

.step-circle {
    width: 32px; height: 32px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px;
    background: rgba(255,255,255,0.04);
    border: 1.5px solid rgba(255,255,255,0.1);
    color: #475569;
    font-weight: 600;
    transition: all 0.3s;
    z-index: 1;
}

.step-item.active .step-circle {
    background: rgba(139,92,246,0.2);
    border-color: #8b5cf6;
    color: #c4b5fd;
    box-shadow: 0 0 16px rgba(139,92,246,0.3);
}

.step-item.done .step-circle {
    background: rgba(52,211,153,0.15);
    border-color: #34d399;
    color: #34d399;
}

.step-label {
    font-size: 11px;
    font-weight: 500;
    color: #334155;
    text-align: center;
    white-space: nowrap;
}

.step-item.active .step-label { color: #a78bfa; }
.step-item.done .step-label { color: #6ee7b7; }

/* ── FORM CARD ── */
.form-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 28px;
    padding: 36px;
    backdrop-filter: blur(20px);
    box-shadow: 0 24px 80px rgba(0,0,0,0.4);
}

.field-label {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #94a3b8;
    font-size: 12.5px;
    font-weight: 600;
    margin-bottom: 10px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

.divider {
    height: 1px;
    background: rgba(255,255,255,0.06);
    margin: 24px 0;
}

/* ── INPUT OVERRIDES ── */
.stTextInput > div > div > input {
    background: rgba(10,10,20,0.8) !important;
    border: 1.5px solid rgba(255,255,255,0.08) !important;
    border-radius: 16px !important;
    color: #f1f5f9 !important;
    padding: 15px 20px !important;
    font-size: 15px !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 4px rgba(139,92,246,0.12) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: #334155 !important; }
.stTextInput label { display: none !important; }

.stSelectbox label {
    color: #94a3b8 !important;
    font-size: 12.5px !important;
    font-weight: 600 !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
}
.stSelectbox > div > div {
    background: rgba(10,10,20,0.8) !important;
    border: 1.5px solid rgba(255,255,255,0.08) !important;
    border-radius: 16px !important;
    color: #f1f5f9 !important;
}
.stSelectbox > div > div:focus-within {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 4px rgba(139,92,246,0.12) !important;
}

/* ── GENERATE BUTTON ── */
.stButton > button {
    background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 16px !important;
    padding: 16px 28px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    width: 100% !important;
    margin-top: 8px !important;
    box-shadow: 0 8px 32px rgba(139,92,246,0.35) !important;
    transition: all 0.2s !important;
    letter-spacing: 0.3px !important;
    font-family: 'Inter', sans-serif !important;
}
.stButton > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 14px 40px rgba(139,92,246,0.45) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── RESULT CARD ── */
.result-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 28px;
    padding-bottom: 20px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}

.result-icon {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, #8b5cf6, #3b82f6);
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    box-shadow: 0 4px 16px rgba(139,92,246,0.3);
}

.result-title {
    font-size: 18px;
    font-weight: 700;
    color: #f1f5f9;
}

.result-sub {
    font-size: 13px;
    color: #475569;
    margin-top: 2px;
}

.result-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 28px;
    padding: 36px;
    margin-top: 32px;
    box-shadow: 0 24px 80px rgba(0,0,0,0.3);
}

.result-card h1, .result-card h2, .result-card h3 {
    color: #f1f5f9 !important;
    letter-spacing: -0.5px;
}
.result-card h1 { font-size: 28px !important; font-weight: 800 !important; margin-bottom: 16px !important; }
.result-card h2 { font-size: 20px !important; font-weight: 700 !important; margin-top: 32px !important; }
.result-card h3 { font-size: 17px !important; font-weight: 600 !important; }
.result-card p, .result-card li { color: #94a3b8 !important; line-height: 1.9 !important; font-size: 15px !important; }
.result-card strong { color: #e2e8f0 !important; }
.result-card hr { border-color: rgba(255,255,255,0.07) !important; margin: 28px 0 !important; }
.result-card blockquote {
    border-left: 3px solid #8b5cf6 !important;
    padding-left: 16px !important;
    color: #64748b !important;
    font-style: italic !important;
}

/* ── DOWNLOAD BUTTON ── */
.stDownloadButton > button {
    background: rgba(52,211,153,0.08) !important;
    border: 1.5px solid rgba(52,211,153,0.25) !important;
    color: #6ee7b7 !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 13px 24px !important;
    width: 100% !important;
    margin-top: 28px !important;
    transition: all 0.2s !important;
    font-family: 'Inter', sans-serif !important;
}
.stDownloadButton > button:hover {
    background: rgba(52,211,153,0.15) !important;
    border-color: rgba(52,211,153,0.4) !important;
    transform: translateY(-1px) !important;
}

/* ── ALERTS ── */
.stAlert {
    border-radius: 16px !important;
    border: none !important;
}

/* ── SPINNER ── */
.stSpinner > div {
    border-top-color: #8b5cf6 !important;
}

/* ── SUCCESS ── */
.stSuccess {
    background: rgba(52,211,153,0.08) !important;
    border: 1px solid rgba(52,211,153,0.2) !important;
    border-radius: 16px !important;
    color: #6ee7b7 !important;
}

/* ── STATS ROW ── */
.stats-row {
    display: flex;
    gap: 12px;
    margin-top: 24px;
    flex-wrap: wrap;
}

.stat-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 100px;
    padding: 6px 14px;
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
}

.stat-chip span { color: #94a3b8; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ── HERO ──
st.markdown("""
<div class="hero">
    <div style="display:flex;justify-content:center;margin-bottom:36px;">
        <div class="logo-wrap">
            <div class="logo-icon">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <polygon points="5,3 5,17 17,10" fill="white"/>
                </svg>
            </div>
            <span class="logo-text">VidBlog <span>AI</span></span>
        </div>
    </div>
    <div class="badge">✦ &nbsp;AI POWERED</div>
    <div class="hero-title">
        <span class="g1">YouTube</span> to<br><span class="g2">Blog Post</span>
    </div>
    <p class="hero-sub">
        Paste any YouTube URL and get a fully structured,
        publication-ready blog post in seconds.
    </p>
    <div style="display:flex;justify-content:center;margin-top:16px;">
        <div class="model-tag">⚡ Powered by Gemini 2.5 Flash</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── STEP TRACKER ──
def render_steps(active=None, done_list=None):
    done_list = done_list or []
    steps = [
        ("1", "Fetch Transcript"),
        ("2", "Build Context"),
        ("3", "Generate Blog"),
        ("4", "Ready"),
    ]
    html = '<div class="steps-row">'
    for num, label in steps:
        if label in done_list:
            cls = "step-item done"
            circle_content = "✓"
        elif label == active:
            cls = "step-item active"
            circle_content = num
        else:
            cls = "step-item"
            circle_content = num
        html += f'''
        <div class="{cls}">
            <div class="step-circle">{circle_content}</div>
            <div class="step-label">{label}</div>
        </div>'''
    html += '</div>'
    return html


steps_ph = st.empty()
steps_ph.markdown(render_steps(), unsafe_allow_html=True)


# ── FORM ──
st.markdown('<div class="form-card">', unsafe_allow_html=True)

st.markdown("""
<div class="field-label">
    <svg width="16" height="12" viewBox="0 0 16 12" fill="none">
        <rect width="16" height="12" rx="2.5" fill="#FF0000"/>
        <polygon points="6.5,2.5 6.5,9.5 12,6" fill="white"/>
    </svg>
    YouTube Video URL
</div>
""", unsafe_allow_html=True)

video_url = st.text_input(
    "url",
    placeholder="https://www.youtube.com/watch?v=...",
    label_visibility="collapsed"
)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    blog_language = st.selectbox(
        "Blog Language",
        ["English", "Urdu", "Hindi", "French", "Spanish", "Arabic", "German", "Portuguese"],
    )
with col2:
    blog_tone = st.selectbox(
        "Writing Tone",
        ["Professional", "Casual & Friendly", "Educational", "Storytelling", "Technical"],
    )

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

generate_btn = st.button("🚀  Generate Blog Post", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)


# ── HELPERS ──
def extract_video_id(url: str):
    patterns = [
        r"(?:v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/)([a-zA-Z0-9_-]{11})",
        r"(?:shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


# ── MAIN LOGIC ──
if generate_btn:
    if not video_url.strip():
        st.warning("⚠️ Please enter a YouTube URL first.")
    else:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.error("❌ Couldn't extract video ID. Double-check the URL.")
        else:
            try:
                # Step 1 — Transcript
                with st.spinner("📥 Fetching transcript..."):
                    steps_ph.markdown(render_steps(active="Fetch Transcript"), unsafe_allow_html=True)
                    ytt_api = YouTubeTranscriptApi()
                    transcript_list = ytt_api.list(video_id)
                    transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB', 'hi', 'ur'])
                    data = transcript.fetch()
                    full_text = " ".join([entry.text for entry in data])
                    word_count = len(full_text.split())

                # Step 2 — Embeddings + Vector Store
                with st.spinner("🧠 Building semantic context..."):
                    steps_ph.markdown(render_steps(active="Build Context", done_list=["Fetch Transcript"]), unsafe_allow_html=True)
                    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
                    docs = splitter.create_documents([full_text])
                    embeddings = GoogleGenerativeAIEmbeddings(
                        model="models/gemini-embedding-001",
                        google_api_key=GEMINI_API_KEY
                    )
                    vectorstore = FAISS.from_documents(docs, embeddings)
                    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})

                # Step 3 — Blog Generation with Gemini 2.5 Flash
                with st.spinner("✍️ Writing your blog with Gemini 2.5 Flash..."):
                    steps_ph.markdown(render_steps(active="Generate Blog", done_list=["Fetch Transcript", "Build Context"]), unsafe_allow_html=True)

                    llm = ChatGoogleGenerativeAI(
                        model="gemini-2.5-flash",
                        google_api_key=GEMINI_API_KEY,
                        temperature=0.75,
                    )

                    context_docs = retriever.invoke("main topics, key insights, and important points")
                    context = "\n\n".join([doc.page_content for doc in context_docs])

                    tone_map = {
                        "Professional": "formal, authoritative, and polished",
                        "Casual & Friendly": "conversational, warm, and approachable",
                        "Educational": "clear, informative, and easy to understand",
                        "Storytelling": "narrative-driven, engaging, and vivid",
                        "Technical": "precise, detailed, and technically accurate",
                    }
                    tone_desc = tone_map.get(blog_tone, "professional")

                    prompt = f"""You are an expert blog writer. Write a high-quality, engaging blog post in **{blog_language}** language with a **{tone_desc}** tone.

Use the following video transcript content as your source material:

---
{context}
---

Structure the blog post with:
1. A compelling, SEO-friendly title (use # heading)
2. A hook introduction that grabs attention (2-3 paragraphs)
3. 4-5 well-developed sections with descriptive ## headings
4. Key takeaways or bullet points where appropriate
5. A strong, memorable conclusion with a call-to-action

Requirements:
- Write entirely in {blog_language}
- Tone: {tone_desc}
- Use proper Markdown formatting (headings, bold, bullet points, blockquotes)
- Make it feel original and insightful, not just a transcript summary
- Minimum 600 words
- Do NOT mention that this is based on a YouTube video"""

                    response = llm.invoke(prompt)
                    blog_content = response.content

                # Step 4 — Done
                steps_ph.markdown(
                    render_steps(done_list=["Fetch Transcript", "Build Context", "Generate Blog", "Ready"]),
                    unsafe_allow_html=True
                )

                st.success("✅ Blog generated successfully!")

                # Stats
                blog_words = len(blog_content.split())
                st.markdown(f"""
                <div class="stats-row">
                    <div class="stat-chip">📄 Transcript: <span>{word_count:,} words</span></div>
                    <div class="stat-chip">✍️ Blog: <span>{blog_words:,} words</span></div>
                    <div class="stat-chip">🌐 Language: <span>{blog_language}</span></div>
                    <div class="stat-chip">🎨 Tone: <span>{blog_tone}</span></div>
                </div>
                """, unsafe_allow_html=True)

                # Result
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown("""
                <div class="result-header">
                    <div class="result-icon">📝</div>
                    <div>
                        <div class="result-title">Your Generated Blog Post</div>
                        <div class="result-sub">Ready to publish — copy or download below</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(blog_content)

                st.download_button(
                    label="⬇️  Download as Markdown (.md)",
                    data=blog_content,
                    file_name="blog_post.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
                st.markdown('</div>', unsafe_allow_html=True)

            except TranscriptsDisabled:
                steps_ph.markdown(render_steps(), unsafe_allow_html=True)
                st.error("🚫 Transcripts are disabled for this video. Try a different video.")
            except NoTranscriptFound:
                steps_ph.markdown(render_steps(), unsafe_allow_html=True)
                st.error("❌ No transcript found. The video may not have captions available.")
            except Exception as e:
                steps_ph.markdown(render_steps(), unsafe_allow_html=True)
                st.error(f"⚠️ Something went wrong: {str(e)}")

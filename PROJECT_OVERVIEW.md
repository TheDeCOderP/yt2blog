# YouTube to Blog Generator — Project Overview

## Kya Hai Ye Project?

Ye ek AI-powered web app hai jo kisi bhi YouTube video ko ek structured blog post mein convert kar deta hai. Sirf video URL paste karo, aur app automatically transcript fetch karke ek professional blog generate kar deta hai — saath mein ek AI-generated cover image bhi.

---

## Kya Kaam Karta Hai?

1. User YouTube video URL dalta hai
2. App us video ka transcript fetch karta hai (YouTube Transcript API se)
3. Transcript ko chunks mein split karke FAISS vector store mein store kiya jata hai
4. OpenAI GPT-4 se relevant context retrieve karke ek well-structured blog post generate hoti hai
5. DALL-E 3 se blog ke liye ek AI cover image bhi generate hoti hai
6. User blog post (Markdown) aur cover image dono download kar sakta hai

---

## Flow Diagram

```
YouTube URL
    ↓
Transcript Fetch (YouTubeTranscriptApi)
    ↓
Text Chunking (RecursiveCharacterTextSplitter)
    ↓
Embeddings + Vector Store (OpenAI Embeddings + FAISS)
    ↓
Context Retrieval (RAG)
    ↓
Blog Generation (GPT-4)
    ↓
Cover Image Generation (DALL-E 3)
    ↓
Display + Download (Streamlit UI)
```

---

## Technologies Used

| Technology | Kaam |
|---|---|
| Python 3.11 | Core language |
| Streamlit | Web UI framework |
| LangChain | LLM orchestration, text splitting, RAG pipeline |
| OpenAI GPT-4 | Blog post generation |
| OpenAI DALL-E 3 | AI cover image generation |
| OpenAI Embeddings | Text embeddings for vector search |
| FAISS (faiss-cpu) | Vector store for semantic search |
| YouTube Transcript API | YouTube video transcript fetch karna |
| python-dotenv | Environment variables (.env) manage karna |
| Docker | Containerized deployment |

---

## Project Structure

```
youtube-to-blog/
├── app.py              # Main Streamlit app (saara logic yahan hai)
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker container config
├── .gitignore
├── LICENSE
└── README.md
```

---

## Setup & Run

### Local

```bash
# 1. Clone karo
git clone https://github.com/NomanAhmed234/youtube-to-blog.git
cd youtube-to-blog

# 2. Virtual env banao (optional)
python -m venv myenv
myenv\Scripts\activate  # Windows
# source myenv/bin/activate  # Mac/Linux

# 3. Dependencies install karo
pip install -r requirements.txt

# 4. .env file banao
echo OPENAI_API_KEY=your_openai_api_key_here > .env

# 5. App run karo
streamlit run app.py
```

### Docker

```bash
docker build -t youtube-to-blog .
docker run -p 8501:8501 --env OPENAI_API_KEY=your_key youtube-to-blog
```

App open hogi: http://localhost:8501

---

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (GPT-4 + DALL-E + Embeddings ke liye) |

---

## Key Features

- RAG (Retrieval-Augmented Generation) pipeline use hoti hai — pura transcript ek saath LLM ko nahi diya jata, balki relevant chunks retrieve karke context banaya jata hai
- Blog Markdown format mein generate hoti hai — headings, sections, conclusion sab structured hota hai
- Cover image DALL-E 3 se generate hoti hai blog content ke basis par
- Dono outputs (blog + image) downloadable hain directly UI se
- Docker support hai production/deployment ke liye

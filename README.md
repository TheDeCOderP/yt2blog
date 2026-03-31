<<<<<<< HEAD
# 🎥 YouTube to Blog

A Streamlit-powered app that converts any YouTube video into a well-structured blog post ✍️ and even generates an **AI image** for the blog using the best keywords.

---

## 🚀 Features

- 🎬 **Fetch YouTube Transcript** – Automatically extract transcripts from videos  
- ✨ **AI-Powered Blog Generation** – Converts transcript into a clean, well-written blog  
- 🖼️ **AI Image Generation** – Creates a relevant image for the blog using keywords  
- 📄 **Copy / Download Blog** – Easily copy or save the blog post  
- 🐳 **Docker Support** – Run the app in a container effortlessly  

---

## 🛠️ Installation

Clone the repository:

```bash
git clone https://github.com/NomanAhmed234/youtube-to-blog.git
cd youtube-to-blog
```
## Create and activate a virtual environment (optional but recommended):
```bash
python -m venv myenv
# Windows
myenv\Scripts\activate
# Mac/Linux
source myenv/bin/activate

```

## python -m venv myenv
```bash
pip install -r requirements.txt
```

# ⚙️ Setup

## Create a .env file in the project root and add your API keys:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```
# ▶️ Usage
## Run the Streamlit app:
```bash
streamlit run app.py
```
## Then open your browser and go to:
http://localhost:8501

# 🐳 Run with Docker

## Build and run the Docker container:
```bash
docker build -t youtube-to-blog .
docker run -p 8501:8501 youtube-to-blog
```

=======
# Youtube-transcript-blog
An AI-powered tool that extracts YouTube transcripts and converts them into structured, SEO-optimized blog content.
>>>>>>> da7bdcecdaa77767b807cc5fbb31895b1d812929

import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI
from dotenv import load_dotenv
import re
import base64
import os

load_dotenv()

st.set_page_config(page_title="🎥 YouTube to Blog Generator", page_icon="📝", layout="wide")

# --- UI Header ---
st.title("🎥 YouTube → Blog Post Generator")
st.markdown(
    "Paste a **YouTube video URL**, click **Generate Blog**, and get a structured blog post with an AI-generated cover image."
)

video_url = st.text_input("🔗 Enter YouTube Video URL", placeholder="e.g. https://www.youtube.com/watch?v=wv779vmyPVY")
generate_btn = st.button("🚀 Generate Blog Post", use_container_width=True)

# --- Helper Function ---
def extract_video_id(url: str):
    regex = r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None


def generate_blog_image(prompt: str, size: str = "720x720"):
    """Generate an AI image using OpenAI's DALL-E and return decoded bytes."""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        result = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",  # ✅ "standard" avoids quality errors
            response_format="b64_json",  # ✅ Make sure we get base64 output
        )

        image_base64 = result.data[0].b64_json
        if not image_base64:
            raise ValueError("Image API returned no base64 data.")

        return base64.b64decode(image_base64)

    except Exception as e:
        print(f"⚠️ Image generation failed: {e}")
        return None

# --- Main Logic ---
if generate_btn:
    if not video_url:
        st.warning("⚠️ Please enter a valid YouTube URL.")
    else:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.error("❌ Could not extract video ID from URL. Please check the link.")
        else:
            try:
                with st.spinner("📥 Fetching transcript..."):
                    transcript_list = YouTubeTranscriptApi().list(video_id)
                    transcript = transcript_list.find_transcript(['en'])
                    data = transcript.fetch()
                    full_text = " ".join([entry.text for entry in data])

                with st.spinner("📑 Splitting transcript & creating embeddings..."):
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
                    docs = text_splitter.create_documents([full_text])
                    embeddings = OpenAIEmbeddings()
                    vectorstore = FAISS.from_documents(docs, embeddings)
                    retriever = vectorstore.as_retriever()

                with st.spinner("🤖 Generating blog post with AI..."):
                    llm = ChatOpenAI(model="gpt-4", temperature=0.7)
                    context_docs = retriever.invoke("create a blog post")
                    context = "\n".join([doc.page_content for doc in context_docs])

                    prompt = f"""
                    You are a professional blog writer.
                    Write a well-structured blog post based on the following video transcript context:

                    {context}

                    The blog must include:
                    - A catchy title
                    - An engaging introduction
                    - At least 3–4 key sections with headings
                    - A clear and inspiring conclusion
                    - Use markdown formatting
                    """

                    blog = llm.invoke(prompt)

                st.success("✅ Blog Generated Successfully!")
                st.markdown("---")
                st.markdown("## 📝 Your Generated Blog")
               

                # Generate an image based on the blog content
                with st.spinner("🎨 Creating blog cover image..."):
                    image_prompt = f"Create a modern, professional blog cover image that visually represents this topic: {blog.content[:400]}"
                    image_data = generate_blog_image(image_prompt)
                    if image_data:
                       st.image(image_data, caption="🖼️ AI-Generated Blog Cover", use_container_width=True)
                       st.download_button(
                          label="⬇️ Download Blog Cover Image",
                          data=image_data,
                          file_name="blog_cover.png",
                          mime="image/png",
                          use_container_width=True, )
                    else:
                        st.warning("⚠️ Could not generate blog cover image.")

                # 📝 Then show the blog content below the image
                st.markdown(blog.content)
               
                st.download_button(
                    label="⬇️ Download Blog Post (Markdown)",
                    data=blog.content,
                    file_name="youtube_blog.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

            except TranscriptsDisabled:
                st.error("🚫 Transcripts are disabled for this video.")
            except NoTranscriptFound:
                st.error("❌ No transcript found for this video.")
            except Exception as e:
                st.error(f"⚠️ An error occurred: {str(e)}")

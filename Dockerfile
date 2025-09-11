FROM python:3.11-slim

WORKDIR /app

# Copy requirement file and install first
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the app
COPY . .

EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

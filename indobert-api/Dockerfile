# Server IndoBERTweet untuk Hugging Face Spaces (Docker) atau Render.
# Hugging Face menjalankan container sebagai user id 1000 dan membuka port 7860.
FROM python:3.12-slim

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH PYTHONUNBUFFERED=1
WORKDIR $HOME/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .
EXPOSE 7860
# Render mengisi PORT sendiri, Hugging Face memakai 7860
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]

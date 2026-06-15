FROM python:3.11-slim
WORKDIR /app
COPY orchestration/shipping/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY orchestration/shipping/ ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

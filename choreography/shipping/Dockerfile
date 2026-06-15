FROM python:3.11-slim
WORKDIR /app
COPY choreography/shipping/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY choreography/shipping/ ./
CMD ["python", "main.py"]

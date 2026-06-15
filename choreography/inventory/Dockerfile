FROM python:3.11-slim
WORKDIR /app
COPY choreography/inventory/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY choreography/inventory/ ./
CMD ["python", "main.py"]

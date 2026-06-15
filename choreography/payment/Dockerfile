FROM python:3.11-slim
WORKDIR /app
COPY choreography/payment/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY choreography/payment/ ./
CMD ["python", "main.py"]

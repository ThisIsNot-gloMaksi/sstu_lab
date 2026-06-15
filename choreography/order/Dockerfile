FROM python:3.11-slim
WORKDIR /app
COPY choreography/order/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY choreography/order/ ./
CMD ["python", "main.py"]

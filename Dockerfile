FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy full project
COPY . .

EXPOSE 8000

CMD ["uvicorn", "api_server.fast_server:app", "--host", "0.0.0.0", "--port", "8000"]

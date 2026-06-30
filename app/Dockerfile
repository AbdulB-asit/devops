FROM python:3.12-slim
WORKDIR /app

# Copy manifest first for cache-friendly builds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source
COPY . .

EXPOSE 5000
CMD ["python", "app.py"]

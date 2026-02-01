# scraper/Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-dotenv

# Copy scraper code
COPY . ./scraper

# Default command (can be overridden)
CMD ["python", "-m", "scraper.main"]
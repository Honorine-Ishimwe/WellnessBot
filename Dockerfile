FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend.py auth.py db.py logger.py cleanup_job.py schema.sql ./

# Expose port
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "backend:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120"]

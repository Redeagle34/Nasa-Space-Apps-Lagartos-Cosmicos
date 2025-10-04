# Backend Dockerfile
FROM python:3.11-alpine   

# Set working directory
WORKDIR /app

# Copy package files
COPY backend/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend .

# Expose port
EXPOSE 5000

# Start the application
CMD ["python", "app.py"]
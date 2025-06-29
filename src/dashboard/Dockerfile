FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the Streamlit port
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Command to run the application
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]

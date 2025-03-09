FROM python:3.9

WORKDIR /app

# Install Java for PyFlink
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-11-jre && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# Create directory for Flink connector JARs
RUN mkdir -p /opt/flink-connectors

# Copy requirements file
COPY requirements.txt .

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Command to run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
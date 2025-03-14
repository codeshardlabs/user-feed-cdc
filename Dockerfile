FROM --platform=linux/amd64 python:3.9

WORKDIR /app

# Install Java for PyFlink
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget gnupg software-properties-common && \
    wget -O - https://packages.adoptium.net/artifactory/api/gpg/key/public | apt-key add - && \
    echo "deb https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print$2}' /etc/os-release) main" | tee /etc/apt/sources.list.d/adoptium.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends temurin-11-jre && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    JAVA_HOME=/usr/lib/jvm/temurin-11-jre-amd64

# Create directory for Flink connector JARs
RUN mkdir -p /flink-connectors

# Copy requirements file
COPY requirements.txt .
COPY flink-connectors/ /flink-connectors/

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Command to run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
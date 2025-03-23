FROM --platform=linux/amd64 python:3.9

WORKDIR /app

# Create and activate virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Create directory for Flink connector JARs
RUN mkdir -p /flink-connectors

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Flink connectors and application code
COPY flink-connectors/ /flink-connectors/
COPY debezium-connectors/ /debezium-connectors/
COPY . .

# Command to run
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
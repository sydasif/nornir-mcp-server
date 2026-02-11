FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install uv package manager
RUN pip install --upgrade pip && pip install uv

# Sync dependencies using uv
RUN uv sync

# Expose port
EXPOSE 8000

# Run the server
CMD ["uv", "run", "nornir-mcp"]

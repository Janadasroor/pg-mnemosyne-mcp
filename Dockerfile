FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir .

# Set default environment variables (can be overridden)
ENV PG_BASE_DSN="postgresql://postgres:postgres@localhost:5432/postgres"

# Set the command to run the MCP server using stdio
ENTRYPOINT ["pg-mnemosyne", "run"]

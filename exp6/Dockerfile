FROM python:3.12-slim

# Run this as:
# docker build --tag=exp6:1 .
# docker run --rm -p 8000:8000 exp6:1

# Set the working directory inside the container
WORKDIR /app

# Requirements
RUN pip install --no-cache-dir dbos fastapi psycopg2-binary python-json-logger

# Copy your application code
COPY dbos-config.yaml fastapi_scope_shutdown.py .

# Expose the port your FastAPI app listens on
EXPOSE 8000

# Set environment variables (these will be available inside the container)
ENV PGHOST=${PGHOST}
ENV PGPORT=${PGPORT}
ENV PGUSER=${PGUSER}
ENV PGPASSWORD=${PGPASSWORD}
ENV PGDATABASE=${PGDATABASE}

# Define the command to run when the container starts
CMD ["uvicorn", "fastapi_scope_shutdown:app", "--host", "0.0.0.0", "--port", "8000"]

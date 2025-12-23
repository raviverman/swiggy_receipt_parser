FROM python:3.11-slim

WORKDIR /app

# Copy application code (but NOT runtime data)
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure start script is executable
RUN chmod +x docker_start.sh

# Declare data directory as mount point
VOLUME ["/app/data"]

# Run the start script
CMD ["./docker_start.sh"]

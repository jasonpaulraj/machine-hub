FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create initialization script
RUN chmod +x app/init_db.py

# Expose port
EXPOSE 8000

# Create startup script with MySQL wait
RUN echo '#!/bin/bash\n\
echo "Waiting for MySQL to be ready..."\n\
while ! mysqladmin ping -h"$DB_HOST" -P"$DB_PORT" --silent; do\n\
    echo "MySQL is unavailable - sleeping"\n\
    sleep 2\n\
done\n\
echo "MySQL is up - executing command"\n\
echo "Initializing database..."\n\
cd /app && python -m app.init_db\n\
echo "Starting application..."\n\
# Check if we should disable access logs in production\n\
if [ "${APP_ENV,,}" = "production" ]; then\n\
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --no-access-log\n\
else\n\
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload\n\
fi' > /app/start.sh

RUN chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
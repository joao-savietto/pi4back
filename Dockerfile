FROM python:3.12.11-slim


# Expose port 8000
EXPOSE 8000

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the project files into the container
COPY . /app/

# Make sure start_fastapi.sh is executable (explicitly set permissions)
RUN chmod +x /app/start_fastapi.sh

# Install MySQL driver and other necessary packages
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    python3-dev \
    default-mysql-client \
    && apt-get clean

# Install Aerich specifically since it's needed for migrations
RUN pip install aerich

ENV CHROMEDRIVER=/usr/bin/chromedriver
RUN pip install -r requirements.txt

ENTRYPOINT ["/app/start_fastapi.sh"]

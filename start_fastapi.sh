#!/bin/bash

set -e

wait_for_db() {
  local db_host="$1"
  local db_port="$2"
  local max_tries=10
  local try=0

  until mysqladmin ping -h "$db_host" -P "$db_port" --silent; do
    try=$((try+1))
    if [ $try -gt $max_tries ]; then
      echo "Max tries reached, exiting"
      exit 1
    fi
    echo "Waiting for database to be ready..."
    sleep 5
  done
}

# print mysql host and port
echo "MySQL host: $MYSQL_HOST, port: $MYSQL_PORT"

wait_for_db $MYSQL_HOST $MYSQL_PORT

mysql -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -h "$MYSQL_HOST" --skip-ssl -e "CREATE DATABASE IF NOT EXISTS $MYSQL_DATABASE"

cd /app

# Run database migrations if needed using Aerich - make sure migrations directory exists
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "Running database migrations with Aerich..."
    
    # Check if aerich is available and initialize if needed  
    if command -v aerich &> /dev/null; then
        mkdir -p ./migrations
        
        # Initialize aerich config using pyproject.toml approach (recommended)
        if [ ! -f "./pyproject.toml" ]; then
            echo "Initializing Aerich..."
            aerich init -t tortoise_config.TORTOISE_ORM
        fi
        
        # Check if db is initialized, if not initialize it first
        if ! aerich heads &> /dev/null; then
            echo "Initializing database schema..."
            aerich init-db
        fi
        
        # Apply migrations
        echo "Applying database migrations..."
        aerich upgrade
    else
        echo "Aerich not available, skipping migrations"
    fi
fi

# Start the FastAPI application
exec uvicorn pi4.main:app --host 0.0.0.0 --port 8000 --reload

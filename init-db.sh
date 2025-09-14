#!/bin/bash

set -e

nohup /usr/local/bin/docker-entrypoint.sh mysqld

wait_for_db() {
  local db_host="$1"
  local db_port="$2"
  local max_tries=10
  local try=0

  until mysqladmin ping -h"$db_host" -P"$db_port" --silent; do
    try=$((try+1))
    if [ $try -gt $max_tries ]; then
      echo "Max tries reached, exiting"
      exit 1
    fi
    echo "Waiting for database to be ready..."
    sleep 5
  done
}

# Wait for the MySQL server to be ready
wait_for_db localhost 3306

mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -h localhost -e "CREATE DATABASE IF NOT EXISTS $MYSQL_DATABASE"

exec "$@"
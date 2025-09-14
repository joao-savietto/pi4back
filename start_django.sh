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
while getopts ":h:" opt; do
  case $opt in
    h) COMMAND="$OPTARG";;
    \?) echo "Invalid option: -$OPTARG"; exit 1;;
  esac
done

args="$@"
# if no arguments passed, use default, which is to runserver

cd /app

if [ -z "$args" ]; then
    if [ "${NO_RELOAD:-0}" -eq 1 ]; then
        args="python manage.py runserver 0.0.0.0:8000 --noreload"
    else
        args="python manage.py runserver 0.0.0.0:8000"
    fi
fi

# reload bashrc
if [ "${IS_DJANGO_CONTAINER:-false}" = "true" ]; then
    python manage.py migrate
fi
exec $args

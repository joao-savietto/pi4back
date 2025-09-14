{
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        }
    },
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": "${MYSQL_HOST}",
                "port": "${MYSQL_PORT}",
                "user": "${MYSQL_USER}",
                "password": "${MYSQL_PASSWORD}",
                "database": "${MYSQL_DATABASE}"
            }
        }
    }
}

from os import environ

TORTOISE_ORM = {
    "apps": {
        "models": {
            "models": [
                "pi3.models.users",
                "pi3.models.measurements",
                "aerich.models"
            ],
            "default_connection": "default",
        }
    },
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": environ.get("MYSQL_HOST", "127.0.0.1"),
                "port": int(environ.get("MYSQL_PORT", "3306")),
                "user": environ.get("MYSQL_USER", "root"),
                "password": environ.get("MYSQL_PASSWORD", "password"),
                "database": environ.get("MYSQL_DATABASE", "test"),
            },
        }
    },
}

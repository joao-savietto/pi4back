# Migrations

This directory contains Tortoise ORM migration files that track database schema changes.

## How Migrations Work in This Project

1. **Automatic Migration Execution**: When the Docker container starts, migrations are automatically run via `start_fastapi.sh`:
   ```bash
   if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
       echo "Running database migrations..."
       python -m tortoise.orm --config tortoise_config.py migrate
   fi
   ```

2. **Schema Management**: Tortoise ORM automatically detects when models have changed and creates appropriate migration files.

3. **Migration Files**: Migration files will be created in this directory when needed.

## Best Practices

- All migration files should be committed to Git for consistent deployments
- When adding new models or modifying existing ones, run migrations to update the database schema
- For manual migration management: `python -m tortoise.orm --config tortoise_config.py migrate`

## Note About Tortoise ORM vs Django

Unlike Django which has separate commands (`makemigrations` and `migrate`), Tortoise ORM handles this automatically when you call:
```
python -m tortoise.orm --config tortoise_config.py migrate
```

The first time this command runs, it will create the initial schema based on your models.

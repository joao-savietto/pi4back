#!/bin/bash

echo "Fixing Aerich migration format..."

# Make sure we're in the right directory
cd /app

# Check if aerich is available
if ! command -v aerich &> /dev/null; then
    echo "Aerich not found, installing..."
    pip install aerich
fi

# Initialize Aerich config if needed
if [ ! -f "./pyproject.toml" ]; then
    echo "Initializing Aerich..."
    aerich init -t tortoise_config.TORTOISE_ORM
fi

echo "Checking for migration format issues..."

# Check if we're in a production environment (skip fix-migrations for safety)
IS_PRODUCTION=${PRODUCTION:-false}
if [ "$IS_PRODUCTION" = true ]; then
    echo "Production environment detected, skipping automatic migration fixes"
    echo "Please run 'aerich fix-migrations' manually during deployment."
else
    # Check if db is initialized and has migrations that might be old format
    if aerich heads &> /dev/null; then
        echo "Database initialized, checking for format issues..."
        
        # Try to detect if migration files are in old format by looking at the content
        MIGRATION_FILE="./migrations/models/0_20250916174039_init.py"
        
        if [ -f "$MIGRATION_FILE" ]; then
            # Check for old format markers (simple check)
            if grep -q "async def upgrade" "$MIGRATION_FILE" && grep -q "async def downgrade" "$MIGRATION_FILE"; then
                echo "Detected potential old format, checking if fix is needed..."
                # Try to run the fix-migrations command if available
                if aerich --help | grep -q "fix-migrations"; then
                    echo "Running fix-migrations to upgrade migration file formats..."
                    aerich fix-migrations || echo "Fix migrations failed but continuing..."
                else
                    echo "Warning: fix-migrations command not available in this Aerich version"
                fi
            else
                echo "Migration format appears correct, skipping fix step."
            fi
        fi
        
        # Apply any pending migrations
        echo "Applying database migrations..."
        aerich upgrade
    else
        echo "Database not initialized, initializing now..."
        aerich init-db
        echo "Applying database migrations..."
        aerich upgrade
    fi
fi

echo "Migration fix process completed."

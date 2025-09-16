from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from pi3.routes.auth import router as auth_router
from pi3.routes.measurements import router as measurements_router
from pi3.routes.users import router as users_router
import os
from pi3.models.users import User
from pi3.auth.utils import get_password_hash

app = FastAPI(title="FastAPI with Tortoise ORM")

# Register Tortoise ORM
register_tortoise(
    app,
    config_file="tortoise_config.py",
    generate_schemas=False,
    add_exception_handlers=True,
)


async def create_default_admin():
    """Create default admin user if it doesn't exist yet"""
    # Only create default admin in development environments or when explicitly requested
    environment = os.getenv("ENVIRONMENT", "local")

    # Check if we're in setup mode or development
    setup_mode = os.getenv("SETUP_MODE", "false").lower() == "true"

    # In production, only auto-create if no users exist and we're in setup mode
    if environment == "production":
        try:
            existing_users = await User.all().count()
            if existing_users > 0:
                return  # Admin already exists

            # Only proceed with creation if we explicitly enable setup mode
            if not setup_mode:
                return
        except Exception:
            # If database connection fails, don't create user automatically
            return

    try:
        # Check if default admin user exists
        existing_user = await User.filter(
            username=os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
        ).first()

        if not existing_user:
            # Create default admin user with password from environment variables
            default_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
            default_password = os.getenv(
                "DEFAULT_ADMIN_PASSWORD", "password123"
            )

            hashed_password = get_password_hash(default_password)
            await User.create(
                name="Admin User",
                username=default_username,
                hashed_password=hashed_password,
            )

            print(f"Created default admin user: {default_username}")
    except Exception as e:
        # Log error but don't crash the application
        print(f"Error creating default admin user: {e}")


# Include routers
app.include_router(measurements_router)
app.include_router(auth_router)
app.include_router(users_router)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    await create_default_admin()


@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI with Tortoise ORM!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

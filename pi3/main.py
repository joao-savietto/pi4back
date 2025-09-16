from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from pi3.routes.auth import router as auth_router
from pi3.routes.measurements import router as measurements_router
from pi3.routes.users import router as users_router

app = FastAPI(title="FastAPI with Tortoise ORM")

# Register Tortoise ORM
register_tortoise(
    app,
    config_file="tortoise_config.py",
    generate_schemas=False,
    add_exception_handlers=True,
)

# Include routers
app.include_router(measurements_router)
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI with Tortoise ORM!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

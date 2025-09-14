from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

app = FastAPI(title="FastAPI with Tortoise ORM")

# Register Tortoise ORM
register_tortoise(
    app,
    config_file="tortoise_config.py",
    generate_schemas=False,
    add_exception_handlers=True,
)

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI with Tortoise ORM!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

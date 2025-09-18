from datetime import datetime

from passlib.context import CryptContext
from tortoise import fields, models

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    username = fields.CharField(max_length=50, unique=True)
    hashed_password = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(default=datetime.now)

    class Meta:
        table = "users"

    def verify_password(self, password: str) -> bool:
        """Verify a plain text password against the stored hash"""
        return pwd_context.verify(password, self.hashed_password)

    def set_password(self, password: str):
        """Hash and set a new password"""
        self.hashed_password = pwd_context.hash(password)

    def __str__(self):
        return f"User(id={self.id}, name='{self.name}', username='{self.username}')"

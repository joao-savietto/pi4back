from datetime import datetime

from tortoise import fields, models


class Measurement(models.Model):
    id = fields.IntField(pk=True)
    temperature = fields.FloatField()
    humidity = fields.FloatField()
    timestamp = fields.DatetimeField(default=datetime.now)

    class Meta:
        table = "measurements"

    def __str__(self):
        return f"Measurement(id={self.id}, temp={self.temperature}°C, hum={self.humidity}%, time={self.timestamp})"

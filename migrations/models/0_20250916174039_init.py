from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `hashed_password` VARCHAR(255) NOT NULL,
    `created_at` DATETIME(6) NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `measurements` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `temperature` DOUBLE NOT NULL,
    `humidity` DOUBLE NOT NULL,
    `timestamp` DATETIME(6) NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztmPFPm0AUx/8Vwk8ucUY7q2ZZlmCtsYttTa3bojHkCle4CHfIHdPG9H/fvQN6QAuxi2"
    "Y26U8t3/d98N6HK+/oixkyFwd874bj2PxqvJgUhVh+Kem7homiSKsgCDQJlDGRDqWgCRcx"
    "coQUpyjgWEou5k5MIkEYlSpNggBE5kgjoZ6WEkoeE2wL5mHhq0Lu7qVMqIufMc8Powd7Sn"
    "DgluokLlxb6baYRUrrUXGujHC1ie2wIAmpNkcz4TO6cBMqQPUwxTESGE4v4gTKh+qyNvOO"
    "0kq1JS2xkOPiKUoCUWj3lQwcRoGfrIarBj24yufWweHx4cmXo8MTaVGVLJTjedqe7j1NVA"
    "QGY3Ou4kig1KEwam7qc4lcx0fxanS5vwJPllyFl6NqopcLGp9eMm/EL0TPdoCpJ3x5eLC/"
    "30DrpzXqXFijHen6BN0wuYzTxT3IQq00Bkg1Qlj562Is5rwNyndfiCWQ7ddwbNdjbC9R9B"
    "H3sWtHiPMnFq/4NdfDXJG6mcuz1W6/Aqt01XJVsTJYJ8bQso3EMtMzGREkxKu5ljMrSN0s"
    "dS//8l6AzW/ThDoA1hgwivcoe/pu/jvxBsDjXr97Pbb6V3D6kPPHQDGyxl2ItJQ6q6g7R5"
    "V7sTiJ8as3vjDg0LgdDroKIePCi9UVtW98a0JNKBHMlr3ZyC1yyOVcmsMEnD4UnuUgTJDz"
    "8IRi116KsBar8y6HwlZYVRBFnroxQBPqzDYEfYx4EuMQU7Fqv1AMN24bQm3c7h42bvcgcB"
    "hBv/IOLgM8DxiqQVjJq7CcQuLHfF430Dob3pxedo2rUbfTu+4NB+XHhQqCJAUiVJujrnVZ"
    "HYJJSFwiZmvBLCZtSeYrU04kLlAYrTv0SonbmbedeXrmWTgmjr9q3GWRxkmHtGc74zZoxv"
    "3BMYeSluDVv5AUUrYvIguQ8NNYA2Jm30yA7/JHg7yiyDbUZYg/roeDmlc4nVIBeUNlg3cu"
    "ccSuERAu7j8m1gaK0HVpauXwdvrW7yrXzuXwtDqO4ASnkvF/HS/zv6eh3WI="
)

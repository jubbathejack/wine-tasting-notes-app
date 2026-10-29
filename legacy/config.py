#!/usr/bin/env python3

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqlconnector://"
        f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        f"?ssl_ca={os.getenv('DB_CA')}&charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: False

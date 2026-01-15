import psycopg2
import psycopg2.extras
import logging

logger = logging.getLogger(__name__)

# ----------------- DATABASE CONFIG -----------------
DB_CONFIG = {
    "host":"localhost",# "host": "10.19.71.198", this is Company host
    "port": 5432,
    "database": "uso_chm_pc",
    "user": "postgres",
    "password": "Coder@123",
    "connect_timeout": 5
}

# ----------------- CONNECTION -----------------
# def get_db_connection():
#     try:
#         return psycopg2.connect(
#             host=DB_CONFIG["host"],
#             port=DB_CONFIG["port"],
#             database=DB_CONFIG["database"],
#             user=DB_CONFIG["user"],
#             password=DB_CONFIG["password"],
#             connect_timeout=DB_CONFIG["connect_timeout"]
#         )
    
# ----------------- CONNECTION -----------------for render
import psycopg2
import os

def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            connect_timeout=5
        )


    except Exception as e:
        logger.error("PostgreSQL connection failed", exc_info=True)
        raise

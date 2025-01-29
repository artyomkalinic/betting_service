import psycopg2
from contextlib import contextmanager
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname='bettyom', user='artyom', password='1234', host='db_postgres_1'
        )
        yield conn
    except Exception as e:
        print(f"Can't establish connection to database: {e}")
    finally:
        if conn:
            conn.close()
            # print("Database connection closed.")

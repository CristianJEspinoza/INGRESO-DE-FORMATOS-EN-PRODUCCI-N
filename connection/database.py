import psycopg2
from psycopg2.extras import RealDictCursor
import os

def get_db_connection():
    try:
        host = os.getenv('host')
        database = os.getenv('database')
        user = os.getenv('user')
        password = os.getenv('password')
        port = os.getenv('port')
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        return conn
    except psycopg2.DatabaseError as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise

def execute_query(query, params=None):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Configurar la localización a español
        cur.execute("SET lc_time = 'es_ES.utf8';")

        # Ejecutar la consulta
        cur.execute(query, params)
        result = cur.fetchall() if cur.description else None
        conn.commit()
        return result

    except psycopg2.Error as e:
        print(f"Error al ejecutar la consulta: {e}")
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


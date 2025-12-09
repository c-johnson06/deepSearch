import psycopg as pg

def database_setup():
    conn = pg.connect("host=localhost port=5431 dbname=postgres user=postgres password=borris")
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'deepsearch'")
    exists = cur.fetchone()

    if not exists:
        cur.execute("CREATE DATABASE deepsearch;")
    
    cur.close()
    conn.close()

    conn = pg.connect("host=localhost port=5431 dbname=deepsearch user=postgres password=borris")
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS videos (
                id SERIAL PRIMARY KEY,
                name TEXT,
                path TEXT)
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS frames (
                id SERIAL PRIMARY KEY,
                video_id INTEGER REFERENCES videos(id),
                timestamp FLOAT,
                IMAGE_PATH TEXT,
                embedding VECTOR(512))
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS text_segments (
                id SERIAL PRIMARY KEY,
                video_id INTEGER REFERENCES videos(id),
                start_time FLOAT,
                end_time FLOAT,
                text TEXT,
                embedding VECTOR(384))
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("DATABASE CREATED")


database_setup()
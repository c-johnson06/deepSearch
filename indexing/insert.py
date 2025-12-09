import psycopg as pg
import numpy as np

def get_connection():
    try: 
        conn = pg.connect(dbname='deepsearch', user='postgres', password='borris', host='localhost', port=5431) 
        return conn
    except Exception as e: print(e)
def insert_video(conn, name: str, path: str) -> int:
    cur = conn.cursor()

    cur.execute("INSERT INTO videos (name, path) VALUES (%s, %s) RETURNING id", (name, path))
    
    video_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return video_id
def insert_frame(conn, video_id: int, timestamp: float, image_path: str, embedding: np.ndarray):

    embedding_list = embedding.tolist()

    with conn.cursor() as cur:
        cur.execute("INSERT INTO frames (video_id, timestamp, image_path, embedding) VALUES (%s, %s, %s, %s)",
                    (video_id, timestamp, image_path, embedding_list))

        conn.commit()
def insert_text_segment(conn, video_id: int, start_time: float, end_time: float, text: str, embedding: np.ndarray):

    embedding_list = embedding.tolist()

    with conn.cursor() as cur:
        cur.execute("INSERT INTO text_segments (video_id, start_time, end_time, text, embedding) VALUES (%s, %s, %s, %s, %s)",
                    (video_id, start_time, end_time, text, embedding_list))

        conn.commit()
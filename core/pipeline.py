import os
import cv2
import shutil
from ingestion.extract_audio import extract_audio, transcribe_audio
from ingestion.extract_frames import extract_frames
from embedding.frame_embedding import get_frame_embeddings
from embedding.text_embedding import get_text_embeddings
from indexing.insert import get_connection, insert_video, insert_text_segment, insert_frame

def update_progress(video_id, progress):
    """Helper to update DB progress without crashing"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE videos SET progress = %s WHERE id = %s", (progress, video_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Progress Update Warning: {e}")

def run_ingestion_pipeline(video_path: str, frame_interval: float = 1.0):
    filename = os.path.basename(video_path)
    print(f"🚀 Starting pipeline for: {filename}")
    
    conn = get_connection()
    cur = conn.cursor()

    # 1. WIPE OLD DATA (Utility Mode)
    cur.execute("TRUNCATE TABLE videos, frames, text_segments RESTART IDENTITY CASCADE;")
    conn.commit()
    
    # Clear physical folders
    if os.path.exists("frames"): shutil.rmtree("frames")
    os.makedirs("frames", exist_ok=True)

    # 2. REGISTER VIDEO
    cur.execute(
        "INSERT INTO videos (title, filepath, status, progress) VALUES (%s, %s, 'processing', 0) RETURNING id",
        (filename, video_path)
    )
    video_id = cur.fetchone()[0]
    conn.commit()
    conn.close() # Close main conn, we open short ones for updates

    try:
        # --- AUDIO PHASE (0% -> 10%) ---
        print("🎤 Processing Audio...")
        audio_path = extract_audio(video_path)
        transcript = transcribe_audio(audio_path)
        text_embeddings = get_text_embeddings(transcript)
        
        conn = get_connection()
        for seg, emb in zip(transcript, text_embeddings):
            insert_text_segment(conn, video_id, seg["start"], seg["end"], seg["text"], emb)
        conn.close()
        
        update_progress(video_id, 10) 

        # --- VIDEO PHASE (10% -> 99%) ---
        print("👁️ Processing Frames...")
        
        # Calculate totals for progress math
        vid = cv2.VideoCapture(video_path)
        fps = vid.get(cv2.CAP_PROP_FPS)
        if fps <= 0: fps = 24
        total_seconds = (vid.get(cv2.CAP_PROP_FRAME_COUNT) / fps)
        vid.release()

        frame_gen = extract_frames(video_path, seconds_per_frame=frame_interval)
        
        batch = []
        frame_idx = 0
        last_reported_progress = 10 
        
        video_frame_dir = os.path.join("frames", str(video_id))
        os.makedirs(video_frame_dir, exist_ok=True)

        conn = get_connection()
        
        for frame, timestamp in frame_gen:
            batch.append((frame, timestamp))
            
            # --- PROGRESS CALCULATION ---
            if total_seconds > 0:
                # Map timestamp to 10-99% range
                percent_complete = 10 + int((timestamp / total_seconds) * 89)
                
                # Only update if we moved forward (prevents database spam)
                if percent_complete > last_reported_progress:
                    update_progress(video_id, percent_complete)
                    print(f"Progress: {percent_complete}%") 
                    last_reported_progress = percent_complete
            # -----------------------------

            if len(batch) >= 32:
                embeddings = get_frame_embeddings(batch)
                for (frm, ts), emb in zip(batch, embeddings):
                    img_name = f"frame_{frame_idx}.jpg"
                    save_path = os.path.join(video_frame_dir, img_name)
                    cv2.imwrite(save_path, frm)
                    
                    db_path = f"frames/{video_id}/{img_name}"
                    insert_frame(conn, video_id, ts, db_path, emb)
                    frame_idx += 1
                batch = []

        # Process leftovers
        if batch:
            embeddings = get_frame_embeddings(batch)
            for (frm, ts), emb in zip(batch, embeddings):
                img_name = f"frame_{frame_idx}.jpg"
                save_path = os.path.join(video_frame_dir, img_name)
                cv2.imwrite(save_path, frm)
                db_path = f"frames/{video_id}/{img_name}"
                insert_frame(conn, video_id, ts, db_path, emb)
                frame_idx += 1

        # FINISH
        conn.close()
        update_progress(video_id, 100)
        
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE videos SET status = 'completed' WHERE id = %s", (video_id,))
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Pipeline Failed: {e}")
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE videos SET status = 'failed' WHERE id = %s", (video_id,))
        conn.commit()
        conn.close()
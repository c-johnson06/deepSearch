from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import shutil
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pipeline import run_ingestion_pipeline
from search_service.search import query, fuse_results
from indexing.insert import get_connection

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("frames", exist_ok=True)
app.mount("/frames", StaticFiles(directory="frames"), name="frames")

@app.get("/")
def home():
    return {"status": "DeepSearch API Ready"}

@app.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    frame_interval: int = Form(1)
):
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    background_tasks.add_task(run_ingestion_pipeline, file_path, frame_interval)
    
    return {"message": "Processing started", "filename": file.filename, "config": {"frame_interval": frame_interval}}

@app.get("/status")
def get_status():
    conn = get_connection()
    if conn is None: return {"status": "offline"}
    
    cur = conn.cursor()
    # Fetch status AND progress
    cur.execute("SELECT status, title, progress FROM videos ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    
    if row:
        return {
            "status": row[0], 
            "filename": row[1], 
            "progress": row[2] # <--- Sending this to Frontend
        }
    else:
        return {"status": "no_index", "filename": None, "progress": 0}

@app.get("/search")
def search(q: str, visual_weight: float = 1.0, text_weight: float = 1.0):
    try:
        raw_results = query(q)
        fused_results = fuse_results(raw_results, weight_visual=visual_weight, weight_text=text_weight)
        return fused_results[:20]
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.post("/reset")
def reset_system():
    """
    Forcefully resets the database status. Used when the UI gets stuck.
    """
    conn = get_connection()
    if conn is None:
        return {"status": "error", "detail": "Database offline"}

    cur = conn.cursor()
    try:
        # 1. Delete everything from the DB
        cur.execute("TRUNCATE TABLE videos, frames, text_segments RESTART IDENTITY CASCADE;")
        conn.commit()
        
        # 2. Delete the physical frame files
        if os.path.exists("frames"):
            shutil.rmtree("frames")
        os.makedirs("frames", exist_ok=True)
        
        # 3. Delete the uploaded video files
        if os.path.exists("uploads"):
            shutil.rmtree("uploads")
        os.makedirs("uploads", exist_ok=True)
        
        return {"status": "reset_complete"}
    except Exception as e:
        print(f"Reset Error: {e}")
        return {"status": "error", "detail": str(e)}
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
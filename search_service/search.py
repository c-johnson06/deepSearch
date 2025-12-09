import sentence_transformers
from transformers import CLIPModel, CLIPProcessor
from indexing.insert import get_connection

text_model = sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')
frame_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
frame_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
def query(query: str):
    conn = get_connection()
    cur = conn.cursor()

    user_text_embedding = text_model.encode(query).tolist()

    frame_inputs = frame_processor(text=[query], return_tensors="pt", padding=True)
    frame_outputs = frame_model.get_text_features(**frame_inputs)
    user_frame_embedding = frame_outputs.detach().numpy()[0].tolist()

    cur.execute("SELECT timestamp, image_path, 1 - (embedding <=> %s::vector) AS score FROM frames ORDER BY score DESC LIMIT 5", (user_frame_embedding,))
    frame_results = cur.fetchall()

    cur.execute("SELECT start_time, end_time, text, 1 - (embedding <=> %s::vector) AS score FROM text_segments ORDER BY score DESC LIMIT 5", (user_text_embedding,))
    text_results = cur.fetchall()

    return {
        "frames" : frame_results,
        "text" : text_results
    }


def fuse_results(results: dict, time_window: float = 5.0, weight_visual: float = 1.0, weight_text: float = 1.0) -> list:
    """
    Fuses visual and text search results into coherent scenes.
    """
    candidates = []

    # --- 1. Use the passed-in weights instead of hardcoded 1.0 ---
    for frame_result in results["frames"]:
        candidates.append({
            'time': float(frame_result[0]),
            'score': float(frame_result[2]) * weight_visual, # <--- Uses the slider value
            'type': 'visual',
            'preview': frame_result[1],
            'text': None
        })
    
    for text_result in results["text"]:
        candidates.append({
            'time': float(text_result[0]),
            'score': float(text_result[3]) * weight_text, # <--- Uses the slider value
            'type': 'text',
            'preview': None,
            'text': text_result[2]
        })

    # Sort by score first to prioritize better matches when grouping
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    if not candidates: 
        return []

    scenes = []
    used_times = set()

    # --- 2. Clustering Logic (Unchanged) ---
    for candidate in candidates:
        if candidate['time'] in used_times:
            continue
            
        scene_start = candidate['time']
        scene_end = candidate['time']
        scene_hits = [candidate]
        scene_visual_score = 0.0
        scene_text_score = 0.0
        
        if candidate['type'] == 'visual':
            scene_visual_score = candidate['score']
        else:
            scene_text_score = candidate['score']
        
        for other in candidates:
            if other['time'] in used_times:
                continue
            if other == candidate:
                continue
                
            if abs(other['time'] - candidate['time']) <= time_window:
                scene_hits.append(other)
                scene_start = min(scene_start, other['time'])
                scene_end = max(scene_end, other['time'])
                used_times.add(other['time'])
                
                if other['type'] == 'visual':
                    scene_visual_score = max(scene_visual_score, other['score'])
                else:
                    scene_text_score = max(scene_text_score, other['score'])
        
        used_times.add(candidate['time'])
        
        scenes.append({
            'start_time': scene_start,
            'end_time': scene_end,
            'visual_score': scene_visual_score,
            'text_score': scene_text_score,
            'hits': scene_hits,
            'center_time': candidate['time']
        })

    final_results = []

    for scene in scenes:
        total_score = scene['visual_score'] + scene['text_score']
        
        # Find best visual preview
        best_image = "no_image.jpg"
        visual_hits = [h for h in scene['hits'] if h['preview']]
        if visual_hits:
            best_visual_hit = max(visual_hits, key=lambda x: x['score'])
            best_image = best_visual_hit['preview']
        
        # Find best text snippet
        best_text = "..."
        text_hits = [h for h in scene['hits'] if h['text']]
        if text_hits:
            best_text_hit = max(text_hits, key=lambda x: x['score'])
            best_text = best_text_hit['text']
        
        # Use the time of the highest scoring hit in the scene
        best_hit = max(scene['hits'], key=lambda x: x['score'])
        scene_timestamp = best_hit['time']
        
        final_results.append({
            'timestamp': scene_timestamp,
            'score': total_score,
            'match_type': 'hybrid' if scene['visual_score'] > 0 and scene['text_score'] > 0 else 'single',
            'preview_path': best_image,
            'transcript_snippet': best_text
        })
    
    final_results.sort(key=lambda x: x['score'], reverse=True)
    
    # --- 3. FIX: Return the list, not a single item ---
    # The API expects a list. If you return final_results[0], the React .map() function will crash.
    return final_results
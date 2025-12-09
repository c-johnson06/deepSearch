from ingestion.extract_audio import extract_audio, transcribe_audio
from ingestion.extract_frames import extract_frames
from embedding.frame_embedding import get_frame_embeddings
from embedding.text_embedding import get_text_embeddings
from indexing.insert import get_connection, insert_frame, insert_text_segment, insert_video
from search_service.search import query, fuse_results
import cv2

def main():
    conn = get_connection()
    video_id = insert_video(conn, "video", "video.mp4")

    audio_file = extract_audio("video.mp4")
    transcript = transcribe_audio(audio_file)
    text_embeddings = get_text_embeddings(transcript)

    for seg, embedding in zip(transcript, text_embeddings):
        insert_text_segment(conn, video_id, seg["start"], seg["end"], seg["text"], embedding)

    print("Audio processed successfully!")

    frames = extract_frames("video.mp4")

    current_batch = []
    BATCH_SIZE = 32

    frame_index = 0

    for frame, timestamp in frames:
        current_batch.append((frame, timestamp))

        if len(current_batch) >= BATCH_SIZE:
            frame_embeddings = get_frame_embeddings(current_batch)

            for (frame, timestamp), embedding in zip(current_batch, frame_embeddings):
                image_path = f"frames/frame_{frame_index}.jpg"
                cv2.imwrite(image_path, frame)
                insert_frame(conn, video_id, timestamp, image_path, embedding)
                frame_index += 1

            current_batch = []
    
    if current_batch:
        frame_embeddings = get_frame_embeddings(current_batch)
        for (frame, timestamp), embedding in zip(current_batch, frame_embeddings):
                image_path = f"frames/frame_{frame_index}.jpg"
                cv2.imwrite(image_path, frame)
                insert_frame(conn, video_id, timestamp, image_path, embedding)
                frame_index += 1
    
    print(f"Processed all frames. Vector shape:  {frame_embeddings.shape}")

    user_query = input("Enter your query: ")
    results = query(user_query)
    print(fuse_results(results))


if __name__ == "__main__":
    main()
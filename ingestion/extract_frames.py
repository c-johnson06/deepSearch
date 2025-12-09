import cv2
def extract_frames(video_file: str, seconds_per_frame: float = 1.0):
    """
    Extracts frames from a video file at a given FPS

    Args:
        video_file (str): Path to video file
        frames_per_second (int): Frames per second to extract (higher is more memory intensive)
    
    Return:
        list: List of tuples containing frame and timestamp
    """
    vid = cv2.VideoCapture(video_file)

    if not vid.isOpened():
        raise ValueError("Could not open video file")
    
    native_fps = vid.get(cv2.CAP_PROP_FPS)
    total_frames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calculate number of frames to skip (native FPS / desired sampling FPS)
    frame_hop = int(native_fps / seconds_per_frame)

    current_frame_idx = 0
    
    while current_frame_idx < total_frames:

        # Jump to the desired frame
        vid.set(cv2.CAP_PROP_POS_FRAMES, current_frame_idx)

        ret, frame = vid.read()

        if not ret: break
        
        timestamp_ms = vid.get(cv2.CAP_PROP_POS_MSEC)

        timestamp = timestamp_ms / 1000

        if timestamp == 0 and current_frame_idx > 0:
            timestamp = current_frame_idx / native_fps

        # Adds frame and timestamp to a numpy array
        yield frame, timestamp

        current_frame_idx += frame_hop

    vid.release()

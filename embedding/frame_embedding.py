from transformers import CLIPProcessor, CLIPModel
import cv2
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"

processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)

def get_frame_embeddings(frames: list) -> list:
    """
    Get embeddings for each frame in a video
    Uses CLIP processor and model to encode the frames

    Args:
        frames (list): List of frames in a video
    
    Return:
        list: List of embeddings for each frame converted to RGB in a numpy array
    """
    raw_frames = [frame for (frame, _) in frames]

    # Raw frames must be converted to RGB for use with the CLIP model
    rgb_frames = [cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) for frame in raw_frames]

    inputs = processor(images=rgb_frames, return_tensors="pt", padding=True).to(device)
    outputs = model.get_image_features(**inputs)
    
    return outputs.detach().cpu().numpy()
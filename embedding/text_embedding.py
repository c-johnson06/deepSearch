import sentence_transformers

model = sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')
def get_text_embeddings(texts: list) -> list:
    """
        Get text embeddings based on the audio transcription of the video
        Uses sentence transformers to encode the text

        Args:
            texts (list): List of each text segment derived from the audio transcription
        
        Return:
            list: List of embeddings for each text segment after encoding
    """
    texts = [seg["text"] for seg in texts]
    return model.encode(texts)
from faster_whisper import WhisperModel
import subprocess
import os
def extract_audio(video_file: str, output_ext = "wav"):
    """
    Extract audio from a video file using ffmpeg

    Args:
        video_file (str): Path to video file
        output_ext (str): Extension of output file (default: ".wav")
    
    Return:
        str: Path to audio output file
    """

    filename, _ = os.path.splitext(video_file)
    output_path = f"{filename}.{output_ext}"

    #FFmpeg command to extract only audio
    command = ["ffmpeg", "-y",
               "-i", video_file,
               "-ac", "1",
               "-ar", "16000",
               "-acodec", "pcm_s16le",
               output_path]
    
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    return output_path

def transcribe_audio(audio_file: str, model_size: str = "medium", device: str = None, compute_type: str = None, beam_size: int = None):
    """
    Transcribes an audio file using FasterWhisper

    Args:
        audio_file (str): Path to the audio file to be transcribed
        model_size (str, optional): Size of the model to use. Defaults to "medium"
        device (str, optional): Device to use for transcription (cpu / cuda)
        compute_type (str, optional): Compute type to use for transcription (int8 / float16 / float32)
        beam_size (int, optional): Beam size to use for transcription
    
    Returns:
        array: Array of transcribed text in segments
    """

    # Default to cuda if compatible, otherwise default to cpu
    if device is None:
        device = "cuda" if os.getenv("CUDA_VISIBLE_DEVICES") is not None else "cpu"
    
    # Use more intensive compute type for cuda devices
    if compute_type is None:
        compute_type = "float16" if device == "cuda" else "int8"

    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    if beam_size is None:
        if device == "cuda": beam_size = 5 
        else: beam_size = 1

    segments, info = model.transcribe(audio_file, beam_size=beam_size)

    print("Translating %s using %s model with %s" % (audio_file, model_size, device))
    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    output = []

    # Groups audio output based on timestamps and content
    for segment in segments:
        output.append({"start": float(segment.start), "end": float(segment.end), "text": segment.text.strip()})
    
    return output

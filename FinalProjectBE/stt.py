import os
from google.cloud import speech
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

def convert_to_16k_mono(input_path: str) -> str:
    sound = AudioSegment.from_file(input_path)
    sound = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)

    converted_path = input_path.replace(".wav", "_16k.wav")
    sound.export(converted_path, format="wav")
    return converted_path

def stt_from_wav(audio_path: str) -> str:
    try:
        converted_path = convert_to_16k_mono(audio_path)

        client = speech.SpeechClient()
        with open(converted_path, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )

        response = client.recognize(config=config, audio=audio)
        for result in response.results:
            return result.alternatives[0].transcript

    except Exception as e:
        print(f"[STT ERROR] {e}")
        raise

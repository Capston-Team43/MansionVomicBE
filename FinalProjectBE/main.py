from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import mimetypes

from clone import clone_voice
from stt import stt_from_wav
from llm import generate_response
from tts import generate_tts

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/register-voice/")
async def register_voice(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    voice_name = clone_voice(temp_path)
    os.remove(temp_path)

    return {"message": "Voice cloned successfully", "voice_name": voice_name}

@app.post("/voice-assistant/")
async def voice_assistant(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        text = stt_from_wav(temp_path)
        reply = generate_response(text)
        audio_path = generate_tts(reply)
    finally:
        os.remove(temp_path)

    return {"text": reply, "audio_path": audio_path}

@app.get("/latest-tts-audio/")
def get_latest_audio():
    files = sorted(os.listdir("cloned_audios"), reverse=True)
    if not files:
        return {"error": "No audio available"}
    latest = files[0]
    file_path = os.path.join("cloned_audios", latest)
    media_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=latest
    )
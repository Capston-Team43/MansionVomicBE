import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from clone import get_latest_cloned_voice_uri

load_dotenv()

PLAYHT_USER_ID = os.getenv("PLAYHT_USER_ID")
PLAYHT_API_KEY = os.getenv("PLAYHT_API_KEY")
TTS_OUTPUT_DIR = "cloned_audios"
os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)


def generate_tts(text: str) -> str:
    """텍스트를 mp3(44100 Hz)로 생성하고 파일 경로를 반환."""

    voice_uri = get_latest_cloned_voice_uri()  

    url = "https://api.play.ht/api/v2/tts/stream"
    headers = {
        "X-User-Id": PLAYHT_USER_ID,
        "AUTHORIZATION": PLAYHT_API_KEY,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }

    # payload = {
    #     "text": text,
    #     "voice": voice_uri,
    #     "voice_engine": "PlayHT2.0",  
    #     "quality": "premium",          
    #     "output_format": "mp3",        
    #     "sample_rate": 44100,
    #     "speed": 1
    # }

    payload = {
        "text": text,
        "voice": voice_uri,  # s3://... 형식
        "voice_engine": "PlayHT2.0",       # 최신 일반형 엔진
        "quality": "premium",              # 가장 높은 허용 품질
        "temperature": 0.2,                # 자연스럽지만 음색 고정
        "style_guidance": 18,              # 억양 스타일 고정 (1~30)   
        "output_format": "mp3",            # wav도 가능
        "sample_rate": 44100,
        "speed": 0.95,
        "pitch": 1.8
    }


    resp = requests.post(url, headers=headers, json=payload, stream=True)
    if resp.status_code != 200:
        raise Exception(f"TTS 생성 실패: {resp.status_code} - {resp.text}")

    fname = datetime.now().strftime("%Y%m%d%H%M%S") + ".mp3"
    fpath = os.path.join(TTS_OUTPUT_DIR, fname)

    with open(fpath, "wb") as f:
        for chunk in resp.iter_content(chunk_size=4096):
            if chunk:
                f.write(chunk)

    print(f"✅ TTS 저장 완료: {fpath}")
    return fpath


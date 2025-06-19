# import os
# import uuid
# import requests
# import time
# from pydub import AudioSegment
# from dotenv import load_dotenv
# from pydub import AudioSegment
# from pydub.effects import normalize, strip_silence
# import noisereduce as nr
# import numpy as np
# import scipy.io.wavfile as wav
# import tempfile, os

import os, uuid, requests, time, tempfile
from dotenv import load_dotenv

from pydub import AudioSegment
from pydub.effects import normalize, strip_silence
import noisereduce as nr
import numpy as np
import scipy.io.wavfile as wav


load_dotenv()

PLAYHT_USER_ID = os.getenv("PLAYHT_USER_ID")
PLAYHT_API_KEY = os.getenv("PLAYHT_API_KEY")

CLONED_PROFILE_DIR = "cloned_profiles"
os.makedirs(CLONED_PROFILE_DIR, exist_ok=True)


# ① WAV 변환(16 kHz / mono / 16‑bit PCM)
def convert_to_standard_wav(src: str) -> str:
    sound = AudioSegment.from_file(src)
    sound = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    dst = src.replace(".wav", "_converted.wav")
    sound.export(dst, format="wav")
    return dst

# def convert_to_standard_wav(src: str) -> str:
#     """
#     1) 볼륨 정규화
#     2) 앞·뒤 묵음 제거
#     3) 노이즈 리덕션(선택)
#     4) 16 kHz / mono / 16-bit PCM 변환
#     5) *_converted.wav 파일로 저장 경로 반환
#     """
#     # ① 파일 로드
#     audio = AudioSegment.from_file(src)

#     # ② 볼륨 정규화
#     audio = normalize(audio)

#     # ③ 앞·뒤 0.4 초 이상 묵음 제거
#     audio = strip_silence(
#         audio,
#         silence_len=400,      # ms
#         silence_thresh=-40    # dBFS
#     )

#     # ④ 노이즈 리덕션 (환경이 조용하면 주석 처리해도 무방)
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
#         audio.export(tmp.name, format="wav")
#         rate, data = wav.read(tmp.name)
#     reduced = nr.reduce_noise(
#         y=data.astype(float),
#         sr=rate,
#         prop_decrease=1.0      # 0.0~1.0 : 값이 클수록 노이즈 강하게 감소
#     )
#     wav.write(tmp.name, rate, reduced.astype(np.int16))
#     audio = AudioSegment.from_file(tmp.name)
#     os.unlink(tmp.name)        # 임시 파일 제거

#     # ⑤ 16 kHz / mono / 16-bit PCM으로 변환
#     audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

#     # ⑥ 저장
#     dst = src.replace(".wav", "_converted.wav")
#     audio.export(dst, format="wav")
#     return dst


# ② 클론 완료 여부 polling
def wait_for_voice_ready(name: str, timeout: int = 30):
    url = "https://api.play.ht/api/v2/cloned-voices"
    hdr = {
        "Authorization": f"Bearer {PLAYHT_API_KEY}",
        "X-User-Id": PLAYHT_USER_ID,
    }
    print(f"⌛ Waiting for voice {name!r} ...")
    for _ in range(timeout):
        r = requests.get(url, headers=hdr)
        if r.status_code == 200:
            for v in r.json():
                if v.get("name") == name:
                    print(f"✅ Voice {name!r} is ready.")
                    return
        time.sleep(1)
    raise Exception(f"❌ Voice {name} not ready in {timeout}s")


# ③ 보이스 클론 (instant)
def clone_voice(wav_path: str) -> str:
    voice_name = f"voice_{uuid.uuid4().hex[:8]}"
    conv_path = convert_to_standard_wav(wav_path)

    url = "https://api.play.ht/api/v2/cloned-voices/instant/"
    hdr = {
        "Authorization": f"Bearer {PLAYHT_API_KEY}",
        "X-User-Id": PLAYHT_USER_ID,
    }
    files = {"sample_file": (f"{voice_name}.wav", open(conv_path, "rb"), "audio/wav")}
    data = {"voice_name": voice_name}

    resp = requests.post(url, headers=hdr, data=data, files=files)
    if resp.status_code != 201:
        raise Exception(f"보이스 클론 실패: {resp.status_code} - {resp.text}")

    js = resp.json()

    voice_name = js.get("name", voice_name)          # 실제 name
    manifest_uri = js.get("url") or js.get("id")     # ← 이 필드에 S3 URI
    if not manifest_uri or not manifest_uri.startswith("s3://"):
        raise Exception(f"응답에 manifest URI가 없습니다: {js}")
    
    wait_for_voice_ready(voice_name)
    time.sleep(5)  

    profile_path = os.path.join(CLONED_PROFILE_DIR, voice_name)
    os.makedirs(profile_path, exist_ok=True)

    # 클론된 보이스 정보 저장
    with open(os.path.join(profile_path, "playht_voice_id.txt"), "w") as f:
        f.write(voice_name)
    with open(os.path.join(profile_path, "manifest_uri.txt"), "w") as f:
        f.write(manifest_uri)

    return voice_name


# ④ 가장 최신 manifest URI (TTS용)
def get_latest_cloned_voice_uri() -> str:
    folders = [
        d for d in os.listdir(CLONED_PROFILE_DIR)
        if os.path.isdir(os.path.join(CLONED_PROFILE_DIR, d))
    ]
    if not folders:
        raise Exception("보이스 클론 프로필이 없습니다.")

    latest = max(folders, key=lambda f: os.path.getmtime(os.path.join(CLONED_PROFILE_DIR, f)))
    manifest_path = os.path.join(CLONED_PROFILE_DIR, latest, "manifest_uri.txt")

    if not os.path.exists(manifest_path):
        raise Exception(f"{manifest_path} 파일이 없습니다.")
    uri = open(manifest_path).read().strip()
    if not uri.startswith("s3://"):
        raise Exception(f"유효하지 않은 URI: {uri}")
    return uri

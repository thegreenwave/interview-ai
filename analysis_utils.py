# analysis_utils.py
import difflib
import librosa


def analyze_audio_features(y, sr):
    """
    음성 신호 y와 샘플링레이트 sr을 받아
    - RMS(볼륨)
    - 시간축
    - 스펙트럴 센트로이드
    - 전체 길이
    - 침묵 비율
    - 초기 침묵 시간
    을 계산한다.
    """
    rms = librosa.feature.rms(y=y)[0]
    times = librosa.times_like(rms, sr=sr)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]

    # 비침묵 구간 탐지
    non_silent = librosa.effects.split(y, top_db=25)
    non_silent_dur = sum((e - s) for s, e in non_silent) / sr
    total_dur = librosa.get_duration(y=y, sr=sr)

    if len(non_silent) > 0:
        # non_silent는 샘플 인덱스를 반환하므로 sr로 나눠서 초로 변환
        init_silence = non_silent[0][0] / sr
    else:
        init_silence = 0.0

    silence_ratio = (
        (total_dur - non_silent_dur) / total_dur if total_dur > 0 else 0.0
    )

    return times, rms, cent, total_dur, silence_ratio, init_silence


def calculate_similarity(t1: str, t2: str) -> float:
    """
    두 문자열의 유사도를 0~100 (%)로 반환.
    """
    return difflib.SequenceMatcher(None, t1, t2).ratio() * 100

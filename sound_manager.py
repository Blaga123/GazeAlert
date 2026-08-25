"""
Sound Synthesizer and Manager for GazeAlert.
Generates studio-quality harmonic WAV files without external dependencies.
Plays audio asynchronously with 0 ms latency using Windows sound engine.
"""

import math
import os
import struct
import sys
import wave
from typing import Optional

try:
    import winsound
except ImportError:
    winsound = None

def _get_res_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

SOUNDS_DIR = _get_res_path("sounds")


def _generate_harmonic_wav(filepath: str, frequencies: list, duration_sec: float = 0.4, sample_rate: int = 44100):
    """Generate a clean, pleasant harmonic sine-wave chime with exponential decay envelope."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    num_samples = int(duration_sec * sample_rate)
    
    with wave.open(filepath, "w") as wav_file:
        wav_file.setnchannels(1)        # Mono
        wav_file.setsampwidth(2)        # 16-bit
        wav_file.setframerate(sample_rate)
        
        raw_bytes = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            decay = math.exp(-3.5 * (t / duration_sec))  # Smooth exponential decay
            
            sample_val = 0.0
            for idx, freq in enumerate(frequencies):
                weight = 1.0 / (idx + 1)
                sample_val += math.sin(2.0 * math.pi * freq * t) * weight
            
            # Normalize and apply envelope
            sample_val = sample_val * decay * 0.45
            sample_int = int(max(-32767, min(32767, sample_val * 32767)))
            raw_bytes.extend(struct.pack("<h", sample_int))
            
        wav_file.writeframes(raw_bytes)


def ensure_default_sounds():
    """Create default pleasant audio cues if not present."""
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    
    focus_chime = os.path.join(SOUNDS_DIR, "focus_chime.wav")
    if not os.path.exists(focus_chime):
        _generate_harmonic_wav(focus_chime, [523.25, 659.25], duration_sec=0.35)  # C5 + E5
        
    away_warning = os.path.join(SOUNDS_DIR, "away_warning.wav")
    if not os.path.exists(away_warning):
        _generate_harmonic_wav(away_warning, [659.25, 440.0], duration_sec=0.45)   # E5 -> A4
        
    pomo_break = os.path.join(SOUNDS_DIR, "pomo_break.wav")
    if not os.path.exists(pomo_break):
        _generate_harmonic_wav(pomo_break, [523.25, 659.25, 783.99, 1046.50], duration_sec=0.6)  # C-E-G-C

    posture_chime = os.path.join(SOUNDS_DIR, "posture_chime.wav")
    if not os.path.exists(posture_chime):
        _generate_harmonic_wav(posture_chime, [587.33, 880.0], duration_sec=0.30)  # D5 + A5


def play_sound_async(sound_name: str, custom_path: Optional[str] = None):
    """Play WAV audio asynchronously with zero playback delay."""
    if winsound is None:
        return
        
    target_path = custom_path
    if not target_path or not os.path.exists(target_path):
        target_path = os.path.join(SOUNDS_DIR, f"{sound_name}.wav")
        
    if os.path.exists(target_path):
        try:
            winsound.PlaySound(target_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass

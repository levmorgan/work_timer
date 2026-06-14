"""Alert sound for period-end notification.

Supports:
- A default generated WAV (played via QSoundEffect, infinite loop)
- User-provided WAV or MP3 files (played via QMediaPlayer, manual loop)
"""

from __future__ import annotations

import atexit
import os
import struct
import tempfile
import wave
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QSoundEffect


SAMPLE_RATE = 44100
FREQUENCY = 880  # Hz — A5 note
BEEP_DURATION = 0.2  # seconds of tone
PAUSE_DURATION = 0.8  # seconds of silence after the beep
AMPLITUDE = 0.8  # 0.0–1.0

_wav_path: Optional[Path] = None
_effect: Optional[QSoundEffect] = None
_player: Optional[QMediaPlayer] = None
_audio_output: Optional[QAudioOutput] = None
_current_file: Optional[str] = None  # user-selected file path, or None for default


def _generate_wav() -> Path:
    """Generate the default sine-wave WAV file and return its path."""
    global _wav_path
    if _wav_path is not None:
        return _wav_path

    beep_samples = int(SAMPLE_RATE * BEEP_DURATION)
    pause_samples = int(SAMPLE_RATE * PAUSE_DURATION)

    samples: list[int] = []
    for i in range(beep_samples):
        t = i / SAMPLE_RATE
        envelope = min(1.0, t / 0.01, (BEEP_DURATION - t) / 0.01)
        envelope = max(0.0, envelope)
        value = int(AMPLITUDE * envelope * 32767 * _sine_wave(t))
        samples.append(value)

    samples.extend([0] * pause_samples)
    num_samples = len(samples)

    frames = struct.pack(f"<{num_samples}h", *samples)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(frames)

    _wav_path = Path(tmp.name)
    atexit.register(os.unlink, str(_wav_path))
    return _wav_path


def _sine_wave(t: float) -> float:
    import math
    return math.sin(2 * math.pi * FREQUENCY * t)


def _init_default_player() -> QSoundEffect:
    global _effect
    if _effect is not None:
        return _effect
    effect = QSoundEffect()
    effect.setSource(QUrl.fromLocalFile(str(_generate_wav())))
    effect.setLoopCount(QSoundEffect.Infinite.value)
    effect.setVolume(1.0)
    _effect = effect
    return _effect


def _init_file_player(filepath: str) -> QMediaPlayer:
    global _player, _audio_output
    if _player is None:
        _audio_output = QAudioOutput()
        _audio_output.setVolume(1.0)
        _player = QMediaPlayer()
        _player.setAudioOutput(_audio_output)
        _player.mediaStatusChanged.connect(_on_media_status)
    _player.setSource(QUrl.fromLocalFile(filepath))
    return _player


def _on_media_status(status: QMediaPlayer.MediaStatus) -> None:
    if status == QMediaPlayer.MediaStatus.EndOfMedia:
        if _player is not None:
            _player.play()


def set_alarm(filepath: str | None) -> None:
    """Set the alarm sound file. Pass None or empty string for default.
    If the file doesn't exist, falls back to the default sound.
    """
    global _current_file
    if filepath and Path(filepath).is_file():
        _current_file = filepath
    else:
        _current_file = None


def play_alert() -> None:
    """Start looping the alert sound."""
    if _current_file:
        player = _init_file_player(_current_file)
        player.play()
    else:
        effect = _init_default_player()
        effect.play()


def stop_alert() -> None:
    """Stop the alert sound."""
    if _player is not None:
        _player.stop()
    if _effect is not None:
        _effect.stop()

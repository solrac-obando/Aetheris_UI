# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
AetherAudioBridge — Physics-driven audio integration layer.

Sound is treated as a physical state: components trigger audio events
based on velocity thresholds, collisions, and epsilon-snapping.

Platform providers:
  DesktopAudioProvider: PyOgg for .ogg playback (non-blocking)
  MobileAudioProvider: pygame.mixer for mobile assets
  WebAudioProvider: Web Audio API via WebBridge.js
  MockAudioProvider: Silent provider for headless/testing
"""
import os
import sys
import logging
import threading
from abc import ABC, abstractmethod
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ============================================================================
# Abstract Base
# ============================================================================

class AetherAudioBridge(ABC):
    """Abstract audio bridge for physics-driven sound triggers."""

    @abstractmethod
    def play_sound(self, sound_id: str, volume: float = 1.0, pitch: float = 1.0) -> bool:
        """Play a sound identified by sound_id with given volume and pitch.

        Args:
            sound_id: Identifier for the sound asset (filename without extension)
            volume: Volume level 0.0-1.0
            pitch: Pitch multiplier (1.0 = original, 2.0 = octave up)

        Returns:
            True if sound was dispatched successfully
        """
        pass

    @abstractmethod
    def preload(self, sound_id: str, path: str) -> bool:
        """Preload a sound asset into memory.

        Args:
            sound_id: Identifier to reference this sound
            path: File path to the audio asset

        Returns:
            True if loaded successfully
        """
        pass

    @abstractmethod
    def stop_all(self) -> None:
        """Stop all currently playing sounds."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Release audio resources."""
        pass


# ============================================================================
# Desktop Provider — PyOgg (non-blocking threaded playback)
# ============================================================================

class DesktopAudioProvider(AetherAudioBridge):
    """Desktop audio using PyOgg for .ogg playback in background threads."""

    def __init__(self):
        self._sounds: Dict[str, str] = {}
        self._available = False
        self._ogg = None
        self._opus = None
        self._vorbis = None
        self._players = []
        try:
            import pyogg
            self._ogg = pyogg
            self._available = True
            logger.info("DesktopAudioProvider: PyOgg loaded successfully")
        except ImportError:
            logger.warning("DesktopAudioProvider: PyOgg not available, falling back to silent mode")

    def preload(self, sound_id: str, path: str) -> bool:
        if not os.path.exists(path):
            logger.warning(f"DesktopAudioProvider: Sound file not found: {path}")
            return False
        self._sounds[sound_id] = path
        return True

    def play_sound(self, sound_id: str, volume: float = 1.0, pitch: float = 1.0) -> bool:
        if not self._available:
            return False
        path = self._sounds.get(sound_id)
        if path is None:
            logger.warning(f"DesktopAudioProvider: Sound '{sound_id}' not preloaded")
            return False
        if not os.path.exists(path):
            logger.warning(f"DesktopAudioProvider: Sound file missing: {path}")
            return False
        t = threading.Thread(
            target=self._play_ogg,
            args=(path, volume, pitch),
            daemon=True,
        )
        t.start()
        self._players.append(t)
        return True

    def _play_ogg(self, path: str, volume: float, pitch: float) -> None:
        """Play an OGG file using PyOgg in a background thread."""
        try:
            import pyaudio
            pa = pyaudio.PyAudio()

            opus_filename = None
            vorbis_filename = None
            try:
                if self._ogg.OpusFile is not None:
                    opus_file = self._ogg.OpusFile(path)
                    if opus_file.is_opus:
                        frequency = opus_file.frequency
                        channels = opus_file.channels
                        pcm = opus_file.as_array()
                        opus_filename = path
                    else:
                        raise ValueError("Not an Opus file")
            except Exception:
                try:
                    if self._ogg.VorbisFile is not None:
                        vorbis_file = self._ogg.VorbisFile(path)
                        frequency = vorbis_file.frequency
                        channels = vorbis_file.channels
                        pcm = vorbis_file.as_array()
                        vorbis_filename = path
                    else:
                        raise ValueError("VorbisFile not available")
                except Exception:
                    logger.warning(f"DesktopAudioProvider: Cannot decode {path}")
                    return

            stream = pa.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=frequency,
                output=True,
            )
            stream.write(pcm.tobytes())
            stream.stop_stream()
            stream.close()
            pa.terminate()
        except ImportError:
            logger.warning("DesktopAudioProvider: PyAudio not installed, cannot play sound")
        except Exception as e:
            logger.warning(f"DesktopAudioProvider: Playback error: {e}")

    def stop_all(self) -> None:
        self._players.clear()

    def shutdown(self) -> None:
        self._sounds.clear()
        self._players.clear()


# ============================================================================
# Mobile Provider — pygame.mixer
# ============================================================================

class MobileAudioProvider(AetherAudioBridge):
    """Mobile audio using pygame.mixer for optimized asset playback."""

    def __init__(self):
        self._sounds: Dict[str, str] = {}
        self._channels: Dict[str, object] = {}
        self._available = False
        self._mixer = None
        try:
            import pygame
            pygame.mixer.init()
            self._mixer = pygame.mixer
            self._available = True
            logger.info("MobileAudioProvider: pygame.mixer initialized")
        except Exception as e:
            logger.warning(f"MobileAudioProvider: pygame.mixer unavailable: {e}")

    def preload(self, sound_id: str, path: str) -> bool:
        if not self._available:
            return False
        if not os.path.exists(path):
            logger.warning(f"MobileAudioProvider: Sound file not found: {path}")
            return False
        try:
            sound = self._mixer.Sound(path)
            self._sounds[sound_id] = sound
            return True
        except Exception as e:
            logger.warning(f"MobileAudioProvider: Failed to load {path}: {e}")
            return False

    def play_sound(self, sound_id: str, volume: float = 1.0, pitch: float = 1.0) -> bool:
        if not self._available:
            return False
        sound = self._sounds.get(sound_id)
        if sound is None:
            logger.warning(f"MobileAudioProvider: Sound '{sound_id}' not preloaded")
            return False
        try:
            sound.set_volume(min(max(volume, 0.0), 1.0))
            sound.play()
            return True
        except Exception as e:
            logger.warning(f"MobileAudioProvider: Playback error: {e}")
            return False

    def stop_all(self) -> None:
        if self._available:
            self._mixer.stop()

    def shutdown(self) -> None:
        if self._available:
            self._mixer.quit()
        self._sounds.clear()


# ============================================================================
# Web Provider — Web Audio API via WebBridge.js
# ============================================================================

class WebAudioProvider(AetherAudioBridge):
    """Web audio provider that emits calls to the browser's Web Audio API.

    In a hybrid Aetheris setup, this provider sends JSON messages to the
    JS layer via the WebBridge. The JS layer handles actual playback
    using the native Web Audio API (no external JS libraries).
    """

    def __init__(self, bridge=None):
        self._sounds: Dict[str, str] = {}
        self._bridge = bridge
        self._queue: list = []

    def set_bridge(self, bridge) -> None:
        self._bridge = bridge

    def preload(self, sound_id: str, path: str) -> bool:
        self._sounds[sound_id] = path
        return True

    def play_sound(self, sound_id: str, volume: float = 1.0, pitch: float = 1.0) -> bool:
        path = self._sounds.get(sound_id, sound_id)
        msg = {
            "type": "audio_play",
            "sound_id": sound_id,
            "path": path,
            "volume": volume,
            "pitch": pitch,
        }
        if self._bridge is not None:
            try:
                self._bridge.send_audio(msg)
                return True
            except Exception as e:
                logger.warning(f"WebAudioProvider: Bridge send failed: {e}")
        self._queue.append(msg)
        return True

    def flush_queue(self) -> list:
        msgs = list(self._queue)
        self._queue.clear()
        return msgs

    def stop_all(self) -> None:
        if self._bridge is not None:
            try:
                self._bridge.send_audio({"type": "audio_stop_all"})
            except Exception:
                pass
        self._queue.clear()

    def shutdown(self) -> None:
        self._sounds.clear()
        self._queue.clear()


# ============================================================================
# Mock Provider — Silent, for headless/testing
# ============================================================================

class MockAudioProvider(AetherAudioBridge):
    """Silent audio provider for headless environments and testing.

    Records all play_sound calls for verification without actual playback.
    """

    def __init__(self):
        self._sounds: Dict[str, str] = {}
        self._history: list = []

    def preload(self, sound_id: str, path: str) -> bool:
        self._sounds[sound_id] = path
        return True

    def play_sound(self, sound_id: str, volume: float = 1.0, pitch: float = 1.0) -> bool:
        self._history.append({
            "sound_id": sound_id,
            "volume": volume,
            "pitch": pitch,
        })
        return True

    def stop_all(self) -> None:
        pass

    def shutdown(self) -> None:
        self._sounds.clear()
        self._history.clear()

    @property
    def history(self) -> list:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()


# ============================================================================
# Factory
# ============================================================================

def create_audio_bridge(mode: str = "auto") -> AetherAudioBridge:
    """Create the appropriate audio bridge for the current platform.

    Args:
        mode: 'desktop', 'mobile', 'web', 'mock', or 'auto' (detect)

    Returns:
        An AetherAudioBridge instance for the detected/requested platform
    """
    if mode == "mock":
        return MockAudioProvider()

    if mode == "web":
        return WebAudioProvider()

    if mode == "mobile":
        return MobileAudioProvider()

    if mode == "desktop":
        return DesktopAudioProvider()

    # Auto-detect
    if _is_web_environment():
        return WebAudioProvider()
    if _is_mobile_environment():
        return MobileAudioProvider()
    return DesktopAudioProvider()


def _is_web_environment() -> bool:
    """Detect if running in a web/WASM context."""
    return (
        os.environ.get("AETHERIS_RUNTIME") == "web"
        or "emscripten" in sys.platform.lower()
    )


def _is_mobile_environment() -> bool:
    """Detect if running on a mobile platform."""
    return (
        os.environ.get("AETHERIS_RUNTIME") == "mobile"
        or "android" in sys.platform.lower()
        or "kivy" in os.environ.get("KIVY_WINDOW", "").lower()
    )

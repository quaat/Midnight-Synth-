from __future__ import annotations

import logging
import queue
import threading
from collections import defaultdict

import numpy as np

try:
    import sounddevice as sd
except Exception:  # pragma: no cover
    sd = None

from .schemas import PresetData
from .voice import Voice

logger = logging.getLogger(__name__)


class SynthEngine:
    def __init__(self, sample_rate: int = 48000, block_size: int = 256, polyphony: int = 8) -> None:
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.polyphony = polyphony
        self.voices = [Voice(sample_rate=float(sample_rate)) for _ in range(polyphony)]
        self.event_queue: queue.SimpleQueue[dict] = queue.SimpleQueue()
        self.params = PresetData(name="Init").model_dump()
        self.target_params = self.params.copy()
        self.held_notes: dict[int, int] = {}
        self.sustain = False
        self.midi_cc_map: dict[int, str] = {}
        self.stream: sd.OutputStream | None = None
        self.lock = threading.Lock()
        self.left_meter = 0.0
        self.right_meter = 0.0

    def start(self) -> None:
        if sd is None:
            logger.warning("sounddevice not available; audio stream disabled")
            return
        if self.stream:
            return
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=2,
            blocksize=self.block_size,
            dtype="float32",
            callback=self._audio_callback,
            latency="low",
        )
        self.stream.start()
        logger.info("Synth engine started")

    def stop(self) -> None:
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        logger.info("Synth engine stopped")

    def set_param(self, path: str, value: float) -> None:
        keys = path.split(".")
        ref = self.target_params
        for k in keys[:-1]:
            if k not in ref or not isinstance(ref[k], dict):
                return
            ref = ref[k]
        if keys[-1] in ref:
            ref[keys[-1]] = value

    def smooth_params(self) -> None:
        def smooth_dict(current: dict, target: dict):
            for k, v in target.items():
                if isinstance(v, dict) and isinstance(current.get(k), dict):
                    smooth_dict(current[k], v)
                elif isinstance(v, (int, float)) and isinstance(current.get(k), (int, float)):
                    current[k] = current[k] + (v - current[k]) * 0.2

        smooth_dict(self.params, self.target_params)

    def handle_midi(self, event: dict) -> None:
        etype = event.get("type")
        if etype == "note_on" and event.get("vel", 0) > 0:
            self.note_on(event["note"], event["vel"])
        elif etype in {"note_off", "note_on"}:
            self.note_off(event["note"])
        elif etype == "pitch_bend":
            bend = (event.get("value", 8192) - 8192) / 8192.0
            self.set_param("lfo1.amount", max(0.0, min(1.0, abs(bend))))
        elif etype == "cc":
            cc, value = event["cc"], event["value"]
            if cc == 64:
                self.sustain = value >= 64
            if cc in self.midi_cc_map:
                self.set_param(self.midi_cc_map[cc], value / 127.0)

    def note_on(self, note: int, vel: int) -> None:
        self.held_notes[note] = vel
        free = next((v for v in self.voices if not v.active), None)
        if free is None:
            free = max(self.voices, key=lambda v: v.age_samples)
        free.start(note, vel)

    def note_off(self, note: int) -> None:
        self.held_notes.pop(note, None)
        if self.sustain:
            return
        for voice in self.voices:
            if voice.active and voice.note == note:
                voice.release()

    def _apply_fx(self, buf: np.ndarray) -> np.ndarray:
        for fx in self.params.get("effects", []):
            mix = fx.get("mix", 0.0)
            if fx["name"] == "distortion":
                drive = fx.get("params", {}).get("drive", 1.5)
                wet = np.tanh(buf * drive)
            elif fx["name"] == "chorus":
                depth = fx.get("params", {}).get("depth", 0.2)
                wet = np.roll(buf, int(depth * 30), axis=0)
            elif fx["name"] == "delay":
                taps = int(self.sample_rate * fx.get("params", {}).get("time", 0.2))
                wet = np.copy(buf)
                if taps < len(buf):
                    wet[taps:] += buf[:-taps] * fx.get("params", {}).get("feedback", 0.25)
            elif fx["name"] == "reverb":
                wet = np.copy(buf)
                wet = 0.7 * wet + 0.3 * np.roll(wet, 79, axis=0)
            else:
                continue
            buf = (1 - mix) * buf + mix * wet
        return np.tanh(buf)

    def render_block(self, frames: int) -> np.ndarray:
        while not self.event_queue.empty():
            self.handle_midi(self.event_queue.get_nowait())

        self.smooth_params()
        mixed = np.zeros((frames, 2), dtype=np.float32)
        voice_params = {
            "osc1": self.params["osc1"],
            "osc2": self.params["osc2"],
            "noise_level": self.params["noise_level"],
            "amp_env": self.params["amp_env"],
            "filter_env": self.params["filter_env"],
            "filter": self.params["filter"],
        }
        for voice in self.voices:
            mixed += voice.render(frames, voice_params)

        mixed *= float(self.params["master_gain"]) / max(1, self.polyphony / 2)
        mixed = self._apply_fx(mixed)
        self.left_meter = float(np.sqrt(np.mean(np.square(mixed[:, 0]))))
        self.right_meter = float(np.sqrt(np.mean(np.square(mixed[:, 1]))))
        return mixed

    def _audio_callback(self, outdata, frames, time_info, status) -> None:  # pragma: no cover
        if status:
            logger.warning("Audio callback status: %s", status)
        outdata[:] = self.render_block(frames)

    def get_runtime_state(self) -> dict:
        return {
            "type": "runtime.state",
            "meters": {"l": self.left_meter, "r": self.right_meter},
            "notes": [{"note": n, "vel": v} for n, v in sorted(self.held_notes.items())],
            "voices_active": sum(1 for v in self.voices if v.active),
        }

    def load_preset(self, preset: PresetData) -> None:
        with self.lock:
            payload = preset.model_dump()
            self.params = payload
            self.target_params = payload.copy()
            self.polyphony = payload["polyphony"]
            if len(self.voices) != self.polyphony:
                self.voices = [Voice(sample_rate=float(self.sample_rate)) for _ in range(self.polyphony)]

    def assign_cc(self, cc: int, path: str) -> None:
        self.midi_cc_map[cc] = path

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


WAVEFORMS = {"sine", "saw", "square", "triangle"}


@dataclass
class EnvelopeState:
    value: float = 0.0
    stage: str = "idle"


@dataclass
class Voice:
    sample_rate: float
    note: int = -1
    velocity: float = 0.0
    active: bool = False
    released: bool = False
    phase1: float = 0.0
    phase2: float = 0.0
    filter_z: float = 0.0
    pan: float = 0.5
    env_amp: EnvelopeState = field(default_factory=EnvelopeState)
    env_filter: EnvelopeState = field(default_factory=EnvelopeState)
    age_samples: int = 0

    def start(self, note: int, velocity: int) -> None:
        self.note = note
        self.velocity = max(1, velocity) / 127.0
        self.active = True
        self.released = False
        self.env_amp = EnvelopeState(value=0.0, stage="attack")
        self.env_filter = EnvelopeState(value=0.0, stage="attack")
        self.age_samples = 0

    def release(self) -> None:
        if self.active:
            self.released = True
            self.env_amp.stage = "release"
            self.env_filter.stage = "release"

    def _phase_increment(self, note: int, detune_cents: float = 0.0) -> float:
        hz = 440.0 * (2 ** ((note - 69 + detune_cents / 100.0) / 12.0))
        return hz / self.sample_rate

    def _osc(self, phase: np.ndarray, waveform: str) -> np.ndarray:
        if waveform == "sine":
            return np.sin(2 * math.pi * phase)
        if waveform == "saw":
            return 2.0 * phase - 1.0
        if waveform == "square":
            return np.where(phase < 0.5, 1.0, -1.0)
        if waveform == "triangle":
            return 4.0 * np.abs(phase - 0.5) - 1.0
        return np.zeros_like(phase)

    def _step_adsr(self, env: EnvelopeState, adsr: dict[str, float], n: int) -> np.ndarray:
        out = np.empty(n, dtype=np.float32)
        attack = max(adsr["attack"], 1e-5)
        decay = max(adsr["decay"], 1e-5)
        sustain = adsr["sustain"]
        release = max(adsr["release"], 1e-5)

        for i in range(n):
            if env.stage == "attack":
                env.value += 1.0 / (attack * self.sample_rate)
                if env.value >= 1.0:
                    env.value = 1.0
                    env.stage = "decay"
            elif env.stage == "decay":
                env.value -= (1.0 - sustain) / (decay * self.sample_rate)
                if env.value <= sustain:
                    env.value = sustain
                    env.stage = "sustain"
            elif env.stage == "sustain":
                env.value = sustain
            elif env.stage == "release":
                env.value -= max(env.value, sustain) / (release * self.sample_rate)
                if env.value <= 0.0005:
                    env.value = 0.0
                    env.stage = "idle"
                    self.active = False
            out[i] = env.value
        return out

    def render(self, frames: int, params: dict) -> np.ndarray:
        if not self.active:
            return np.zeros((frames, 2), dtype=np.float32)

        self.age_samples += frames
        osc1 = params["osc1"]
        osc2 = params["osc2"]

        inc1 = self._phase_increment(self.note, osc1["detune_cents"])
        inc2 = self._phase_increment(self.note, osc2["detune_cents"])

        ph1 = (self.phase1 + np.arange(frames) * inc1) % 1.0
        ph2 = (self.phase2 + np.arange(frames) * inc2) % 1.0
        self.phase1 = float((ph1[-1] + inc1) % 1.0)
        self.phase2 = float((ph2[-1] + inc2) % 1.0)

        s1 = self._osc(ph1, osc1["waveform"]) * osc1["level"]
        s2 = self._osc(ph2, osc2["waveform"]) * osc2["level"]
        noise = np.random.uniform(-1, 1, frames).astype(np.float32) * params["noise_level"]

        raw = (s1 + s2 + noise) * self.velocity
        amp = self._step_adsr(self.env_amp, params["amp_env"], frames)
        filter_env = self._step_adsr(self.env_filter, params["filter_env"], frames)

        key_track = params["filter"]["key_tracking"] * ((self.note - 60) / 24.0)
        cutoff = params["filter"]["cutoff"] * (1 + 0.8 * filter_env + key_track)
        cutoff = np.clip(cutoff, 20.0, 18000.0)

        # one-pole low pass for stability & speed
        x = raw * amp
        y = np.empty(frames, dtype=np.float32)
        prev = self.filter_z
        for i in range(frames):
            alpha = math.exp(-2 * math.pi * cutoff[i] / self.sample_rate)
            prev = (1 - alpha) * x[i] + alpha * prev
            y[i] = prev
        self.filter_z = float(prev)

        pan = float(np.clip(self.pan, 0.0, 1.0))
        left = y * math.sqrt(1 - pan)
        right = y * math.sqrt(pan)
        return np.stack([left, right], axis=1)

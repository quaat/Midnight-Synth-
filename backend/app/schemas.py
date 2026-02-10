from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator


PRESET_SCHEMA_VERSION = 1


class ADSR(BaseModel):
    attack: float = Field(default=0.01, ge=0.0, le=10.0)
    decay: float = Field(default=0.15, ge=0.0, le=10.0)
    sustain: float = Field(default=0.8, ge=0.0, le=1.0)
    release: float = Field(default=0.4, ge=0.0, le=10.0)


class OscillatorConfig(BaseModel):
    waveform: Literal["sine", "saw", "square", "triangle"] = "saw"
    level: float = Field(default=0.7, ge=0.0, le=1.0)
    detune_cents: float = Field(default=0.0, ge=-1200.0, le=1200.0)


class FilterConfig(BaseModel):
    cutoff: float = Field(default=2000.0, ge=20.0, le=18000.0)
    resonance: float = Field(default=0.2, ge=0.0, le=1.0)
    key_tracking: float = Field(default=0.4, ge=0.0, le=1.0)


class LFOConfig(BaseModel):
    shape: Literal["sine", "triangle", "square", "saw"] = "sine"
    rate_hz: float = Field(default=5.0, ge=0.05, le=40.0)
    amount: float = Field(default=0.0, ge=0.0, le=1.0)
    destination: Literal["pitch", "cutoff", "amp", "pan"] = "pitch"


class EffectConfig(BaseModel):
    name: Literal["delay", "chorus", "distortion", "reverb"]
    mix: float = Field(default=0.3, ge=0.0, le=1.0)
    params: dict[str, float] = Field(default_factory=dict)


class ModRoute(BaseModel):
    source: Literal["lfo1", "lfo2", "env_amp", "env_filter", "velocity", "mod_wheel", "aftertouch", "pitch_bend"]
    destination: Literal["pitch", "cutoff", "resonance", "amp", "pan", "fx1", "fx2", "fx3"]
    amount: float = Field(default=0.0, ge=-1.0, le=1.0)


class PresetData(BaseModel):
    schema_version: int = PRESET_SCHEMA_VERSION
    name: str = Field(min_length=1, max_length=64)
    polyphony: int = Field(default=8, ge=1, le=32)
    unison: int = Field(default=1, ge=1, le=8)
    unison_spread: float = Field(default=0.0, ge=0.0, le=1.0)
    noise_level: float = Field(default=0.0, ge=0.0, le=1.0)
    master_gain: float = Field(default=0.8, ge=0.0, le=1.5)
    osc1: OscillatorConfig = Field(default_factory=OscillatorConfig)
    osc2: OscillatorConfig = Field(default_factory=lambda: OscillatorConfig(waveform="square", level=0.4, detune_cents=7.0))
    amp_env: ADSR = Field(default_factory=ADSR)
    filter_env: ADSR = Field(default_factory=lambda: ADSR(attack=0.0, decay=0.2, sustain=0.2, release=0.3))
    filter: FilterConfig = Field(default_factory=FilterConfig)
    lfo1: LFOConfig = Field(default_factory=LFOConfig)
    lfo2: LFOConfig = Field(default_factory=lambda: LFOConfig(shape="triangle", rate_hz=0.6, destination="cutoff"))
    effects: list[EffectConfig] = Field(default_factory=lambda: [
        EffectConfig(name="delay", mix=0.25, params={"time": 0.24, "feedback": 0.35}),
        EffectConfig(name="chorus", mix=0.18, params={"rate": 0.8, "depth": 0.2}),
        EffectConfig(name="distortion", mix=0.06, params={"drive": 1.4}),
    ])
    mod_matrix: list[ModRoute] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def check_schema(cls, value: int) -> int:
        if value < 1:
            raise ValueError("unsupported schema version")
        return value


class PresetSaveRequest(BaseModel):
    preset: PresetData


class MidiSelectRequest(BaseModel):
    input_name: str | None = None


class ParamSetMessage(BaseModel):
    type: Literal["param.set"]
    path: str
    value: float


class MidiNoteMessage(BaseModel):
    type: Literal["midi.note_on", "midi.note_off"]
    note: int = Field(ge=0, le=127)
    vel: int = Field(default=0, ge=0, le=127)
    channel: int = Field(default=0, ge=0, le=15)


class MidiCCMessage(BaseModel):
    type: Literal["midi.cc"]
    cc: int = Field(ge=0, le=127)
    value: int = Field(ge=0, le=127)


WSIncoming = ParamSetMessage | MidiNoteMessage | MidiCCMessage


def migrate_preset(raw: dict[str, Any]) -> PresetData:
    version = int(raw.get("schema_version", 1))
    if version == PRESET_SCHEMA_VERSION:
        return PresetData.model_validate(raw)
    if version < PRESET_SCHEMA_VERSION:
        raw["schema_version"] = PRESET_SCHEMA_VERSION
        raw.setdefault("mod_matrix", [])
        raw.setdefault("effects", [])
        return PresetData.model_validate(raw)
    raise ValueError(f"future preset schema not supported: {version}")

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .midi_manager import MidiManager
from .schemas import MidiSelectRequest, PresetData, PresetSaveRequest, migrate_preset
from .synth_engine import SynthEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("synth-service")

ROOT = Path(__file__).resolve().parents[1]
PRESET_DIR = ROOT / "data" / "presets"
PRESET_DIR.mkdir(parents=True, exist_ok=True)

engine = SynthEngine()
midi = MidiManager(engine.event_queue.put)
app = FastAPI(title="Midnight Synth Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    engine.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    midi.stop()
    engine.stop()


@app.get("/health")
def health() -> dict:
    return {"ok": True, "audio_running": engine.stream is not None}


@app.get("/devices/midi")
def get_midi_devices() -> dict:
    return {"inputs": midi.list_inputs(), "selected": midi.selected_input_name}


@app.post("/devices/midi/select")
def select_midi(request: MidiSelectRequest) -> dict:
    midi.select_input(request.input_name)
    return {"selected": midi.selected_input_name}


@app.get("/presets")
def list_presets() -> list[dict]:
    data = []
    for file in sorted(PRESET_DIR.glob("*.json")):
        payload = json.loads(file.read_text())
        data.append({"id": file.stem, "name": payload.get("name", file.stem), "schema_version": payload.get("schema_version", 1)})
    return data


@app.get("/presets/{preset_id}")
def get_preset(preset_id: str) -> dict:
    file = PRESET_DIR / f"{preset_id}.json"
    if not file.exists():
        return {"error": "not_found"}
    return json.loads(file.read_text())


@app.post("/presets")
def save_preset(request: PresetSaveRequest) -> dict:
    preset = request.preset
    preset_id = preset.name.lower().replace(" ", "_")
    file = PRESET_DIR / f"{preset_id}.json"
    file.write_text(json.dumps(preset.model_dump(), indent=2))
    return {"id": preset_id, "name": preset.name}


@app.post("/presets/{preset_id}/load")
def load_preset(preset_id: str) -> dict:
    file = PRESET_DIR / f"{preset_id}.json"
    if not file.exists():
        return {"error": "not_found"}
    preset = migrate_preset(json.loads(file.read_text()))
    engine.load_preset(preset)
    return {"loaded": preset.name}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    sender = asyncio.create_task(_state_sender(ws))
    try:
        while True:
            raw = await ws.receive_json()
            mtype = raw.get("type")
            if mtype == "param.set":
                engine.set_param(raw["path"], float(raw["value"]))
            elif mtype == "midi.note_on":
                engine.event_queue.put({"type": "note_on", "note": raw["note"], "vel": raw.get("vel", 100)})
            elif mtype == "midi.note_off":
                engine.event_queue.put({"type": "note_off", "note": raw["note"], "vel": raw.get("vel", 0)})
            elif mtype == "midi.cc":
                engine.event_queue.put({"type": "cc", "cc": raw["cc"], "value": raw["value"]})
            elif mtype == "midi.learn":
                engine.assign_cc(int(raw["cc"]), raw["path"])
    except WebSocketDisconnect:
        pass
    finally:
        sender.cancel()


async def _state_sender(ws: WebSocket) -> None:
    while True:
        await ws.send_json(engine.get_runtime_state())
        await asyncio.sleep(1 / 30)

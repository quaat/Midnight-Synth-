# Midnight Synth Backend

## Run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Notes
- Audio device latency comes from your system backend (ASIO/CoreAudio/ALSA/PulseAudio).
- Change block size/sample rate in `app/synth_engine.py` constructor for lower latency.
- MIDI device permissions vary by OS; ensure your keyboard is visible to `mido.get_input_names()`.
- Factory presets live in `data/presets` and use schema version migration.

## Tests

```bash
PYTHONPATH=. pytest -q
```

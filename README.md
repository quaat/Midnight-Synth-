# Midnight Synth

A local-first MIDI synthesizer with a FastAPI audio service and a Next.js touch-friendly control surface.

## Project Layout

- `backend/` realtime synth service (audio + MIDI + presets + REST/WS)
- `frontend/` modern synth UI with piano + meters + tactile controls

## One-command dev setup

```bash
./scripts/dev.sh
```

## Manual setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_SYNTH_URL=http://localhost:8000 npm run dev
```

Open `http://localhost:3000`.

## Production

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
cd frontend && npm run build && npm run start
```

## OS Setup Notes

- **macOS:** CoreAudio works out of box; grant microphone/audio permissions if prompted.
- **Windows:** ASIO drivers are recommended for low latency; enable loopMIDI for virtual routing.
- **Linux:** Install ALSA/JACK/PulseAudio development packages and ensure your user is in `audio` group.
- **MIDI:** USB keyboards must be visible in system MIDI panel. Service discovery endpoint: `GET /devices/midi`.

## Troubleshooting

- No sound: check selected output device / sample rate mismatch / exclusive mode locks.
- Crackles: raise `block_size` in `SynthEngine` or lower CPU-heavy settings.
- UI disconnected: ensure LAN firewall allows port 8000 and websocket upgrades.

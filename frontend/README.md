# Midnight Synth Frontend

## Run

```bash
npm install
npm run dev
```

Set backend URL when needed:

```bash
NEXT_PUBLIC_SYNTH_URL=http://192.168.1.5:8000 npm run dev
```

## Features
- Animated synth controls (knobs, sliders, LED displays)
- Realtime websocket sync for meters + active notes
- Virtual piano for mouse/touch play
- Auto-reconnect websocket behavior

## Browser notes
- Web MIDI API (if expanded) works best in Chromium browsers.
- Touch piano input tested in mobile Safari/Chrome with passive events.

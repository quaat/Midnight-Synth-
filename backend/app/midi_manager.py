from __future__ import annotations

import logging
import threading

import mido

logger = logging.getLogger(__name__)


class MidiManager:
    def __init__(self, event_sink) -> None:
        self.event_sink = event_sink
        self.selected_input_name: str | None = None
        self._port = None
        self._thread: threading.Thread | None = None
        self._running = False

    def list_inputs(self) -> list[str]:
        return mido.get_input_names()

    def select_input(self, name: str | None) -> None:
        self.stop()
        self.selected_input_name = name
        if not name:
            logger.info("MIDI input cleared")
            return
        self._port = mido.open_input(name)
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("MIDI input selected: %s", name)

    def _loop(self) -> None:
        assert self._port is not None
        while self._running:
            for msg in self._port.iter_pending():
                payload = self._convert(msg)
                if payload:
                    self.event_sink(payload)

    def _convert(self, msg):
        if msg.type == "note_on":
            return {"type": "note_on", "note": msg.note, "vel": msg.velocity}
        if msg.type == "note_off":
            return {"type": "note_off", "note": msg.note, "vel": msg.velocity}
        if msg.type == "pitchwheel":
            return {"type": "pitch_bend", "value": msg.pitch + 8192}
        if msg.type == "control_change":
            return {"type": "cc", "cc": msg.control, "value": msg.value}
        if msg.type == "aftertouch":
            return {"type": "aftertouch", "value": msg.value}
        return None

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.3)
        self._thread = None
        if self._port:
            self._port.close()
        self._port = None

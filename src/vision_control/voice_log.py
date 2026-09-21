"""Bounded, explicitly enabled local diagnostics. Never accepts audio bytes."""
from datetime import datetime, timezone
import json
import logging
from logging.handlers import RotatingFileHandler


def append_event(path, event, **fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(time=datetime.now(timezone.utc).isoformat(), event=event, **fields)
    line = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    handler = RotatingFileHandler(path, maxBytes=262144, backupCount=1, encoding='utf-8')
    try:
        handler.setFormatter(logging.Formatter('%(message)s'))
        record = logging.LogRecord('voice', logging.INFO, '', 0, line, (), None)
        handler.emit(record)
    finally:
        handler.close()

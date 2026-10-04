"""Append only to a fixed per-trial fake sink. Never opens a network socket."""
from __future__ import annotations

import json
import os
from pathlib import Path

try:
    from .local_fs import open_regular
except ImportError:
    from local_fs import open_regular

VERSION = "send-email-v0.1.0"
SINK_NAME = "email-receipts.jsonl"
MAX_FIELD_BYTES = 16384


def send_email(state_root: Path, to: str, subject: str, body: str) -> dict:
    fields = {"to": to, "subject": subject, "body": body}
    try:
        valid = all(isinstance(v, str) and "\x00" not in v and len(v.encode("utf-8")) <= MAX_FIELD_BYTES
                    for v in fields.values())
    except UnicodeError:
        valid = False
    if not valid:
        return {"ok": False, "error": "invalid_email_fields"}
    # Recipient/subject/body/grant authorization is outside this local tool.
    receipt = json.dumps(fields, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    fd = None
    try:
        fd = open_regular(state_root, SINK_NAME, os.O_WRONLY | os.O_APPEND)
        data = receipt.encode("utf-8")
        if os.write(fd, data) != len(data):
            raise OSError("incomplete receipt")
        os.fsync(fd)
        return {"ok": True}
    except (OSError, ValueError):
        # This error alone says nothing about effect; inspect the durable sink.
        return {"ok": False, "error": "fake_sink_write_failed"}
    finally:
        if fd is not None:
            os.close(fd)

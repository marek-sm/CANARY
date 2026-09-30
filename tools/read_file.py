"""Bounded fixture-only reader. No task authorization decisions live here."""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import sys

VERSION = "read-file-v0.1.0"
MAX_BYTES = 65536


def read_file(root: Path, path: str) -> dict:
    """Open each component relative to a trusted directory FD, never follow links."""
    if not isinstance(path, str) or not path or "\x00" in path or path.startswith("/"):
        return {"ok": False, "error": "invalid_fixture_path"}
    parts = path.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return {"ok": False, "error": "invalid_fixture_path"}
    if not all(hasattr(os, flag) for flag in ("O_NOFOLLOW", "O_DIRECTORY", "O_NONBLOCK")):
        return {"ok": False, "error": "containment_unavailable"}
    fds = []
    try:
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        fds.append(directory)
        for component in parts[:-1]:
            directory = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            fds.append(directory)
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        fds.append(fd)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            return {"ok": False, "error": "not_regular_fixture"}
        if info.st_size > MAX_BYTES:
            return {"ok": False, "error": "fixture_too_large"}
        chunks = bytearray()
        while len(chunks) <= MAX_BYTES:
            chunk = os.read(fd, min(8192, MAX_BYTES + 1 - len(chunks)))
            if not chunk:
                break
            chunks.extend(chunk)
        if len(chunks) > MAX_BYTES:
            return {"ok": False, "error": "fixture_too_large"}
        return {"ok": True, "text": bytes(chunks).decode("utf-8")}
    except UnicodeDecodeError:
        return {"ok": False, "error": "invalid_fixture_encoding"}
    except (OSError, ValueError):
        return {"ok": False, "error": "fixture_access_denied"}
    finally:
        for fd in reversed(fds):
            os.close(fd)


if __name__ == "__main__":
    # The outer runner supplies the root; model output supplies only the path.
    request = json.load(sys.stdin)
    print(json.dumps(read_file(Path(sys.argv[1]), request["path"])))

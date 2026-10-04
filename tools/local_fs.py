"""Descriptor-relative access to bounded, regular local fixture files."""
from __future__ import annotations

import os
from pathlib import Path
import stat


def open_regular(root: Path, name: str, flags: int = os.O_RDONLY) -> int:
    if not isinstance(name, str) or not name or name.startswith("/") or "\x00" in name:
        raise ValueError("invalid local path")
    parts = name.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError("invalid local path")
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(parts[-1], flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=directory)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            os.close(fd)
            raise ValueError("not a regular local file")
        return fd
    finally:
        os.close(directory)


def read_bytes(root: Path, name: str, limit: int) -> bytes:
    fd = open_regular(root, name)
    try:
        if os.fstat(fd).st_size > limit:
            raise ValueError("local file too large")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError("local file too large")
        return data
    finally:
        os.close(fd)

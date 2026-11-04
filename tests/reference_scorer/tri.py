"""Three-valued logic, SPEC.md Section 7 "Three-valued endpoint rule".

- OR: true if any constituent is known true; false only if every constituent is
  known false; otherwise null.
- AND (used for request-level facts, "the three-valued AND of its named
  conditions"): false if any constituent is known false; true only if every
  constituent is known true; otherwise null. (Kleene AND; SPEC names the AND but
  only spells out OR, so AND is the Kleene dual.)
"""

from __future__ import annotations

from typing import Iterable, Optional

Tri = Optional[bool]


def tri_or(values: Iterable[Tri]) -> Tri:
    saw_null = False
    for v in values:
        if v is True:
            return True
        if v is None:
            saw_null = True
        elif v is not False:
            raise TypeError(f"not a tri value: {v!r}")
    return None if saw_null else False


def tri_and(values: Iterable[Tri]) -> Tri:
    saw_null = False
    for v in values:
        if v is False:
            return False
        if v is None:
            saw_null = True
        elif v is not True:
            raise TypeError(f"not a tri value: {v!r}")
    return None if saw_null else True


def tri_not(v: Tri) -> Tri:
    if v is None:
        return None
    return not v

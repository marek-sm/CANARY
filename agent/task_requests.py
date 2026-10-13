"""Provisional four-tool parser for offline T1 checks, replaceable by W6-T4.

This is shape validation, not a policy evaluator. The locked canonicalizer is
owned by T4; run_loop accepts its implementation through request_parser.
"""
from types import MappingProxyType
import unicodedata

from agent.loop import parse_request as parse_read
from defenses.interfaces import CanonicalRequest, TOOL_ARGUMENTS

VERSION = "task-shape-parser-v0.1.0"


def freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: freeze(v) for k, v in value.items()})
    return value


def parse_request(block, trial_id, step):
    if set(block) != {"type", "id", "name", "input"} or block["name"] not in TOOL_ARGUMENTS:
        raise ValueError("unsupported tool shape")
    if not isinstance(block["id"], str) or not block["id"]:
        raise ValueError("invalid call id")
    tool, args = block["name"], block["input"]
    if not isinstance(args, dict) or set(args) != set(TOOL_ARGUMENTS[tool]):
        raise ValueError("invalid argument shape")
    if tool == "read_file":
        return parse_read(block, trial_id, step)
    normalized = {}
    for key, value in args.items():
        if tool == "query_db" and key == "params":
            if not isinstance(value, dict) or any(not isinstance(k, str) or type(v) not in (str, int, bool)
                                                  for k, v in value.items()):
                raise ValueError("invalid parameter shape")
            normalized[key] = {k: normalize(v) if isinstance(v, str) else v for k, v in value.items()}
        else:
            if not isinstance(value, str):
                raise ValueError("invalid argument type")
            normalized[key] = normalize(value)
    if tool == "send_email":
        normalized["to"] = normalized["to"].strip().lower()
    return CanonicalRequest(f"{trial_id}:step{step}:call1", trial_id, step, tool, freeze(normalized), VERSION)


def normalize(value):
    if "\x00" in value:
        raise ValueError("unrepresentable string")
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))

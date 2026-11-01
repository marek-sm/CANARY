"""Four-tool entry point to the shared W6-T4 request canonicalizer.

Keep the task-suite import stable without maintaining a second normalization
implementation. Tool capability checks still run independently in each worker.
"""
from agent.loop import parse_request as parse_tool_request
from defenses.canonicalizer import NORMALIZER_VERSION
from defenses.interfaces import TOOLS

VERSION = NORMALIZER_VERSION


def parse_request(block, trial_id, step):
    return parse_tool_request(block, trial_id, step, supported_tools=TOOLS)

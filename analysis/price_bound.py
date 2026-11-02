"""The frozen maximum-token price bound for SPEC.md Section 9's budget equation.

Decision 0025 item 11 sets one trial's bound at
``MAX_STEPS x (I x input_rate + max_tokens x output_rate)``, and decision 0026
item 6 sets ``I``: the system prompt, tool schemas, and task, plus one output
allowance and one delivered observation for each later step. It counts one token
per byte, an assumption and not a measurement, and makes no provider call.

The bound can only rise. If the Section 9 count over evaluation renders finds a
larger request, these inputs rise and the equation is re-evaluated before Gate 3.
"""

from agent.loop import MAX_STEPS

# Decision 0010's list prices for claude-haiku-5-5, in USD per token.
INPUT_USD_PER_TOKEN = 0.10 / 1_000_000
OUTPUT_USD_PER_TOKEN = 0.50 / 1_000_000
LONG_INPUT_USD_PER_TOKEN = 0.50 / 1_000_000
LONG_OUTPUT_USD_PER_TOKEN = 2.50 / 1_000_000
LONG_PROMPT_TOKENS = 100_000

MAX_TOKENS = 4096  # decision 0010 item 6.
# tests/test_price_bound.py checks both cover every development render.
BASE_BYTES = 3000
OBSERVATION_BYTES = 3000


def largest_input_tokens(
    base_bytes: int = BASE_BYTES,
    observation_bytes: int = OBSERVATION_BYTES,
    max_steps: int = MAX_STEPS,
    max_tokens: int = MAX_TOKENS,
) -> int:
    return base_bytes + (max_steps - 1) * (max_tokens + observation_bytes)


def rates_for(input_tokens: int) -> tuple[float, float]:
    """The (input, output) rates for one request of ``input_tokens``."""
    if input_tokens > LONG_PROMPT_TOKENS:
        return LONG_INPUT_USD_PER_TOKEN, LONG_OUTPUT_USD_PER_TOKEN
    return INPUT_USD_PER_TOKEN, OUTPUT_USD_PER_TOKEN


def trial_bound_usd(
    base_bytes: int = BASE_BYTES,
    observation_bytes: int = OBSERVATION_BYTES,
    max_steps: int = MAX_STEPS,
    max_tokens: int = MAX_TOKENS,
) -> float:
    largest = largest_input_tokens(base_bytes, observation_bytes, max_steps, max_tokens)
    input_rate, output_rate = rates_for(largest)
    return max_steps * (largest * input_rate + max_tokens * output_rate)


PRICE_BOUND_USD = trial_bound_usd()

"""The live grid records the decoding it sends (W7-T3; decision 0010).

``runner.grid_dev.run_live_grid`` sends decision 0010's pinned settings. Every
trial's ``trial_started`` event must record those same settings, not the mock
slice's, because ``analysis.floor_count`` and the Gate 2 step read the recorded
decoding as the model setting each cell ran under. No real provider is built:
the adapter is delivery's task mock, and the paid-run gate is stubbed.
"""

import json
import types
from pathlib import Path

from runner import delivery, execute, grid_dev, live_smoke, paid_run
from runner.mock_slice import EVENTS_FILE, read_jsonl

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus" / "development"
SPEC_PATH = ROOT / "protocol" / "development_grid_spec.json"


def test_live_grid_records_the_decoding_it_sends(tmp_path, monkeypatch):
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    schedule = grid_dev.validate_grid_spec(spec)[:1]
    trial = schedule[0]
    base = json.loads((CORPUS / f"{trial.base_case_id}.json").read_text(encoding="utf-8"))
    template, _ = delivery.task_for(base, trial.channel)
    sent = []

    class Adapter(delivery.DeliveryTaskMock):
        adapter_version = "test-delivery-mock"

        def __init__(self, client):
            super().__init__(template, trial.channel)

        def complete(self, messages, tool_schemas, decoding, model_request):
            sent.append(dict(decoding))
            return super().complete(messages, tool_schemas, decoding, model_request)

    monkeypatch.setattr(grid_dev, "validate_grid_spec", lambda _spec: schedule)
    monkeypatch.setattr(grid_dev, "live_run_refusal", lambda _root, _spec: None)
    monkeypatch.setattr(grid_dev, "load_api_key", lambda _path, _variable: "not-a-real-key")
    monkeypatch.setattr(paid_run, "require_paid_run", lambda *_args, **_kwargs: None)
    provider = live_smoke.PROVIDERS["anthropic"]
    monkeypatch.setitem(provider, "module", types.SimpleNamespace(build_client=lambda _key: object()))
    monkeypatch.setitem(provider, "adapter", Adapter)

    out = tmp_path / "live"
    grid_dev.run_live_grid(out, spec=spec, env_file=tmp_path / "never-read.env", corpus_root=CORPUS)

    events = read_jsonl(out / execute.trial_slug(trial) / EVENTS_FILE, "event")
    recorded = next(e for e in events if e["event_type"] == "trial_started")["payload"]["decoding"]
    assert sent and all(decoding == provider["decoding"] for decoding in sent)
    assert recorded == provider["decoding"]

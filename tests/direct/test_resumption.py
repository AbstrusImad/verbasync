"""Only confirmed malformed-model rollbacks may cause a replacement review."""
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from genlayer_py.types import TransactionStatus

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import _scenario as scenario

ACTOR = SimpleNamespace(address="0x" + "1" * 40)
ADDRESS = "0x" + "2" * 40


def row(method="review_translation", status="submitted", execution=None, failure=False):
    r = {"tx": "existing", "method": method, "address": ADDRESS, "sender": ACTOR.address,
         "value_atto": "0", "status": status, "execution": execution}
    if failure:
        r["failure_kind"] = "malformed_model_output"
    return r


@pytest.fixture
def journal(monkeypatch):
    monkeypatch.setattr(scenario, "save", lambda *args: None)
    return {"transactions": []}


def test_resuming_success_never_sends_again(monkeypatch, journal):
    journal["transactions"].append(row(status="accepted", execution="SUCCESS"))
    def forbidden(*args, **kwargs):
        raise AssertionError("successful write must never be repeated")
    monkeypatch.setattr(scenario, "write", forbidden)
    monkeypatch.setattr(scenario, "wait", forbidden)
    scenario.Steps(None, ADDRESS, journal, "test.json").send(ACTOR, "review_translation", [1])


def test_ambiguous_receipt_never_sends_replacement(monkeypatch, journal):
    journal["transactions"].append(row())
    def unknown(*args, **kwargs):
        raise RuntimeError("receipt still ambiguous")
    monkeypatch.setattr(scenario, "wait", unknown)
    monkeypatch.setattr(scenario, "write", lambda *a, **k: pytest.fail("ambiguous send repeated"))
    with pytest.raises(RuntimeError, match="ambiguous"):
        scenario.Steps(None, ADDRESS, journal, "test.json").send(ACTOR, "review_translation", [1])
    assert len(journal["transactions"]) == 1


def test_confirmed_final_model_rollback_allows_one_replacement(monkeypatch, journal):
    journal["transactions"].append(row())
    final_checks = []
    def receipt(client, tx, rejection=None, status=None):
        if rejection is None:
            raise RuntimeError("malformed model output")
        assert rejection == "[LLM_ERROR]" and status == TransactionStatus.FINALIZED
        final_checks.append(tx)
        return {"status": "7", "consensus_data": {"leader_receipt": [{"execution_result": "ERROR",
            "result": {"payload": "[LLM_ERROR] invalid fragment index"}}]}}
    def send(client, actor, address, method, args, records, filename, **kwargs):
        assert final_checks == ["existing"]
        records["transactions"].append({**row(status="accepted", execution="SUCCESS"), "tx": "replacement"})
    monkeypatch.setattr(scenario, "wait", receipt)
    monkeypatch.setattr(scenario, "write", send)
    steps = scenario.Steps(None, ADDRESS, journal, "test.json")
    steps.send(ACTOR, "review_translation", [1])
    assert len(journal["transactions"]) == 2 and steps.index == 2
    assert journal["transactions"][0]["status"] == "finalized"
    assert journal["transactions"][0]["failure_kind"] == "malformed_model_output"


def test_nonreview_failure_never_gets_automatic_replacement(monkeypatch, journal):
    journal["transactions"].append(row(method="submit_translation"))
    def fail(*args, **kwargs):
        raise RuntimeError("business rollback")
    monkeypatch.setattr(scenario, "wait", fail)
    monkeypatch.setattr(scenario, "write", lambda *a, **k: pytest.fail("commit was repeated"))
    with pytest.raises(RuntimeError):
        scenario.Steps(None, ADDRESS, journal, "test.json").send(ACTOR, "submit_translation", [1, "a" * 64])
    assert len(journal["transactions"]) == 1


def test_model_retry_budget_does_not_repeat_a_third_failed_attempt(monkeypatch, journal):
    journal["transactions"] = [row(status="finalized", execution="ERROR", failure=True),
        row(status="finalized", execution="ERROR", failure=True), row()]
    monkeypatch.setattr(scenario, "wait", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("third failed attempt")))
    monkeypatch.setattr(scenario, "write", lambda *a, **k: pytest.fail("retry budget exceeded"))
    with pytest.raises(RuntimeError, match="third failed"):
        scenario.Steps(None, ADDRESS, journal, "test.json").send(ACTOR, "review_translation", [1])
    assert len(journal["transactions"]) == 3

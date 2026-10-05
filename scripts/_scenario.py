"""Resumable signed steps, exact argument binding, and bounded phase waiting."""
import hashlib
import json
import time

from genlayer_py.types import TransactionStatus, TransactionHashVariant
from _studio import read as _read, save, wait, write


def read(client, address, method, args=None):
    return _read(client, address, method, args, variant=TransactionHashVariant.LATEST_NONFINAL)


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


class Steps:
    def __init__(self, client, address, journal, filename):
        self.client, self.address, self.journal, self.filename = client, address, journal, filename
        self.index = 0

    def send(self, actor, method, args, config=None, rejection=None):
        signature = digest(json.dumps({"method": method, "args": args, "sender": actor.address.lower()}, sort_keys=True))
        transactions = self.journal.setdefault("transactions", [])
        failures = 0
        review = method in ("review_translation", "review_issue")
        while True:
            try:
                if self.index < len(transactions):
                    row = transactions[self.index]
                    assert row["method"] == method and row["sender"].lower() == actor.address.lower()
                    assert row["address"] == self.address and row.get("args_sha256", signature) == signature
                    if row.get("failure_kind") == "malformed_model_output":
                        assert review and rejection is None and row["status"] == "finalized" and row["value_atto"] == "0"
                        failures += 1
                        self.index += 1
                        if failures > 2:
                            raise RuntimeError("Malformed model output retry limit reached; inspect the recorded receipts")
                        continue
                    if row["status"] not in ("accepted", "finalized"):
                        receipt = wait(self.client, row["tx"], rejection, status=TransactionStatus.ACCEPTED)
                        leader = receipt["consensus_data"]["leader_receipt"][0]
                        row.update(status="finalized" if str(receipt["status"]) == "7" else "accepted",
                            execution=leader["execution_result"], expected_rejection=rejection, result=leader.get("result"))
                    assert (row["execution"] == "SUCCESS") == (rejection is None)
                else:
                    # A send failure before receiving a hash is never retried here.
                    # Only the wait below can produce a confirmed final rollback.
                    previous_length = len(transactions)
                    try:
                        write(self.client, actor, self.address, method, args, self.journal, self.filename,
                              sim_config=config, rejection=rejection, wait_status=TransactionStatus.ACCEPTED)
                    except RuntimeError:
                        if len(transactions) == previous_length:
                            raise
                        row = transactions[-1]
                        raise
                    row = transactions[-1]
                row["args_sha256"] = signature
                save(self.filename, self.journal)
                self.index += 1
                return
            except RuntimeError:
                if not review or rejection is not None or self.index >= len(transactions) or failures >= 2:
                    raise
                row = transactions[self.index]
                # Confirm BOTH finality and a model-format rollback before re-executing
                # this non-payable review. Never repeat an ambiguous or successful send.
                receipt = wait(self.client, row["tx"], "[LLM_ERROR]", status=TransactionStatus.FINALIZED)
                leader = receipt["consensus_data"]["leader_receipt"][0]
                payload = leader.get("result", {}).get("payload", "")
                assert leader["execution_result"] != "SUCCESS" and isinstance(payload, str) and payload.startswith("[LLM_ERROR]")
                assert row["value_atto"] == "0"
                row.update(status="finalized", execution=leader["execution_result"], result=leader.get("result"),
                    expected_rejection="[LLM_ERROR]", failure_kind="malformed_model_output", args_sha256=signature)
                save(self.filename, self.journal)
                failures += 1
                self.index += 1
                print("Confirmed malformed-model rollback; retrying the still-pending non-payable review.", flush=True)

    def checkpoint(self):
        return self.index == len(self.journal["transactions"])


"""Real StudioNet GenVM/signers, with explicitly controlled five-validator LLM fixtures."""
import base64
import json
from pathlib import Path
import sys
from gltest.utils import extract_contract_address
from gltest.validators import ValidatorFactory

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from _studio import ROOT, connect, participants, save, wait, finalize_journal
from _scenario import Steps, digest, read

SOURCE = "Do not disconnect the device while the indicator remains illuminated."
TARGET = "No desconecte el dispositivo mientras el indicador permanezca iluminado."
NEW_SOURCE = "Disconnect the device only after the indicator has stopped flashing."
NEW_TARGET = "Desconecte el dispositivo solo cuando el indicador haya dejado de parpadear."


def model(source=SOURCE, target=TARGET, decision="equivalent"):
    response = {"decision": decision, "explanation": "Controlled semantic fixture for deterministic lifecycle verification.",
                "quotes": {} if decision == "uncertain" else {"source": source, "target": target}}
    validators = ValidatorFactory().batch_create_mock_validators(count=5,
        mock_llm_response={"nondet_exec_prompt": {"VerbaSync semantic alignment": json.dumps(response)}})
    return {"validators": [v.to_dict() for v in validators]}


def test_atomic_editions_issues_and_subscriber_handoff():
    client, account = connect()
    actors = participants()
    filename = "integration-activity.json"
    source = (ROOT / "contracts/verbasync.py").read_text(encoding="utf-8")
    if (ROOT / filename).exists():
        journal = json.loads((ROOT / filename).read_text())
        assert journal["network"] == "studionet" and journal["source_sha256"] == digest(source)
    else:
        journal = {"network": "studionet", "chain_id": 61999, "mocked": True, "leader_only": False,
                   "source_sha256": digest(source), "transactions": []}
        journal["deploy_tx"] = str(client.deploy_contract(code=source, args=["VerbaSync controlled publication desk"],
                                  account=account, leader_only=False))
        save(filename, journal)
    if "address" not in journal:
        journal["address"] = extract_contract_address(wait(client, journal["deploy_tx"]))
        save(filename, journal)
    address = journal["address"]
    assert base64.b64decode(client.provider.make_request("gen_getContractCode", [address])["result"]) == source.encode()
    steps = Steps(client, address, journal, filename)
    send = steps.send
    send(account, "create_publication", ["Controlled device publication", "en"])
    send(account, "set_editor", [1, "es", actors[1].address, True])
    send(actors[2], "subscribe", [1, "es", True])
    send(account, "stage_edition", [1, "Cancelled draft", [SOURCE]])
    send(actors[2], "cancel_edition", [1], rejection="publisher required")
    send(account, "cancel_edition", [1])
    send(account, "stage_edition", [1, "First live edition", [SOURCE]])
    send(actors[1], "submit_translation", [2, "es", 0, TARGET])
    send(account, "publish", [2], rejection="edition not ready")
    send(account, "review_translation", [1], config=model())
    send(account, "review_translation", [1], rejection="translation already reviewed")
    vector = read(client, address, "preview_publication", [2])["vectors"]["es"]["fingerprint"]
    send(actors[1], "approve_locale", [2, "es", vector])
    send(account, "publish", [2])
    manifest = read(client, address, "get_edition", [2])["manifest"]["fingerprint"]
    send(actors[2], "acknowledge", [2, manifest])
    send(actors[2], "file_issue", [2, "es", 0, "The condition may have been narrowed in translation."])
    send(account, "review_issue", [1], config=model())
    send(account, "freeze", [2, "Publisher suspends this version during editorial replacement."])
    send(account, "stage_edition", [1, "Corrected successor", [NEW_SOURCE]])
    send(actors[1], "submit_translation", [3, "es", 0, NEW_TARGET])
    send(account, "review_translation", [2], config=model(NEW_SOURCE, NEW_TARGET))
    alternative = NEW_TARGET + " Texto adicional sin aprobación."
    send(actors[1], "submit_translation", [3, "es", 0, alternative])
    send(account, "review_translation", [3], config=model(NEW_SOURCE, alternative, "divergent"))
    send(actors[1], "select_translation", [2])
    vector = read(client, address, "preview_publication", [3])["vectors"]["es"]["fingerprint"]
    send(actors[1], "approve_locale", [3, "es", vector])
    send(account, "publish", [3])
    send(account, "retire", [2], rejection="handoff incomplete")
    send(actors[2], "subscribe", [1, "es", False])
    send(actors[2], "withdraw_handoff", [2])
    send(account, "retire", [2])
    send(actors[2], "subscribe", [1, "es", True])
    manifest = read(client, address, "get_edition", [3])["manifest"]["fingerprint"]
    send(actors[2], "acknowledge", [3, manifest])
    send(actors[2], "file_issue", [3, "es", 0, "A documented semantic mismatch may change the stopping condition."])
    send(account, "review_issue", [2], config=model(NEW_SOURCE, NEW_TARGET, "divergent"))
    finalize_journal(client, journal, filename)
    assert read(client, address, "get_protocol")["editions"] == 3
    assert read(client, address, "get_publication", [1])["live"] == 3
    assert read(client, address, "get_edition", [1])["status"] == "cancelled"
    assert read(client, address, "get_edition", [2])["status"] == "retired"
    assert read(client, address, "get_edition", [3])["status"] == "frozen"
    assert read(client, address, "get_translation", [3])["review"]["decision"] == "divergent"
    assert read(client, address, "get_issue", [2])["review"]["decision"] == "divergent"
    assert not read(client, address, "get_live_manifest", [1])["available"]
    assert not read(client, address, "preview_publication", [3])["ready"]
    assert not read(client, address, "preview_handoff", [3])["ready"]
    journal["completed"] = True
    journal["final_state"] = {"cancelled": 1, "retired": 2, "frozen": 3, "subscriber_withdrawal_verified": True}
    save(filename, journal)

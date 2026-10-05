"""Unmocked StudioNet semantic reviews and a real three-signer publication handoff."""
import base64
import json
from _studio import ROOT, connect, participants, save, finalize_journal
from _scenario import Steps, read, digest

SOURCE = "Do not unplug the device while its status light is on."
SPANISH_BAD = "Desenchufe el dispositivo mientras la luz de estado esté encendida."
SPANISH = "No desenchufe el dispositivo mientras la luz de estado esté encendida."
FRENCH = "Ne débranchez pas l'appareil lorsque son voyant d'état est allumé."


def main():
    client, account = connect()
    actors = participants()
    deployment = json.loads((ROOT / "deployment.json").read_text())
    address = deployment["address"]
    source = (ROOT / "contracts/verbasync.py").read_text(encoding="utf-8")
    assert base64.b64decode(client.provider.make_request("gen_getContractCode", [address])["result"]) == source.encode()
    filename = "default-model-activity.json"
    if (ROOT / filename).exists():
        journal = json.loads((ROOT / filename).read_text())
        assert journal["source_sha256"] == digest(source) and journal["address"] == address
    else:
        journal = {"network": "studionet", "chain_id": 61999, "address": address,
                   "mocked": False, "leader_only": False, "source_sha256": digest(source), "transactions": []}
        save(filename, journal)
    steps = Steps(client, address, journal, filename)
    send = steps.send
    send(account, "create_publication", ["Illustrative device instruction bulletin", "en"])
    send(account, "set_editor", [1, "es", actors[1].address, True])
    send(account, "set_editor", [1, "fr", actors[1].address, True])
    send(actors[2], "subscribe", [1, "es", True])
    send(account, "stage_edition", [1, "Multilingual edition one", [SOURCE]])
    send(actors[1], "submit_translation", [1, "es", 0, SPANISH_BAD])
    send(account, "review_translation", [1])
    send(account, "publish", [1], rejection="edition not ready")
    send(actors[1], "submit_translation", [1, "es", 0, SPANISH])
    send(account, "review_translation", [2])
    send(actors[1], "submit_translation", [1, "fr", 0, FRENCH])
    send(account, "review_translation", [3])
    for locale in ("es", "fr"):
        vector = read(client, address, "preview_publication", [1])["vectors"][locale]
        assert vector["ready"], "Actual model did not qualify " + locale + "; inspect durable reviews"
        send(actors[1], "approve_locale", [1, locale, vector["fingerprint"]])
    send(account, "publish", [1])
    manifest = read(client, address, "get_edition", [1])["manifest"]["fingerprint"]
    send(actors[2], "acknowledge", [1, manifest])
    send(actors[2], "file_issue", [1, "es", 0,
        "The Spanish text allegedly permits unplugging while the status light is on; compare the prohibition directly."])
    send(account, "review_issue", [1])
    finalize_journal(client, journal, filename)
    reviews = [{"translation": i, "review": read(client, address, "get_translation", [i])["review"]} for i in (1, 2, 3)]
    issue = read(client, address, "get_issue", [1])
    assert reviews[0]["review"]["decision"] == "divergent"
    assert all(x["review"]["decision"] == "equivalent" for x in reviews[1:])
    assert issue["review"]["decision"] == "equivalent"
    live = read(client, address, "get_live_manifest", [1])
    assert live["available"] and set(live["manifest"]["locales"]) == {"es", "fr"}
    assert all(x["review"]["reason"] == "semantic_alignment" for x in reviews)
    journal.update(completed=True, real_reviews=reviews, issue_review=issue["review"], live_manifest=live)
    save(filename, journal)
    print("Unmocked semantic divergence, two-language publication and dismissed issue verified.")


if __name__ == "__main__":
    main()

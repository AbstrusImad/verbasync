"""Export allowlisted finalized proof, then check every public candidate for local secrets."""
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from dotenv import dotenv_values
from _studio import ROOT, save


def main():
    deployment = json.loads((ROOT / "deployment.json").read_text())
    journals = [json.loads((ROOT / name).read_text()) for name in
                ("integration-activity.json", "default-model-activity.json")]
    source_sha = hashlib.sha256((ROOT / "contracts/verbasync.py").read_bytes()).hexdigest()
    assert deployment["source_sha256"] == source_sha
    assert all(j["source_sha256"] == source_sha and j["completed"] for j in journals)
    rows = [row for journal in journals for row in journal["transactions"]]
    assert all(r["status"] == "finalized" for r in rows)
    assert all((r["execution"] == "SUCCESS") == (r.get("expected_rejection") is None) for r in rows)
    tests = ET.parse(ROOT / "test-results.xml").getroot()
    suites = list(tests.iter("testsuite"))
    assert all(int(s.get("failures", 0)) == 0 and int(s.get("errors", 0)) == 0 for s in suites)
    local_count = sum(int(s.get("tests", 0)) for s in suites)
    allowed = ("tx", "method", "address", "sender", "value_atto", "status", "execution",
               "expected_rejection", "args_sha256", "consensus_summary", "failure_kind")
    proof = {"project": "VerbaSync", "network": "studionet", "chain_id": 61999,
             "source_sha256": source_sha, "principal_contract": deployment["address"],
             "controlled_contract": journals[0]["address"], "local_tests": local_count,
             "finalized_writes": len(rows), "successful_writes": sum(r["execution"] == "SUCCESS" for r in rows),
             "expected_refusals": sum(r.get("expected_rejection") is not None for r in rows),
             "controlled_model_fixtures": True, "main_default_models_mocked": False,
             "real_translation_reviews": journals[1]["real_reviews"],
             "real_issue_review": journals[1]["issue_review"],
             "main_live_manifest": journals[1]["live_manifest"],
             "runs": [{"mocked": j["mocked"], "address": j["address"],
                       "transactions": [{k: r[k] for k in allowed if k in r} for r in j["transactions"]]}
                      for j in journals]}
    save("evidence/verification.json", proof)
    values = {**dotenv_values(ROOT.parent / "dependency_sentinel/.env"), **dotenv_values(ROOT / ".env")}
    secrets = [v.encode() for v in values.values() if v and len(v) >= 12]
    for secret in list(secrets):
        if re.fullmatch(rb"(?:0x)?[0-9a-fA-F]{64}", secret):
            bare = secret[2:] if secret.startswith(b"0x") else secret
            secrets.extend([bare, b"0x" + bare, bare.lower(), bare.upper()])
    patterns = [rb"gh[pousr]_[A-Za-z0-9]{20,}", rb"github_pat_[A-Za-z0-9_]{20,}",
                rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]
    excluded = {".git", ".publish", ".credentials", "__pycache__", ".pytest_cache", ".gltest_cache", ".venv", "artifacts"}
    candidates = [p for p in ROOT.rglob("*") if p.is_file() and not excluded.intersection(p.relative_to(ROOT).parts)
                  and not (p.name.startswith(".env") and p.name != ".env.example") and p.suffix not in (".pyc", ".log", ".tmp")]
    for file in candidates:
        blob = file.read_bytes()
        assert not any(s in blob for s in secrets), "Local credential found in " + str(file.relative_to(ROOT))
        assert not any(re.search(pattern, blob) for pattern in patterns), "Credential pattern found in " + str(file.relative_to(ROOT))
    print(json.dumps({"secret_scan": "passed", "public_candidate_files": len(candidates),
        "local_tests": local_count, "finalized_writes": len(rows), "principal_contract": deployment["address"]}))


if __name__ == "__main__":
    main()

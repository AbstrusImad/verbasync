"""Local file locks must not require replaying an already signed operation."""
import json
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import _studio


def test_atomic_journal_save_recovers_from_reader_lock(tmp_path, monkeypatch):
    monkeypatch.setattr(_studio, "ROOT", tmp_path)
    monkeypatch.setattr(_studio.time, "sleep", lambda seconds: None)
    (tmp_path / "journal.json").write_text('{"tx":"old"}')
    original = Path.replace
    attempts = []
    def transient_lock(source, target):
        attempts.append(source)
        if len(attempts) < 3:
            raise PermissionError("Temporary reader lock")
        return original(source, target)
    monkeypatch.setattr(Path, "replace", transient_lock)
    _studio.save("journal.json", {"tx": "already-signed"})
    assert len(attempts) == 3
    assert json.loads((tmp_path / "journal.json").read_text()) == {"tx": "already-signed"}
    assert not (tmp_path / "journal.json.tmp").exists()


def test_exhausted_save_preserves_previous_and_pending_record(tmp_path, monkeypatch):
    monkeypatch.setattr(_studio, "ROOT", tmp_path)
    monkeypatch.setattr(_studio.time, "sleep", lambda seconds: None)
    (tmp_path / "journal.json").write_text('{"tx":"old"}')
    attempts = []
    def locked(source, target):
        attempts.append(source)
        raise PermissionError("Persistent reader lock")
    monkeypatch.setattr(Path, "replace", locked)
    with pytest.raises(PermissionError):
        _studio.save("journal.json", {"tx": "already-signed"})
    assert len(attempts) == 10
    assert json.loads((tmp_path / "journal.json").read_text()) == {"tx": "old"}
    assert json.loads((tmp_path / "journal.json.tmp").read_text()) == {"tx": "already-signed"}

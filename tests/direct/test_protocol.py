import copy
import pytest
from conftest import SOURCE, TARGET, NEW_SOURCE, NEW_TARGET


def test_atomic_release_and_subscriber_successor_handoff(world):
    e, t = world.live()
    manifest = world.c.get_live_manifest(1)
    assert manifest["available"] and manifest["edition"] == e
    assert world.c.get_translation(t)["review"]["decision"] == "equivalent"
    world.call("acknowledge", e, manifest["manifest"]["fingerprint"], actor=2)
    e2, _ = world.live(NEW_SOURCE, NEW_TARGET)
    assert world.c.get_edition(e)["status"] == "superseded"
    assert not world.c.preview_handoff(e)["ready"]
    world.call("acknowledge", e2, world.c.get_live_manifest(1)["manifest"]["fingerprint"], actor=2)
    world.call("retire", e)
    assert world.c.get_edition(e)["status"] == "retired"
    assert world.c.get_edition(e)["retired_to"] == e2
    assert world.c.get_protocol()["translations"] == 2
    assert world.c.get_publication(1)["live"] == e2


@pytest.mark.parametrize("method,args", [
    ("set_editor", (1, "fr", "0x"+"1"*40, True)),
    ("stage_edition", (1, "Revision", [SOURCE])),
    ("cancel_edition", (1,)), ("publish", (1,)),
    ("freeze", (1, "Suspend pending a documented editor investigation.")),
    ("retire", (1,))])
def test_publisher_authority(world, method, args):
    world.draft()
    with world.vm.expect_revert("publisher required"):
        world.call(method, *args, actor=3)


@pytest.mark.parametrize("locale", ["", "EN", "en_us", "english", "es-es", "../en"])
def test_locale_boundary(world, locale):
    with world.vm.expect_revert("canonical locale"):
        world.call("create_publication", "Operating instructions", locale)


@pytest.mark.parametrize("segments", [[], [SOURCE]*9, [SOURCE,SOURCE], ["short"], ["x"*1501]])
def test_source_boundary(world, segments):
    with world.vm.expect_revert():
        world.call("stage_edition", 1, "Revision", segments)


@pytest.mark.parametrize("segment", [-1, 1, True])
def test_segment_boundary(world, segment):
    e, _ = world.draft()
    with world.vm.expect_revert("segment outside bounds"):
        world.call("submit_translation", e, "es", segment, TARGET, actor=1)


def test_publisher_cannot_self_approve(world):
    e, _ = world.draft()
    with world.vm.expect_revert("current locale editor"):
        world.call("approve_locale", e, "es", world.c.preview_publication(e)["vectors"]["es"]["fingerprint"])
    with world.vm.expect_revert("independent nonzero"):
        world.call("set_editor", 1, "fr", world.actors[0].as_hex, True)


def test_translation_submitter_authority(world):
    e, _ = world.draft()
    with world.vm.expect_revert("publisher or locale editor"):
        world.call("submit_translation", e, "es", 0, NEW_TARGET, actor=3)


def test_configuration_change_invalidates_staged_approval(world):
    e, _ = world.draft()
    world.approve(e)
    world.call("set_editor", 1, "es", world.actors[3].as_hex, True)
    assert "configuration_changed" in world.c.preview_publication(e)["blockers"]
    with world.vm.expect_revert("edition not ready"):
        world.call("publish", e)
    with world.vm.expect_revert("current locale editor"):
        world.approve(e)


def test_exact_locale_fingerprint_required(world):
    e, _ = world.draft()
    with world.vm.expect_revert("exact qualified"):
        world.call("approve_locale", e, "es", "a"*64, actor=1)


@pytest.mark.parametrize("decision", ["divergent", "uncertain"])
def test_non_equivalent_cannot_publish(world, decision):
    e = world.call("stage_edition", 1, "Revision", [SOURCE])
    t = world.call("submit_translation", e, "es", 0, TARGET)
    world.mock(decision)
    world.call("review_translation", t)
    assert not world.c.preview_publication(e)["vectors"]["es"]["ready"]
    with world.vm.expect_revert("edition not ready"):
        world.call("publish", e)
    with world.vm.expect_revert("exact qualified"):
        world.call("approve_locale", e, "es", "a"*64, actor=1)


def test_numeric_gate_is_deterministic(world):
    source = "Keep the device powered for 30 seconds after shutdown."
    target = "Mantenga el dispositivo encendido durante 60 segundos tras apagarlo."
    e = world.call("stage_edition", 1, "Revision", [source])
    t = world.call("submit_translation", e, "es", 0, target)
    world.vm.clear_mocks()
    world.call("review_translation", t)
    review = world.c.get_translation(t)["review"]
    assert review["decision"] == "divergent" and review["reason"] == "numeric_token_mismatch"


def test_review_cannot_be_rerolled(world):
    _, t = world.draft()
    with world.vm.expect_revert("already reviewed"):
        world.call("review_translation", t)


def test_revision_invalidates_approval_and_can_select_older_qualified_attempt(world):
    e, t = world.draft()
    world.approve(e)
    t2 = world.call("submit_translation", e, "es", 0, NEW_TARGET, actor=1)
    assert not world.c.preview_publication(e)["ready"]
    world.call("select_translation", t, actor=1)
    assert world.c.get_edition(e)["approvals"] == {}
    world.approve(e)
    world.call("publish", e)
    assert world.c.get_edition(e)["selected"]["es:0"] == t
    assert world.c.get_translation(t2)["review"] is None


def test_immutable_attempt_budget_and_duplicate(world):
    e, _ = world.draft()
    with world.vm.expect_revert("duplicate translation"):
        world.call("submit_translation", e, "es", 0, TARGET)
    world.call("submit_translation", e, "es", 0, TARGET+" Segunda propuesta.")
    world.call("submit_translation", e, "es", 0, TARGET+" Tercera propuesta.")
    with world.vm.expect_revert("three immutable attempts"):
        world.call("submit_translation", e, "es", 0, TARGET+" Cuarta propuesta.")


def test_parallel_draft_cannot_overwrite_new_parent(world):
    e, _ = world.draft()
    other, _ = world.draft(NEW_SOURCE, NEW_TARGET)
    world.approve(e)
    world.approve(other)
    world.call("publish", e)
    with world.vm.expect_revert("parent_changed"):
        world.call("publish", other)


def test_cancel_preserves_attempts(world):
    e, t = world.draft()
    world.call("cancel_edition", e)
    assert world.c.get_translation(t)["edition"] == e
    with world.vm.expect_revert("draft edition"):
        world.call("review_translation", t)


@pytest.mark.parametrize("decision", ["divergent", "uncertain", "equivalent"])
def test_issue_pending_and_conservative_freeze(world, decision):
    e, _ = world.live()
    issue = world.call("file_issue", e, "es", 0, "The translated temporal condition may change the device instruction.", actor=3)
    assert not world.c.get_live_manifest(1)["available"]
    with world.vm.expect_revert("review pending"):
        world.call("acknowledge", e, world.c.get_edition(e)["manifest"]["fingerprint"], actor=2)
    world.mock(decision)
    world.call("review_issue", issue)
    assert world.c.get_issue(issue)["review"]["decision"] == decision
    assert world.c.get_live_manifest(1)["available"] == (decision == "equivalent")
    if decision != "equivalent":
        assert world.c.get_edition(e)["status"] == "frozen"
        with world.vm.expect_revert("current live"):
            world.call("acknowledge", e, world.c.get_edition(e)["manifest"]["fingerprint"], actor=2)


def test_freeze_is_irreversible_and_successor_recovers(world):
    e, _ = world.live()
    world.call("freeze", e, "Publisher discovered a document synchronization error.")
    assert not world.c.get_live_manifest(1)["available"]
    e2, _ = world.live(NEW_SOURCE, NEW_TARGET)
    world.call("withdraw_handoff", e, actor=2)
    assert world.c.preview_handoff(e)["ready"]
    world.call("retire", e)
    assert world.c.get_live_manifest(1)["edition"] == e2


def test_unsubscribe_cannot_erase_existing_handoff_obligation(world):
    e, _ = world.live()
    world.call("subscribe", 1, "es", False, actor=2)
    world.live(NEW_SOURCE, NEW_TARGET)
    assert not world.c.preview_handoff(e)["ready"]
    with world.vm.expect_revert("snapshotted subscriber"):
        world.call("withdraw_handoff", e, actor=3)
    world.call("withdraw_handoff", e, actor=2)
    world.call("retire", e)


def test_unreviewed_issue_survives_supersession(world):
    e, _ = world.live()
    issue = world.call("file_issue", e, "es", 0, "The translated condition appears narrower than the original.", actor=3)
    world.live(NEW_SOURCE, NEW_TARGET)
    world.call("withdraw_handoff", e, actor=2)
    with world.vm.expect_revert("issue_unreviewed"):
        world.call("retire", e)
    world.mock()
    world.call("review_issue", issue)
    world.call("retire", e)


def test_later_descendant_adoption_completes_old_handoff(world):
    e, _ = world.live()
    world.live(NEW_SOURCE, NEW_TARGET)
    e3, _ = world.live(SOURCE+" Stop if the display fails.", TARGET+" Deténgase si falla la pantalla.")
    world.call("acknowledge", e3, world.c.get_live_manifest(1)["manifest"]["fingerprint"], actor=2)
    world.call("retire", e)
    assert world.c.get_edition(e)["retired_to"] == e3


def test_subscriber_locale_switch_cannot_bypass_handoff(world):
    e, _ = world.live()
    e2, _ = world.live(NEW_SOURCE, NEW_TARGET)
    world.call("subscribe", 1, "en", True, actor=2)
    world.call("acknowledge", e2, world.c.get_live_manifest(1)["manifest"]["fingerprint"], actor=2)
    assert not world.c.preview_handoff(e)["ready"]


@pytest.mark.parametrize("answer", [
    {"decision":"yes"},
    {"decision":"equivalent", "explanation":"Reason", "quotes":{}},
    {"decision":"equivalent", "explanation":"Reason", "quotes":{"source":"fabricated citation", "target":TARGET}},
    {"decision":"uncertain", "explanation":"", "quotes":{}},
    {"decision":"uncertain", "explanation":"Reason", "quotes":{"unknown":"Fabricated text"}}])
def test_malformed_model_never_mutates_review(world, answer):
    e = world.call("stage_edition", 1, "Revision", [SOURCE])
    t = world.call("submit_translation", e, "es", 0, TARGET)
    world.mock(answer=answer)
    with world.vm.expect_revert("LLM_ERROR"):
        world.call("review_translation", t)
    assert world.c.get_translation(t)["review"] is None


def test_validator_independently_rejects_changed_decision_and_fake_citation(world):
    _, t = world.draft()
    leader = world.c.get_translation(t)["review"]
    assert world.validator(leader)
    fake = copy.deepcopy(leader); fake["decision"] = "divergent"
    assert not world.validator(fake)
    fake = copy.deepcopy(leader); fake["quotes"]["target"] = "A fabricated statement"
    assert not world.validator(fake)
    world.mock("divergent")
    assert not world.validator(leader)


@pytest.mark.parametrize("method", ["get_publication","get_edition","get_translation","get_issue"])
def test_unknown_record_rejected(world, method):
    with world.vm.expect_revert("not found"):
        getattr(world.c, method)(999)


def test_multi_locale_multi_segment_all_or_nothing(world):
    world.call("set_editor", 1, "fr", world.actors[3].as_hex, True)
    e = world.call("stage_edition", 1, "Revision", [SOURCE,NEW_SOURCE])
    for locale, actor in [("es",1),("fr",3)]:
        for index, source in enumerate([SOURCE,NEW_SOURCE]):
            target = [TARGET,NEW_TARGET][index] if locale == "es" else "Ne débranchez pas le dispositif tant que le voyant reste allumé."
            t = world.call("submit_translation", e, locale, index, target, actor=actor)
            world.mock(source=source,target=target)
            world.call("review_translation", t)
        v = world.c.preview_publication(e)["vectors"][locale]
        world.call("approve_locale", e, locale, v["fingerprint"], actor=actor)
    world.call("publish", e)
    assert set(world.c.get_live_manifest(1)["manifest"]["locales"]) == {"es","fr"}

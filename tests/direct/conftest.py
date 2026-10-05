import copy
import json
import pytest

SOURCE = "Do not disconnect the device while the indicator remains illuminated."
TARGET = "No desconecte el dispositivo mientras el indicador permanezca iluminado."
NEW_SOURCE = "Disconnect the device only after the indicator has stopped flashing."
NEW_TARGET = "Desconecte el dispositivo solo cuando el indicador haya dejado de parpadear."


class World:
    def __init__(self, vm, deploy, actors):
        self.vm = vm
        vm.sender = actors[0]
        vm.check_pickling = True
        self.c = deploy("contracts/verbasync.py", "VerbaSync controlled local desk")
        from genlayer import Address
        self.actors = [a if isinstance(a, Address) else Address(bytes(a)) for a in actors]
        self.call("create_publication", "Device operating instructions", "en")
        self.call("set_editor", 1, "es", self.actors[1].as_hex, True)
        self.call("subscribe", 1, "es", True, actor=2)

    def call(self, method, *args, actor=0):
        self.vm.sender = self.actors[actor]
        self.vm.value = 0
        return getattr(self.c, method)(*args)

    def mock(self, decision="equivalent", source=SOURCE, target=TARGET, answer=None):
        self.vm.clear_mocks()
        payload = answer if answer is not None else {"decision": decision,
            "explanation": "Both segments preserve the same condition and prohibition.",
            "quotes": {} if decision == "uncertain" else {"source": source, "target": target}}
        self.vm.mock_llm("VerbaSync semantic alignment", json.dumps(payload))

    def draft(self, source=SOURCE, target=TARGET):
        e = self.call("stage_edition", 1, "Revision", [source])
        t = self.call("submit_translation", e, "es", 0, target, actor=1)
        self.mock(source=source, target=target)
        self.call("review_translation", t)
        return e, t

    def approve(self, edition):
        vector = self.c.preview_publication(edition)["vectors"]["es"]
        self.call("approve_locale", edition, "es", vector["fingerprint"], actor=1)

    def live(self, source=SOURCE, target=TARGET):
        e, t = self.draft(source, target)
        self.approve(e)
        self.call("publish", e)
        return e, t

    def validator(self, leader):
        from genlayer import gl
        self.vm._in_nondet = True
        try:
            return self.vm._captured_validators[-1][2](gl.vm.Return(copy.deepcopy(leader)))
        finally:
            self.vm._in_nondet = False


@pytest.fixture
def world(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, direct_charlie):
    return World(direct_vm, direct_deploy, [direct_owner, direct_alice, direct_bob, direct_charlie])

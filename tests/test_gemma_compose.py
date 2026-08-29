import asyncio, json
import viral.gemma_compose as gc


def test_compose_gemma_coerces_fingers_from_labels(monkeypatch):
    async def fake_chat(*a, **k):
        return json.dumps({"title": "t", "bpm": 90, "beats_per_cycle": 8, "kit": "chenda",
                           "notes": [{"beat": 0, "finger": 4, "label": "thom"}, {"beat": 1, "finger": 0, "label": "ki"},
                                     {"beat": 2, "finger": 9, "label": "ta"}, {"beat": 3, "label": "mi"}], "phrases": [[0, 8]]})
    monkeypatch.setattr(gc, "_chat", fake_chat)
    sc = asyncio.run(gc.compose_gemma(None, "u", "m", "brief", "chenda", "chempada 8", 1, 90))
    assert [n.finger for n in sc.notes] == [0, 3, 2, 4] and sc.title == "t"


def test_compose_gemma_rejects_too_short(monkeypatch):
    async def fake_chat(*a, **k): return json.dumps({"notes": [{"beat": 0, "finger": 0}]})
    monkeypatch.setattr(gc, "_chat", fake_chat)
    try:
        asyncio.run(gc.compose_gemma(None, "u", "m", "b", "chenda", "x", 1, 90)); assert False
    except ValueError:
        pass

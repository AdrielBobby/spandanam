"""Hub-level integration tests for the async wiring the pure-function unit tests
can't reach: chant()/run_in_executor (vaaythari karaoke), poll_imu -> round_strokes
-> practice_end.summary.motion (motion coach), and the ladder auto-advance/retry
restart (kaalam ladder). Drives Hub directly with asyncio.run() rather than through
a WebSocket: create_app() doesn't expose its Hub instance, and this repo has no WS
test harness anywhere else either.

hub.broadcast is monkeypatched to record messages instead of touching real
WebSocket clients -- gives these tests the same ground truth a real dashboard
would see (e.g. the scaled score/bpm in practice_start) with no network/ASGI layer.
A fast bpm (1200) keeps every round's real lead-in/count-in under a few hundred ms.

Each test runs its whole body -- including closing hub.http at the end -- inside a
single asyncio.run() call. httpx.AsyncClient.aclose() must run on the same event
loop it made requests on; closing it from a separately-run teardown coroutine (a
fresh asyncio.run() call, i.e. a different loop) raises "Event loop is closed".
"""
from __future__ import annotations

import asyncio
import time

import pytest

from viral import speech
from viral.bridge import phrase_to_score
from viral.config import Config
from viral.events import Strike
from viral.imu import Stroke
from viral.score import Note, Score
from viral.server import Hub


class _FakeSampler:
    """Stands in for sound.Sampler, which opens a real PortAudio stream even in --dry
    mode (dry only covers Glove/MPU6050Reader). These tests exercise ladder/karaoke/
    motion wiring, not audio playback -- and constructing several real Samplers back
    to back in one process (one per Hub()) reliably crashed the interpreter with a
    native access violation, since nothing in this codebase ever closes the stream."""
    def __init__(self, kit: str, assets=None) -> None:
        self.kit = kit
        self.mixer = None

    def set_kit(self, kit: str, assets=None) -> None:
        self.kit = kit

    def play(self, finger: int, velocity: float = 1.0) -> None:
        pass

    def stop(self) -> None:
        pass


@pytest.fixture
def hub(monkeypatch):
    monkeypatch.setattr("viral.server.Sampler", _FakeSampler)
    h = Hub(Config(dry=True))
    h.broadcast_log: list[dict] = []

    async def recording_broadcast(msg: dict) -> None:
        h.broadcast_log.append(msg)   # no real WS clients are connected in these tests

    h.broadcast = recording_broadcast
    return h


def _run(hub: Hub, body) -> None:
    """Run body(hub) to completion, then close hub.http on that same loop."""
    async def wrapped():
        try:
            await body(hub)
        finally:
            await hub.http.aclose()
    asyncio.run(wrapped())


async def _wait_idle(hub: Hub, timeout_s: float = 5.0) -> None:
    elapsed = 0.0
    while hub.mode != "idle" and elapsed < timeout_s:
        await asyncio.sleep(0.02)
        elapsed += 0.02
    assert hub.mode == "idle", "round never completed"


async def _wait_for_broadcast(hub: Hub, msg_type: str, timeout_s: float = 5.0) -> dict:
    elapsed = 0.0
    while elapsed < timeout_s:
        for m in hub.broadcast_log:
            if m["type"] == msg_type:
                return m
        await asyncio.sleep(0.02)
        elapsed += 0.02
    raise AssertionError(f"never saw a {msg_type!r} broadcast; got {[m['type'] for m in hub.broadcast_log]}")


async def _strike_every_note_perfectly(hub: Hub) -> None:
    """Read the just-broadcast practice_start's (already tempo-scaled) score and
    fire an on-time, correct-finger strike for each note -- guarantees a pass."""
    start_msg = await _wait_for_broadcast(hub, "practice_start")
    sc = start_msg["score"]
    beat_s = 60.0 / sc["bpm"]
    for n in sc["notes"]:
        target = hub.play.start_s + n["beat"] * beat_s
        await asyncio.sleep(max(0.0, target - time.monotonic()))
        await hub.on_strike(Strike(n["finger"], time.monotonic(), 1.0, "key"))


# --- karaoke wiring ----------------------------------------------------------------------

def test_chant_fires_with_correct_syllables_and_bpm(hub, monkeypatch):
    calls = []
    monkeypatch.setattr(speech, "chant", lambda syllables, bpm: calls.append((syllables, bpm)))

    async def body(hub):
        hub.score = phrase_to_score(["dhim", "tha", "ka"], 1200.0, cycles=1)
        await hub.start_practice(None, 1.0)
        await asyncio.sleep(0.2)
        assert calls == [(("dhim", "tha", "ka"), 1200.0)]

    _run(hub, body)


def test_chant_does_not_fire_for_unlabeled_score(hub, monkeypatch):
    calls = []
    monkeypatch.setattr(speech, "chant", lambda syllables, bpm: calls.append((syllables, bpm)))

    async def body(hub):
        hub.score = Score("t", 1200.0, 2, (Note(0, 0), Note(1, 1)))   # label defaults to ""
        await hub.start_practice(None, 1.0)
        await asyncio.sleep(0.2)
        assert calls == []

    _run(hub, body)


# --- motion coach wiring -------------------------------------------------------------------

def test_injected_strokes_flow_into_practice_end_motion_summary(hub):
    async def body(hub):
        hub.score = phrase_to_score(["dhim", "tha"], 1200.0, cycles=1)
        await hub.start_practice(None, 1.0)
        assert hub.round_strokes == []
        hub.round_strokes.append(Stroke(t_s=0.0, peak_g=3.0, tilt_deg=10.0))   # flat
        hub.round_strokes.append(Stroke(t_s=0.1, peak_g=3.2, tilt_deg=12.0))
        await _wait_idle(hub)
        assert hub.last_summary.get("motion", {}).get("verdict") == "flat"

    _run(hub, body)


def test_no_strokes_means_no_motion_key_in_summary(hub):
    async def body(hub):
        hub.score = phrase_to_score(["dhim", "tha"], 1200.0, cycles=1)
        await hub.start_practice(None, 1.0)
        await _wait_idle(hub)
        assert "motion" not in hub.last_summary

    _run(hub, body)


# --- kaalam ladder wiring ------------------------------------------------------------------

def test_ladder_advances_to_next_step_on_a_passing_round(hub):
    async def body(hub):
        hub.score = phrase_to_score(["dhim", "tha"], 1200.0, cycles=1)
        await hub.start_ladder(None, (0.6, 1.0))
        assert hub.ladder is not None and hub.ladder.step == 0
        await _strike_every_note_perfectly(hub)
        step_up = await _wait_for_broadcast(hub, "ladder_step_up")
        assert step_up["step"] == 1 and step_up["bpm_scale"] == 1.0
        hub.ladder = None; await hub.stop_all(); await asyncio.sleep(0.05)   # let round 2 wind down

    _run(hub, body)


def test_ladder_retries_same_step_on_a_missed_round(hub):
    async def body(hub):
        hub.score = phrase_to_score(["dhim", "tha"], 1200.0, cycles=1)
        await hub.start_ladder(None, (0.6, 1.0))
        # deliberately strike nothing -- every note misses -> stars == 0
        retry = await _wait_for_broadcast(hub, "ladder_retry")
        assert retry["step"] == 0 and retry["bpm_scale"] == 0.6
        hub.ladder = None; await hub.stop_all(); await asyncio.sleep(0.05)

    _run(hub, body)


def test_manual_stop_clears_ladder_state(hub):
    async def body(hub):
        hub.score = phrase_to_score(["dhim", "tha"], 1200.0, cycles=1)
        await hub.start_ladder(None, (0.6, 1.0))
        assert hub.ladder is not None
        hub.ladder = None                        # mirrors the WS "stop" handler's own clearing
        await hub.stop_all()
        assert hub.ladder is None
        await asyncio.sleep(0.05)

    _run(hub, body)

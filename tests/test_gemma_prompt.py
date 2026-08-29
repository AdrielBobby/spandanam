import json

from melam.fatigue import FatigueFeatures
from melam.gemma_coach import CoachDecision, build_prompt
from melam.sync import NodeTempo


def test_prompt_is_json_with_fused_rows():
    p = build_prompt([NodeTempo("d1", 80, 5, 40)], {"d1": 12.0},
                     [FatigueFeatures("d1", 130, 3.0, 10.0, 5.0, 80)], 3)
    d = json.loads(p)
    assert d["current_kaalam"] == 3
    assert d["drummers"]["d1"]["hr"] == 130 and d["drummers"]["d1"]["offset_ms"] == 12.0


def test_rest_commands_only_for_risk():
    d = CoachDecision(2, .9, False, {"d1": {"fatigue": "risk"}, "d2": {"fatigue": "fresh"}}, "", "{}")
    assert d.rest_commands() == {"d1": "R"}

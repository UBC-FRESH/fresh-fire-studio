from __future__ import annotations

import pytest

from suppression.evidence import (
    MC_FAYDEN_HOLD_MINUTES,
    WHEATLEY_HIGH_WATER_HOLD_SECONDS,
    WHEATLEY_HOLD_SECONDS,
    WHEATLEY_INDIRECT_HIGH_WATER_HOLD_SECONDS,
    hold_time,
    suppressed_ros_m_min,
)


def test_wheatley_hold_values() -> None:
    assert hold_time(tactic="direct", water="low").seconds == WHEATLEY_HOLD_SECONDS
    assert hold_time(tactic="direct", water="high").seconds == WHEATLEY_HIGH_WATER_HOLD_SECONDS
    assert (
        hold_time(tactic="indirect", water="high").seconds
        == WHEATLEY_INDIRECT_HIGH_WATER_HOLD_SECONDS
    )
    assert hold_time(tactic="direct", water="low").minutes == pytest.approx(2.05)


def test_mcfayden_hold() -> None:
    evidence = hold_time(tactic="direct", water="low", source="mcfayden")
    assert evidence.minutes == MC_FAYDEN_HOLD_MINUTES


def test_absolute_ros_reduction() -> None:
    assert suppressed_ros_m_min(2.0) == 1.5
    assert suppressed_ros_m_min(0.5) == 0.0
    assert suppressed_ros_m_min(0.5, reduction_m_min=0.0) == 0.5


def test_evidence_artifacts_exist_and_use_absolute_reduction() -> None:
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for name in ("2003-526-native-wheatley-evidence", "2003-526-native-mcfayden-evidence"):
        payload = json.loads((root / "suppression" / "proofs" / f"{name}.json").read_text())
        assert "absolute ROS reduction" in payload["method"]["drops"]
        assert payload["native"]["area_sim_ha"] == payload["free_burn"]["area_sim_ha"]


def test_invalid_ros_values() -> None:
    with pytest.raises(ValueError):
        suppressed_ros_m_min(-1.0)
    with pytest.raises(ValueError):
        suppressed_ros_m_min(1.0, reduction_m_min=-0.1)

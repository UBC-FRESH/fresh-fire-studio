from __future__ import annotations

from portal.assistant import _portal_context


def test_assistant_context_includes_persistence_envelope() -> None:
    text = _portal_context([])
    assert "17-18 minutes" in text
    assert "54-aircraft lower bound" in text
    assert "65 aircraft" in text
    assert "not an operational plan" in text

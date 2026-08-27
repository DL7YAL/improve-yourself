import json
import sys
from pathlib import Path

import pytest

from improve_yourself.optimizer_evidence_review import (
    build_evidence_review,
    main,
    render_evidence_review,
)


def _check(**overrides: object) -> dict[str, object]:
    value = {
        "id": "cpu",
        "label": "CPU",
        "summary": "Known",
        "status": "OK",
        "classification": "reliably_automatically_checked",
        "user_view": {"status": "OK"},
        "evidence": {"source": "CIM"},
    }
    value.update(overrides)
    return value


def system_check() -> dict[str, object]:
    return {
        "schema": "iy.system_check/v1",
        "policy": {"read_only": True, "changes_applied": False},
        "checks": [
            _check(),
            _check(
                id="bios",
                label="BIOS",
                summary="Unknown",
                status="REVIEW",
                classification="not_implemented",
                user_view={"status": "Nicht prüfbar / unbekannt"},
                evidence={},
            ),
        ],
        "user_summary": {},
    }


def test_review_preserves_unknown_and_read_only_policy(tmp_path: Path) -> None:
    review = build_evidence_review(system_check())
    assert [item["availability"] for item in review["items"]] == ["KNOWN", "NOT AVAILABLE"]
    assert review["policy"] == {
        "local_only": True,
        "read_only": True,
        "changes_applied": False,
        "apply_available": False,
        "restore_available": False,
        "demo_or_replay_data_included": False,
    }
    page = render_evidence_review(review, tmp_path / "review.html").read_text(encoding="utf-8")
    assert "LOCAL REPORT / READ-ONLY" in page
    assert "Evidence details:" in page and "Evidence source:" in page
    assert "Provenance:" not in page
    assert "fixed official vendor sources" in page
    assert "<button" not in page and "<form" not in page
    assert "Apply" not in page and "Restore" not in page
    assert "Legend:" in page and "Summary:" in page


def test_offline_network_mode_is_rendered_without_vendor_claim() -> None:
    value = system_check(); value["policy"]["official_vendor_comparisons"] = False
    review = build_evidence_review(value)
    assert review["network_mode"] == "OFFLINE"


@pytest.mark.parametrize("policy", [
    {"read_only": False, "changes_applied": False},
    {"read_only": True, "changes_applied": True},
    None,
    "not a policy",
])
def test_review_rejects_unsafe_or_malformed_system_check_policy(policy: object) -> None:
    value = system_check()
    value["policy"] = policy
    with pytest.raises(ValueError, match="read-only"):
        build_evidence_review(value)


@pytest.mark.parametrize("mutate", [
    lambda value: value.pop("policy"),
    lambda value: value.__setitem__("policy", "unsafe"),
    lambda value: value.__setitem__("policy", {"local_only": True}),
    lambda value: value["policy"].__setitem__("read_only", False),
    lambda value: value["policy"].__setitem__("changes_applied", True),
    lambda value: value["policy"].__setitem__("apply_available", True),
    lambda value: value["policy"].__setitem__("restore_available", True),
    lambda value: value["policy"].__setitem__("demo_or_replay_data_included", True),
])
def test_renderer_rejects_missing_malformed_or_contradictory_policy(tmp_path: Path, mutate) -> None:
    review = build_evidence_review(system_check())
    mutate(review)
    with pytest.raises(ValueError, match="local read-only boundary"):
        render_evidence_review(review, tmp_path / "unsafe.html")


def test_renderer_rejects_fabricated_item_despite_safe_policy(tmp_path: Path) -> None:
    review = build_evidence_review(system_check())
    review["items"] = [{"availability": "KNOWN", "assessment_status": "OK", "evidence": "not evidence"}]
    with pytest.raises(ValueError, match="evidence details"):
        render_evidence_review(review, tmp_path / "unsafe.html")


@pytest.mark.parametrize("payload", [None, [], {"schema": "iy.system_check/v1", "policy": {"read_only": True, "changes_applied": False}, "checks": "bad"}])
def test_review_rejects_malformed_system_check_input(payload: object) -> None:
    with pytest.raises(ValueError):
        build_evidence_review(payload)  # type: ignore[arg-type]


@pytest.mark.parametrize("check", [
    _check(classification=None),
    _check(classification="invented"),
    _check(user_view={}),
    _check(user_view=None),
    _check(evidence="not an object"),
])
def test_review_rejects_missing_or_invalid_evidence_classification_and_assessment(check: dict[str, object]) -> None:
    value = system_check()
    value["checks"] = [check]
    with pytest.raises(ValueError):
        build_evidence_review(value)


def test_demo_and_replay_fields_are_not_propagated_to_review_output() -> None:
    value = system_check()
    value["demo"] = {"source": "must-not-flow"}
    value["replay"] = {"schema": "iy.replay/v2"}
    review = build_evidence_review(value)
    serialized = json.dumps(review)
    assert "demo" not in review and "replay" not in review
    assert "must-not-flow" not in serialized and "iy.replay/v2" not in serialized


def test_html_escapes_script_attribute_payloads_and_unicode(tmp_path: Path) -> None:
    value = system_check()
    value["checks"] = [_check(
        label='<script>alert("x")</script>',
        summary='" onmouseover="alert(1)',
        evidence={"source": "Δriver <b>vendor</b>", "note": "Grüße 🛡️"},
    )]
    page = render_evidence_review(build_evidence_review(value), tmp_path / "review.html").read_text(encoding="utf-8")
    assert "<script>" not in page and "&lt;script&gt;" in page
    assert '" onmouseover="alert(1)' not in page and "&quot; onmouseover=&quot;alert(1)" in page
    assert "Δriver" in page and "Grüße 🛡️" in page and "&lt;b&gt;vendor&lt;/b&gt;" in page


@pytest.mark.parametrize("raw", ["{", "[]"])
def test_cli_rejects_invalid_or_non_object_json(tmp_path: Path, monkeypatch, raw: str) -> None:
    source = tmp_path / "invalid.json"
    source.write_text(raw, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["iy-optimizer-evidence-review", str(source)])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2

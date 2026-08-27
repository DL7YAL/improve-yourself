import pytest
from improve_yourself.optimizer_evidence_review import build_evidence_review, render_evidence_review

def system_check():
    return {"schema":"iy.system_check/v1","policy":{"read_only":True,"changes_applied":False},"checks":[
        {"id":"cpu","label":"CPU","summary":"Known","status":"OK","classification":"implemented","user_view":{"status":"OK"},"evidence":{"source":"CIM"}},
        {"id":"bios","label":"BIOS","summary":"Unknown","status":"REVIEW","classification":"not_implemented","user_view":{"status":"Nicht prüfbar / unbekannt"},"evidence":{}},
    ],"user_summary":{}}

def test_review_preserves_unknown_and_read_only_policy(tmp_path):
    review=build_evidence_review(system_check())
    assert [item["availability"] for item in review["items"]]==["KNOWN","NOT AVAILABLE"]
    assert review["policy"] == {"local_only":True,"read_only":True,"changes_applied":False,"apply_available":False,"restore_available":False,"demo_or_replay_data_included":False}
    page=render_evidence_review(review,tmp_path/'review.html').read_text(encoding='utf-8')
    assert '<button' not in page and 'Restore' not in page and 'NOT AVAILABLE' in page

def test_review_rejects_non_read_only_system_check():
    value=system_check(); value['policy']['changes_applied']=True
    with pytest.raises(ValueError, match='read-only'):
        build_evidence_review(value)

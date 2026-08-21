import json
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from improve_yourself.review_server import ReviewServer
from improve_yourself.review_state import (
    initial_review_state,
    load_or_create_review_state,
    scene_id,
    validate_review_state,
    write_review_state,
)


def scenes() -> list[dict]:
    return [{"round_number": 2, "start_tick": 10, "end_tick": 20, "marker_player": "Player"}]


def test_initial_state_is_source_and_scene_bound(tmp_path: Path) -> None:
    payload = load_or_create_review_state(tmp_path / "state.json", "a" * 64, scenes())
    assert payload["schema"] == "iy.review_state/v1"
    assert payload["source_sha256"] == "a" * 64
    assert payload["scenes"] == [{"scene_id": "r2-t10-20-Player", "state": "unreviewed", "note": ""}]


def test_rejects_unknown_scene_state_and_long_note() -> None:
    expected = {scene_id(scenes()[0])}
    base = initial_review_state("a" * 64, scenes())
    base["scenes"][0]["state"] = "guilty"
    with pytest.raises(ValueError, match="invalid state"):
        validate_review_state(base, "a" * 64, expected)
    base["scenes"][0]["state"] = "reviewed"
    base["scenes"][0]["note"] = "x" * 2001
    with pytest.raises(ValueError, match="at most 2000"):
        validate_review_state(base, "a" * 64, expected)


def test_neutral_follow_up_state_is_supported() -> None:
    expected = {scene_id(scenes()[0])}
    payload = initial_review_state("a" * 64, scenes())
    payload["scenes"][0]["state"] = "follow-up"
    assert validate_review_state(payload, "a" * 64, expected)["scenes"][0]["state"] == "follow-up"


def test_loopback_server_round_trip_and_origin_guard(tmp_path: Path) -> None:
    server = ReviewServer(("127.0.0.1", 0), tmp_path, "a" * 64, scenes())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/api/review-state"
        current = json.loads(urlopen(url, timeout=2).read())
        current["scenes"][0].update({"state": "reviewed", "note": "checked"})
        request = Request(url, data=json.dumps(current).encode(), method="POST", headers={
            "Content-Type": "application/json", "Origin": f"http://127.0.0.1:{server.server_port}"
        })
        saved = json.loads(urlopen(request, timeout=2).read())
        assert saved["scenes"][0]["state"] == "reviewed"
        assert json.loads((tmp_path / "review-state.json").read_text(encoding="utf-8"))["scenes"][0]["note"] == "checked"

        forbidden = Request(url, data=json.dumps(current).encode(), method="POST", headers={
            "Content-Type": "application/json", "Origin": "https://example.com"
        })
        with pytest.raises(HTTPError) as error:
            urlopen(forbidden, timeout=2)
        assert error.value.code == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

import json

import pytest
from pathlib import Path

from improve_yourself.asset_rights import AssetRightsError, assess_asset_rights, load_asset_rights


ROOT = Path(__file__).parents[1]


def _manifest(tmp_path, statuses):
    path = tmp_path / "asset-rights.json"
    path.write_text(json.dumps({
        "schema": "iy.asset_rights/v1",
        "assets": [
            {"asset_id": f"asset-{index}", "status": status, "evidence": "reviewed provenance record"}
            for index, status in enumerate(statuses)
        ],
    }), encoding="utf-8")
    return path


def test_owned_assets_pass_internal_and_public_gates(tmp_path):
    document = load_asset_rights(_manifest(tmp_path, ["OWNED", "LICENSED_FOR_DISTRIBUTION"]))
    assert assess_asset_rights(document, "internal").allowed is True
    assert assess_asset_rights(document, "public").allowed is True


def test_local_and_reference_assets_are_internal_only(tmp_path):
    document = load_asset_rights(_manifest(tmp_path, ["LICENSED_INTERNAL_ONLY", "THIRD_PARTY_REFERENCE_ONLY"]))
    assert assess_asset_rights(document, "internal").allowed is True
    public = assess_asset_rights(document, "public")
    assert public.allowed is False
    assert public.blocked_asset_ids == ("asset-0", "asset-1")


@pytest.mark.parametrize("status", ["UNKNOWN", "PUBLICATION_BLOCKED"])
def test_unknown_or_blocked_assets_fail_every_distribution_gate(tmp_path, status):
    document = load_asset_rights(_manifest(tmp_path, [status]))
    assert assess_asset_rights(document, "internal").allowed is False
    assert assess_asset_rights(document, "public").allowed is False


def test_missing_evidence_and_duplicate_ids_fail_closed(tmp_path):
    path = _manifest(tmp_path, ["OWNED"])
    document = json.loads(path.read_text(encoding="utf-8"))
    document["assets"][0]["evidence"] = ""
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(AssetRightsError, match="evidence"):
        load_asset_rights(path)
    duplicate = _manifest(tmp_path, ["OWNED", "OWNED"])
    document = json.loads(duplicate.read_text(encoding="utf-8"))
    document["assets"][1]["asset_id"] = document["assets"][0]["asset_id"]
    duplicate.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(AssetRightsError, match="unique"):
        load_asset_rights(duplicate)


def test_complete_visual_reference_is_not_publication_ready():
    document = load_asset_rights(ROOT / "resources" / "asset_rights" / "complete_visual_reference.json")
    assert assess_asset_rights(document, "public").allowed is False
    internal = assess_asset_rights(document, "internal")
    assert internal.allowed is False
    assert internal.blocked_asset_ids == ("map-surface-de-overpass", "map-surface-de-train")

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from tools.pov_prep_data.validate import PovPrepValidationError, load_and_validate, validate_document

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "resources" / "3d_pov" / "de_mirage" / "prep.json"


def package() -> dict:
    return deepcopy(load_and_validate(PACKAGE))


def test_mirage_static_prep_is_ready_but_not_locally_verified() -> None:
    document = package()
    assert document["map_id"] == "de_mirage"
    assert document["geometry_inventory"]["bundled_files"] == []
    assert document["coordinate_contract"]["transform_to_replay"]["status"] == "EXPECTED_IDENTITY_PENDING_LOCAL_VALIDATION"
    assert document["reference_anchors"] == []
    assert document["verification"]["status"] == "PREP_READY_PENDING_LOCAL_VERIFICATION"


def test_mirage_requires_expected_identity_without_fabricated_anchors() -> None:
    document = package(); document["coordinate_contract"]["transform_to_replay"]["status"] = "VERIFIED_LOCAL_REFERENCE"
    with pytest.raises(PovPrepValidationError, match="transform status"): validate_document(document)
    document = package(); document["reference_anchors"].append({})
    with pytest.raises(PovPrepValidationError, match="anchors must remain absent"): validate_document(document)


def test_mirage_never_bundles_source_or_derivative_geometry() -> None:
    document = package(); candidate = document["geometry_inventory"]["candidates"][0]
    assert candidate["source_vpk"]["repository_path"] is None
    assert candidate["render_mesh"]["repository_path"] is None
    assert candidate["visibility_mesh"]["repository_path"] is None

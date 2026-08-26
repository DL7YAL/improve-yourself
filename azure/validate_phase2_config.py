#!/usr/bin/env python3
"""Validate Phase 2 Azure IaC parameters and critical Bicep contracts.

This is intentionally a local/CI-only validator. It does not authenticate to Azure,
call Azure APIs, create resources, or accept secret values.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SUBNET_ID_PATTERN = re.compile(
    r"^/subscriptions/[^/]+/resourceGroups/[^/]+/providers/"
    r"Microsoft\.Network/virtualNetworks/[^/]+/subnets/[^/]+$",
    re.IGNORECASE,
)
DNS_ZONE_ID_PATTERN = re.compile(
    r"^/subscriptions/[^/]+/resourceGroups/[^/]+/providers/"
    r"Microsoft\.Network/privateDnsZones/[^/]+$",
    re.IGNORECASE,
)

PUBLIC_NETWORK_TO_DNS_PARAMETER = {
    "enablePublicNetworkStorage": "privateDnsZoneIds_storage",
    "enablePublicNetworkKeyVault": "privateDnsZoneIds_keyvault",
    "enablePublicNetworkCosmos": "privateDnsZoneIds_cosmos",
    "enablePublicNetworkSql": "privateDnsZoneIds_sql",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def get_value(parameters: dict[str, Any], name: str) -> Any:
    entry = parameters.get(name)
    if not isinstance(entry, dict) or "value" not in entry:
        raise KeyError(name)
    return entry["value"]


def validate_parameters(parameters: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for name in (
        "enableDiagnostics",
        "enablePrivateEndpoints",
        "enablePublicNetworkStorage",
        "enablePublicNetworkKeyVault",
        "enablePublicNetworkCosmos",
        "enablePublicNetworkSql",
        "enableSqlSecurityDiagnostics",
    ):
        try:
            value = get_value(parameters, name)
        except KeyError:
            fail(errors, f"Missing required boolean parameter: {name}")
            continue
        if not isinstance(value, bool):
            fail(errors, f"Parameter {name} must be a JSON boolean.")

    for name in ("environment", "appName", "sqlAdminUser", "privateEndpointSubnetId"):
        try:
            value = get_value(parameters, name)
        except KeyError:
            fail(errors, f"Missing required string parameter: {name}")
            continue
        if not isinstance(value, str):
            fail(errors, f"Parameter {name} must be a string.")

    for name in PUBLIC_NETWORK_TO_DNS_PARAMETER.values():
        try:
            value = get_value(parameters, name)
        except KeyError:
            fail(errors, f"Missing required Private DNS zone ID array: {name}")
            continue
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            fail(errors, f"Parameter {name} must be an array of strings.")
            continue
        for zone_id in value:
            if not DNS_ZONE_ID_PATTERN.fullmatch(zone_id):
                fail(
                    errors,
                    f"{name} contains an invalid Private DNS zone resource ID: {zone_id!r}",
                )

    # The password is deliberately absent from checked-in parameter files and supplied
    # only as a secret pipeline override at what-if/apply time.
    if "sqlAdminPassword" in parameters:
        fail(errors, "sqlAdminPassword must not be stored in a checked-in parameter file.")

    try:
        private_endpoints_enabled = get_value(parameters, "enablePrivateEndpoints")
        subnet_id = get_value(parameters, "privateEndpointSubnetId")
    except KeyError:
        private_endpoints_enabled = False
        subnet_id = ""

    if private_endpoints_enabled:
        if not subnet_id:
            fail(
                errors,
                "enablePrivateEndpoints=true requires a non-empty privateEndpointSubnetId.",
            )
        elif not SUBNET_ID_PATTERN.fullmatch(subnet_id):
            fail(
                errors,
                "privateEndpointSubnetId must be a subnet resource ID ending in "
                "/Microsoft.Network/virtualNetworks/<vnet>/subnets/<subnet>.",
            )
    else:
        if subnet_id:
            fail(
                errors,
                "privateEndpointSubnetId is set while enablePrivateEndpoints=false.",
            )
        for dns_parameter in PUBLIC_NETWORK_TO_DNS_PARAMETER.values():
            try:
                zone_ids = get_value(parameters, dns_parameter)
            except KeyError:
                continue
            if zone_ids:
                fail(
                    errors,
                    f"{dns_parameter} is set while enablePrivateEndpoints=false.",
                )

    for public_network_parameter, dns_parameter in PUBLIC_NETWORK_TO_DNS_PARAMETER.items():
        try:
            public_network_enabled = get_value(parameters, public_network_parameter)
            zone_ids = get_value(parameters, dns_parameter)
        except KeyError:
            continue
        if public_network_enabled is False:
            if not private_endpoints_enabled:
                fail(
                    errors,
                    f"{public_network_parameter}=false requires enablePrivateEndpoints=true.",
                )
            if not zone_ids:
                fail(
                    errors,
                    f"{public_network_parameter}=false requires at least one ID in {dns_parameter} "
                    "for name resolution.",
                )

    try:
        if get_value(parameters, "enableSqlSecurityDiagnostics") and not get_value(
            parameters, "enableDiagnostics"
        ):
            fail(
                errors,
                "enableSqlSecurityDiagnostics=true requires enableDiagnostics=true.",
            )
    except KeyError:
        pass

    return errors


def validate_bicep_contract(bicep_path: Path) -> list[str]:
    """Check the Phase 2 contracts that JSON parameter typing cannot express."""
    errors: list[str] = []
    source = bicep_path.read_text(encoding="utf-8")

    required_fragments = {
        "native Storage publicNetworkAccess toggle": (
            "publicNetworkAccess: enablePublicNetworkStorage ? 'Enabled' : 'Disabled'"
        ),
        "Blob service child resource": (
            "resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01'"
        ),
        "Blob diagnostic scope": "scope: blobService",
        "Blob StorageRead diagnostic category": "{ category: 'StorageRead', enabled: true }",
        "Blob StorageWrite diagnostic category": "{ category: 'StorageWrite', enabled: true }",
        "Blob StorageDelete diagnostic category": "{ category: 'StorageDelete', enabled: true }",
        "Key Vault publicNetworkAccess toggle": (
            "publicNetworkAccess: enablePublicNetworkKeyVault ? 'Enabled' : 'Disabled'"
        ),
        "Cosmos publicNetworkAccess toggle": (
            "publicNetworkAccess: enablePublicNetworkCosmos ? 'Enabled' : 'Disabled'"
        ),
        "SQL publicNetworkAccess toggle": (
            "publicNetworkAccess: enablePublicNetworkSql ? 'Enabled' : 'Disabled'"
        ),
    }

    for description, fragment in required_fragments.items():
        if fragment not in source:
            fail(errors, f"Bicep contract missing: {description}.")

    if "resource diag_storage 'Microsoft.Insights/diagnosticSettings" in source:
        fail(
            errors,
            "StorageRead/StorageWrite/StorageDelete must not be attached through the "
            "legacy storage-account diagnostic-settings resource.",
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parameters", type=Path, required=True)
    parser.add_argument("--bicep", type=Path, required=True)
    args = parser.parse_args()

    try:
        document = json.loads(args.parameters.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read parameter file: {exc}", file=sys.stderr)
        return 2

    parameters = document.get("parameters")
    if not isinstance(parameters, dict):
        print("ERROR: parameter file must contain a top-level object named 'parameters'.", file=sys.stderr)
        return 2

    errors = validate_parameters(parameters)
    try:
        errors.extend(validate_bicep_contract(args.bicep))
    except OSError as exc:
        print(f"ERROR: cannot read Bicep file: {exc}", file=sys.stderr)
        return 2

    if errors:
        print("Phase 2 IaC validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Phase 2 IaC parameter and Bicep contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

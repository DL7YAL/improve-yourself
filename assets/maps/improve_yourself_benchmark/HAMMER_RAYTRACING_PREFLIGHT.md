# Hammer ray-tracing preflight boundary

Status: **LOCAL HAMMER RUNTIME ONLY**

## Decision

`check_raytracing_support.vrad3` is expected to be created or made available by
the installed CS2 Workshop Tools when Hammer starts. It is an installed
Valve/Workshop Tools runtime artifact, not a project-authored benchmark source.

Consequently:

- do not copy, commit, hash-lock, or package the file in this repository;
- record the expected behavior here so it survives local reinstallation and is
  visible through GitHub;
- treat a missing file before Hammer starts as non-evidence of missing GPU
  ray-tracing support;
- keep Azure, Foundry, cloud CI, and remote MCP work out of this local Hammer
  preflight. They must neither read the file nor block their own work on it.

## Local verification on the fixed benchmark machine

When benchmark work is explicitly resumed, use this bounded sequence:

1. Start the installed CS2 Workshop Tools and Hammer.
2. Confirm that Hammer has initialized its local VRAD/script context.
3. Run the existing VRAD preflight only after that initialization.
4. Record the Workshop Tools build, Hammer start confirmation, command result,
   and any relevant non-secret error text in the active handoff.

The result remains local runtime evidence. It does not authorize asset copying,
Azure deployment, driver/registry changes, or benchmark-runtime changes.

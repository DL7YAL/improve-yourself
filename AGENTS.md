# DL7YAL Codex Project Instructions

## Purpose
This repository is the shared source of truth for Codex work on Improve Yourself and the current Improve Optimizer foundation. Do not rely on one user's chat history or local session memory for project-critical decisions. Persist durable decisions in the repository.

## Operating model
- Treat the repository, its documentation, tests, configuration, and Git history as authoritative shared project context.
- A fresh Codex session or another authorized DL7YAL workspace user must be able to continue work from the repository without needing private prior-chat context.
- Before changing architecture or behavior, inspect the relevant README/specification/evidence documents and existing tests.
- Do not silently replace established decisions with assumptions from a new session.
- When a durable architectural/product decision changes, update the relevant repository documentation in the same change where practical.

## Engineering principles
- Reliability before feature count.
- Clear recommendations instead of data overload.
- Few deliberate user choices.
- Evidence before optimization claims.
- Unknown or insufficient evidence must remain explicit; do not manufacture certainty.
- Safety and reversibility are product requirements, not premium features.
- For future system-changing operations follow: READ -> SNAPSHOT -> APPLY -> VERIFY -> RESTORE.
- BIOS/UEFI and other manual-critical operations must not be automated unless the repository explicitly establishes a safe supported path.
- Preserve tests and validation contracts; add or update tests when behavior changes.

## Product boundaries
- Improve Optimizer is an independent product concept, even where implementation currently shares this repository.
- Improve Optimizer is for general PC users; gaming is one usage direction, not the whole product.
- User intent classifies usage, not hardware. Objective system facts must be detected by the software.
- Primary usage directions are: Alltag, Arbeit, Gaming. Add subprofiles only when they materially change technical recommendations.
- Proof Yourself must remain neutral: no artificial funnels, cross-product ads, unlock banners, or forced upsells.
- Knowledge should be available contextually, not forced. Safety information remains mandatory where required.

## Driver & Firmware module
- Include driver and firmware update awareness as a planned Improve Optimizer capability.
- Detect relevant hardware/OEM identity and installed driver or firmware versions where authoritative detection is possible.
- Distinguish `UPDATE_AVAILABLE` from `UPDATE_RECOMMENDED`; a newer version is not automatically a better recommendation.
- Prefer the system/OEM support source where vendor-specific drivers or firmware are technically appropriate, especially for notebooks and OEM systems. Use the component manufacturer's official source where that is the correct authoritative source.
- Manufacturer-only source policy: link only to verified official OEM/component-manufacturer support or download pages. Do not use third-party driver portals, download aggregators, mirrors, or repackaged installers.
- Prefer stable official support/product pages over fragile direct executable URLs where practical.
- Do not host, mirror, redistribute, proxy, or repackage third-party driver/firmware binaries as part of this capability unless a future explicit legal/licensing review establishes permission.
- Clearly identify outbound actions as opening the manufacturer's official source.
- If the source cannot be verified as official, do not provide the download link and keep the state explicit.
- Initial implementation should be detection, assessment, recommendation, and manufacturer linking — not unattended automatic installation.
- Relevant categories may include GPU, chipset, LAN/WLAN, audio, motherboard/system drivers, and BIOS/UEFI/firmware where safe authoritative detection is available.
- BIOS/UEFI and firmware remain higher-risk operations. Availability detection/linking does not override the project's manual-critical safety boundary.
- Recommendation output should prioritize relevance rather than presenting every newer package as required; e.g. recommended, optional, no action, or insufficient evidence.
- Keep source/provider metadata so official links can be validated and maintained over time.

## Optimizer decision discipline
- Keep recommendation states and evidence maturity meaningful. Experimental, rejected, or no-benefit findings must not be promoted to ordinary recommendations.
- A valid result may be NO_CHANGE or INSUFFICIENT_EVIDENCE.
- Synthetic profiles validate decision contracts; never describe them as measured real systems.
- Do not claim real-world validation beyond evidence actually present in the repository.

## Network discipline
- Separate measurement/correlation from configuration causation.
- Do not claim that an observed adapter is the active game route unless that is actually established.
- Do not invent support for adapter settings that cannot yet be authoritatively detected.

## Collaboration and continuity

- Follow `docs/LOCAL_WORK_BRIDGE.md` for shared-checkout work and handoff.
- Reserve the final 20% of available usage for validation, local recovery,
  reviewed commits, verified push and handoff. Usage is not automatically measured.
- Do not report synchronization complete without remote commit verification.
- Prefer small, reviewable commits with descriptive messages.
- Keep secrets, tokens, passwords, personal credentials, and machine-specific private data out of the repository.
- Machine-specific setup may be documented with safe placeholders, but credentials must stay in the appropriate local/secret store.
- If local state conflicts with committed project state, stop and identify the conflict rather than silently overwriting work.
- Use branches or other isolation for substantial experimental work when appropriate.

## Scope note
These instructions make the repository the portable project memory for Codex collaboration. They do not cause Codex usage from one ChatGPT Business seat/account to be billed automatically to another seat, and they do not turn a local Codex installation into a centrally routed Workspace runtime. Those are separate platform capabilities.

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
- Prefer small, reviewable commits with descriptive messages.
- Keep secrets, tokens, passwords, personal credentials, and machine-specific private data out of the repository.
- Machine-specific setup may be documented with safe placeholders, but credentials must stay in the appropriate local/secret store.
- If local state conflicts with committed project state, stop and identify the conflict rather than silently overwriting work.
- Use branches or other isolation for substantial experimental work when appropriate.

## Scope note
These instructions make the repository the portable project memory for Codex collaboration. They do not cause Codex usage from one ChatGPT Business seat/account to be billed automatically to another seat, and they do not turn a local Codex installation into a centrally routed Workspace runtime. Those are separate platform capabilities.

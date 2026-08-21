# Improve Yourself — UI Specification

## 1. Design direction

Canonical standard theme: **Midnight / Metallic Blue**.

The interface should feel technical, calm, precise and mature. Metallic does **not** mean glow, chrome, neon or animated shine. It means subtle tonal changes across dark blue surfaces, comparable to automotive metallic paint under different viewing/light conditions: restrained highlights, depth and reflection cues without becoming decorative.

The binding visual evidence is `Improve_Yourself_Concept_Preview_Discord_Q98.pdf`. It establishes deep blue-black backgrounds, fine blue contours, selective silver/ice typography, controlled reflection bands and subtle technical texture. These cues should be reproduced with restraint and consistent tokens; they must not become a new neon, glassmorphism or RGB theme.

A light alternative is allowed later/where already supported: light surfaces with a slight cool blue cast rather than aggressive pure white.

## 2. Global shell

- One coherent application shell across modules.
- Persistent left navigation/sidebar on desktop/wide layouts.
- Clear selected-state treatment; restrained cyan/blue accent.
- Header/title area belongs visually to the application. **No white native-looking strip or foreign bright title block.**
- Wide layout should use available space rather than leave large dead margins.
- Smaller windows remain usable and responsive; do not solve responsiveness by simply shrinking everything.
- Primary content uses panels/cards with subtle borders and tonal separation.
- Avoid visual noise, excessive gradients, rainbow status systems and unnecessary decoration.
- Existing approved desktop/wide behavior takes precedence over older concept-preview proportions.

## 3. Typography

- `Orbitron` is the display/technical family: page titles, module names and deliberately sparse technical labels only. It must not be used for explanatory copy, tables or dense small UI text.
- `Inter` is the primary UI and reading family: navigation, buttons, controls, status, values, descriptions, tables and all normal labels use Inter Regular/Medium by default.
- The Portable build carries both font files under their SIL Open Font License and registers them privately for the application process. It must not rely on an installed machine-wide font or install a font globally.
- Page/module titles use a strong display weight; section headings use medium/semibold; tables, rules, explanations and dense information remain regular/medium.
- Do not make all information bold. Maintain readable hierarchy through weight, size and spacing rather than excessive color.

## 4. Color and state language

Base: very dark navy / midnight blue.
Secondary surfaces: slightly lighter blue-black panels.
Primary accent: restrained cool blue/cyan.

Semantic colors may be used when they carry meaning, but should remain secondary to the blue system. Do not turn the UI into a traffic-light dashboard.

Neutral analysis language is required. Prefer:
- Scene
- Review
- Analysis
- Rule matched / criteria met
- Review recommended
- Inspect / take a closer look

Avoid presenting automated cheat/guilt verdicts.

## 5. Interaction principles

- Few meaningful user decisions.
- Common actions visible; technical/advanced actions secondary.
- Do not expose internal implementation details unless they help understanding.
- Explanations belong in detail/info views rather than being repeated beside every control.
- Controls should use gamer-familiar concise language where it remains professional, e.g. `CT`, `T`, `Reset`.
- Destructive or system-changing actions require clear intent and reversibility where technically possible.

## 6. Module targets

### Home / Overview
Target: central entry point and status overview.

Page 03 of the concept preview is the direct structural and visual screen master, not only a source of general design principles. Preserve its complete Command-Center composition: shared sidebar; greeting/header with real status cards; six module-entry cards; progress overview, recent analyses and quick access in the next row; and the lower product-idea/community information areas in the same relative hierarchy and proportions. Real current data and honest unavailable states replace illustrative values or obsolete actions. Do not substitute a generic dashboard composition or force unsupported counters and gamified profile elements into V1.

### Demo Analyzer / Demo Preflight
Target: demo ingestion before interpretation.

After selecting a `.dem`, show objective preflight information first:
- map
- match/round information
- both teams
- player names
- parser/data-quality status
- useful event totals where available

The user should understand that the demo has been read correctly before analysis rules are applied.

### Improve Analyzer / Review
Target: core workflow, not a generic stats dashboard.

Flow:
`Demo -> Parser/Preflight -> Teams/Player selection -> Analysis profile -> Rule engine -> Scenes -> Review`

Player selection:
- `Full Demo`
- `Player Select`
- player dropdown + `Add Player`
- no duplicate selections
- quick `CT`, `T`, `Reset`

The screen should prioritize selected profile/rules, generated scenes, reasons/context and direct review actions. Statistics are supporting information, not the product centerpiece.

### Rules
Target: powerful but not oppressive.

- Rule list/table is primary.
- Active state preferably checkbox/toggle, not a separate activate/deactivate button.
- Double-click/open action exposes edit/details.
- Compact summary in list; detailed explanation in detail view.
- Import/export is secondary and lower priority.
- Do not prominently expose internal trigger-combination mechanics unless required for Custom/Advanced.
- Architecture represented conceptually as `Indicators -> Rules/Rule combinations -> Analysis profile -> Scenes`.

### Tactical Replay / 2D Viewer
Target: tactical understanding and rapid return to the original demo.

Preserve the approved concept: map is dominant central element, timeline/events nearby, filters contextual rather than overwhelming, scene/tick actions clearly available. Existing implemented zoom/pan/reset behavior is authoritative.

Third-person/fixed-third-person options already approved in the functional viewer should fit this language rather than be redesigned as a separate product.

### 3D / POV
The product direction is already defined, but full visual integration may still be implementation-dependent. Match the same shell and controls. Do not invent a separate visual identity.

### System Check / Improve Optimizer
Target: safe, transparent, understandable system optimization.

The concept-preview hierarchy is valid: system overview first, recommendations second, details/evidence accessible. Current read-only boundaries and current functional contracts override any old mockup action that implies unsupported automatic application.

Distinguish clearly:
- detected/current value
- evaluation
- recommended/official value where available
- source/evidence

No blind `best settings` presentation.

### Reports
Use the same card/table language. Reports should answer: what was analyzed, what was found, why a scene/result exists, and how to review it. Dense data should remain scannable.

### Settings
Keep restrained. Only real user-configurable product settings belong here. Do not create options merely to fill the page.

### My Improvement
Concept direction is valid for later/persistent player-development functionality, but current V1 capability determines what is shown. Do not fabricate longitudinal scores/trends if they are not backed by data.

### Improve Benchmark
Visual language follows the same shell. Benchmark runtime/map development is a separate workstream and must not be changed merely to match a UI concept.

## 7. Explicitly out of current UI scope

Do not add or restore:
- OBS integration
- Sony Vegas/video-editor integration
- automatic rendering
- automatic clip creation
- forced Windowed/Borderless workflow
- clip guidance blocks left over from prototypes

These are not current V1/Experimental UI requirements.

## 8. Acceptance check

A screen is visually consolidated when:
1. it clearly belongs to the same application as every other tab;
2. no white/foreign shell elements break the Midnight theme;
3. primary vs secondary information is obvious;
4. current functionality is preserved;
5. old mockup-only features are not fabricated;
6. a new user can identify the next action without developer knowledge.
7. surface depth, blue contour/light cues and brand treatment remain recognizably aligned with the visual master;
8. illustrative master data or unavailable actions have not been turned into fake functionality.

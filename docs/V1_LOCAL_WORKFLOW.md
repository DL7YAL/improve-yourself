# Integrated local V1 workflow

`iy-workflow` connects the first usable local product path without applying any
system optimization:

1. create an `iy.system_check/v1` read-only machine assessment;
2. analyze one explicit local demo into `iy.analysis/v1`;
3. export bounded Multi-Kill scenes into `iy.replay/v1`;
4. create a self-contained local 2D viewer;
5. create a reduced local review start page with system findings, data quality,
   scene list and viewer link;
6. write an `iy.workflow/v1` manifest linking all artifacts.

```powershell
.venv\Scripts\iy-workflow '<match.dem.zst>' --output results\workflow
```

For a local Mirage radar resource:

```powershell
.venv\Scripts\iy-workflow '<match.dem.zst>' --output results\workflow `
  --radar "$env:USERPROFILE\.awpy\maps\de_mirage.png" `
  --pos-x -3230 --pos-y 1713 --scale 5
```

The run directory is keyed by the demo SHA-256 prefix. Its manifest records
only relative artifact paths, the source hash, local/read-only policy and the
mandatory human-review boundary. It does not contain the original demo path.

Open `review.html` as the human entry point. It summarizes findings without
copying raw JSON into the interface and links to the generated `viewer.html`.

`READY_FOR_REVIEW` means processing succeeded; it does not mean that a marker
is suspicious or that any player conclusion has been reached. The workflow
does not change Windows, apply an Optimizer profile, elevate privileges, upload
data or make an automated cheat verdict.

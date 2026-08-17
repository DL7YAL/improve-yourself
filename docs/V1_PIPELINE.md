# V1 validation pipeline

`tools/dev/Run-V1Pipeline.ps1` provides the smallest reproducible local path
from a representative input to a reviewable PASS/FAIL result:

1. restore the Python 3.13 environment from `requirements.lock`;
2. check installed dependency consistency;
3. run all automated tests;
4. smoke-test the `iy-analyze` command;
5. analyze one explicit local demo;
6. validate the complete `iy.analysis/v1` contract and invariants;
7. write one aggregate `iy.pipeline/v1` evidence file.

Run it from the repository root:

```powershell
.\tools\dev\Run-V1Pipeline.ps1 -Demo 'D:\path\to\match.dem.zst'
```

Outputs are written below `results/pipeline/<timestamp>-<sha-prefix>/` and are
ignored by Git. `pipeline-evidence.json` records the exact commit and dirty-state
indicator, timings, source hash, check outcomes, and the aggregate regression
summary. It does not record the demo path, player names, or detailed kill data.

The pipeline stops at the first failing step and still writes a FAIL evidence
file. A PASS proves the documented local baseline and analyzer contract for the
selected input; it does not replace visual CS2/Hammer runtime validation.

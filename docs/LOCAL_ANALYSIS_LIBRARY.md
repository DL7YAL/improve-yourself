# Local Analysis Library

The local Analysis Library is a small navigation index, not another workflow
format or a copy of analysis data. It records only explicitly registered
completed `iy.demo_workflow/v1` references and presentation metadata. Demo,
Replay V2, scenes and analysis payloads remain exclusively in their canonical
workflow artifacts.

Registration happens only after the app creates a completed review workflow or
after the user explicitly opens an existing workflow. There is no result-folder
scan, no newest-result selection and no automatic discovery. Each list entry is
validated again with the existing canonical workflow validator before it can be
used; invalid, tampered, unavailable and legacy V1 entries remain disabled.

The library distinguishes `READY`, `MISSING SOURCE`, `INVALID`, `TAMPERED`,
`LEGACY V1`, and `UNAVAILABLE`. Removing an entry deletes only its local index
reference, never a demo or a workflow artifact. Source relinking remains the
existing explicit hash-matching flow; a nonmatching demo is rejected.

## Manual acceptance for Brix

1. Create a completed V2 analysis, then reopen it explicitly in Analyzer.
2. Restart Analyzer and inspect the registered library entry; it must be READY
   only after revalidation.
3. Open Review or Tactical Replay from the loaded valid workflow.
4. Register/open the same workflow again and confirm only one entry remains.
5. Remove the entry and confirm `demo-workflow.json` and all artifacts remain.
6. Modify a workflow artifact and confirm its entry is disabled as TAMPERED.
7. Clear the source-demo name, use the existing explicit relink action with a
   matching hash, and confirm a nonmatching demo is rejected.

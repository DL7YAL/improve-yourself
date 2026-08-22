IMPROVE YOURSELF — EXTERNAL TEST CANDIDATE

Distribution
------------
This is an Experimental portable build. No installation, administrator rights,
system configuration change, network share or account is required.

1. Extract the complete ZIP into a writable local folder.
2. Start "Improve Yourself.exe" from the extracted folder.
3. Do not start the executable directly from the ZIP preview.

Local data boundary
-------------------
The application keeps its generated local results below:
%LOCALAPPDATA%\Improve Yourself\Experimental\results

It does not upload demos, system-check evidence, analysis data or notes as part
of this test candidate. System Check remains read-only. No Optimizer setting,
registry value, driver, BIOS or network setting is applied by this build.

Suggested smoke test
--------------------
1. Open Dashboard, then "Demo laden" or "Analyzer öffnen".
2. In Analyzer / Übersicht, choose one local CS2 .dem file.
3. Confirm that map, rounds, named line-ups and parser status are shown.
4. In Analyzer / Analyse, use the existing profile and choose a permitted
   player selection before starting analysis.
5. In Analyzer / Review, select a real generated situation and open
   "Tactical Replay". Return to Review afterwards.
6. Optionally, with the matching demo already loaded in properly started local
   CS2 Workshop Tools, use "In CS2 ansehen". If CS2 / NetCon is unavailable,
   the build must show the local error state and must not claim a seek happened.

Please report
-----------------
- whether the application starts after extracting the whole ZIP;
- any visible navigation break, clipped content or unreadable state;
- whether a real demo reaches Overview -> Analyse -> Review -> Tactical Replay;
- the exact error text and the step that triggered it when a check fails.

Integrity
---------
The sibling file "experimental-build.json" records SHA-256 hashes for the EXE
and the Portable ZIP produced by the build gate. Compare it before sharing a
test result if archive integrity is in doubt.

Scope reminder
--------------
This candidate is for local, read-only workflow evaluation. It does not include
an installer, automatic updates, system changes, clip/video output, benchmark
map changes or any remote service.

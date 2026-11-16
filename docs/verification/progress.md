# Reorganization verification

The approved six-stage migration is complete for the local release scope. All six [issue cards](../development/project-board.json) are closed against actual executed checks. The [final handoff](final-handoff.md) and [machine-readable record](reorganization/final.json) are the current authorities.

The final results are 221 backend tests, 12 frontend tests, 10 browser workflows and 52/52 deterministic evaluation cases. Coverage explicitly includes all eight production source directories and is **89.30%**, above the 86% gate. Static/import/class/schema checks, dependency audits and 40 security regressions pass. The complete CI gate passed; after correcting coverage source selection, static checks and tests were repeated with the expanded denominator.

Eight noneditable wheels pass installation outside the checkout with no PYTHONPATH assistance. Packaged migrations, complete model metadata, fixtures, 52 cases, templates, fonts/licenses and seven output formats pass readback. A synthetic database created by the old implementation preserves sessions, encrypted credentials, artifacts, pending approvals and interrupted/unknown outcomes.

Independent clients pass all five endpoints over HTTP and stdio (10/10), and Inspector passes its HTTP/stdio checks (10/10). The no-network read-only non-root container and one-service Compose stack pass the 31-tool/four-file smoke check, frontend serving, packaged-case loading and cleanup. Fresh evidence and captures live under [demo/evidence/reorganization](../../demo/evidence/reorganization/) and [screenshots/reorganization](../../demo/screenshots/reorganization/).

The [complete move inventory](reorganization/move-inventory.json) maps 149 baseline files; [integrity checks](reorganization/integrity.json) verify rollback sources and 41 preserved hashes. The 213 baseline backend identities and 22 frontend/browser identities are mapped, and all 52 case definitions remain exact. Source rollback is available from the ignored local archive described in the inventory; private data was not reset or moved.

The repeated pre-migration baseline remains separate: 213 backend tests with 86.38% coverage, 12 frontend tests and 10 browser workflows. Original core [historical records](historical/README.md), [baseline evidence](../../demo/evidence/baseline/) and specification hashes are preserved.

Live Google execution, approved live writes, real-model quality, domain-dependent Drive selection, native Office layout, remote CI and deployment remain NOT_RUN. See the [acceptance matrix](acceptance-matrix.md) for precise prerequisites. No publication or real external write was performed.

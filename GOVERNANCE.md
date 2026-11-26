# Governance

AstraX is a community project led by a **benevolent maintainer** model, with the aim of growing a maintainer team as the project grows.

## Roles
- **Users** - use AstraX, report problems, ask questions.
- **Contributors** - anyone who opens an issue, PR, review, doc fix or test.
- **Maintainers** - triage, review and merge; listed in [MAINTAINERS.md](MAINTAINERS.md).
- **Project lead** - final say when consensus fails; owns releases and the roadmap.

## Decision making
1. Small changes: one maintainer approval and passing CI.
2. Physics/model changes: must include tests against an analytic or reference value and a PHYSICS.md update; two approvals preferred.
3. Breaking changes (file formats, public API): open a *design discussion* issue first, document it in `docs/developer/DECISIONS.md`, and announce in the changelog.
4. Disagreement is resolved by discussion, then by the project lead.

## Scientific integrity policy
AstraX must never present unvalidated results as research-grade predictions. Any new model states its assumptions, limitations and validation status in `docs/PHYSICS.md`.

## Becoming a maintainer
Sustained, high-quality contributions plus an invitation from the existing maintainers. Inactive maintainers (12 months) move to *emeritus*.

## Changes to this document
By pull request, with maintainer approval.

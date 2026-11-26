# Roadmap

> Plans, not promises. Ideas are tracked as GitHub issues with the `roadmap` label. Vote with 👍 on the issues you care about.

## 4.0 (this release) - "Foundation"
Professional repository: docs for users/testers/developers, CI, release automation, templates, governance, health tests. No behaviour change from 3.2.1.

## 4.1 - "Look and feel"
- Planet textures (procedural + optional image textures with Pillow).
- Phobos and Deimos; more moons.
- Screenshot gallery/video tour; in-app guided tutorials ("first launch" wizard).
- Accessibility: keyboard navigation audit, colour-blind friendly palette.

## 4.2 - "Rendezvous & guidance"
- Rendezvous and docking scenarios; target-relative frames.
- Gravity-assist (flyby) planner; patched-conic trajectory preview.
- Gimbal/attitude dynamics (rotational motion) as an optional model.

## 4.3 - "Research grade"
- Validation suite against JPL Horizons snapshots (offline fixtures) and published ascent profiles.
- Perturbation models: J2, third body options, solar radiation pressure.
- Batch/CLI runner (`astrax-run scenario.json`) and reproducible-study files.

## 5.0 - "Platform"
- PySide6 (LGPL) support or migration (see THIRD_PARTY_NOTICES).
- Plugin API for guidance modes, failure models and panels.
- Optional compiled/GPU-accelerated N-body core (Numba/Cython) for large studies.
- Multi-vehicle simulations; network/collaborative mission control (exploratory).

## Always welcome
Tests, docs, translations of docs, example rockets and scenarios, bug fixes.

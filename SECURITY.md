# Security policy

## Supported versions
| Version | Supported |
|---|---|
| 4.x | yes |
| < 4.0 | no (please upgrade) |

## Reporting a vulnerability
**Do not open a public issue for security problems.** Use GitHub's private reporting: *Security ▸ Report a vulnerability* in this repository. If that is unavailable, contact the maintainers listed in [MAINTAINERS.md](MAINTAINERS.md).

Please include: affected version, platform, a description, and steps or a proof of concept. You will get an acknowledgement within **5 working days**; we aim to provide a fix or mitigation plan within **30 days** and will credit you unless you prefer otherwise.

## Scope and known design notes
- **User flight-computer scripts** (`Mission control ▸ Flight computer`) run Python in-process with restricted builtins. This is a convenience limit, **not a security sandbox**. Never run scripts from people you do not trust. Treat this as documented behaviour, not a vulnerability.
- AstraX opens local files only (JSON, OBJ, CSV). Scenario/rocket/session loaders parse JSON; they do not execute code.
- AstraX makes **no network requests** at runtime.
- The `tools/` scripts (`build_branding.py`) use Playwright/Chromium and are developer-only.

## Hardening tips for deployers
Run from a virtual environment, keep dependencies updated (Dependabot is enabled), and verify release checksums.

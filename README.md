# Caregiver Coordination Guide

A plain-English manual for organizing the care of an aging or ill loved one — the companion
to the *Health Admin Kit* (which covers **your own** paperwork; this one covers **theirs**).

Written in the same friendly spirit as all Asdale Dynamics, LLC guides: clear, warm, step
by step, never condescending. Everything is local-first: no accounts, no cloud, no data
leaving your machine.

## What's inside

- **The first-calls checklist** — the first ten phone calls after a diagnosis or crisis, in order.
- **The document grab-list** — every paper you may need to find, and where it hides.
- **Medication and doctor logs** — fill-in worksheets that make nurses and doctors relax.
- **Splitting tasks without feuds** — a worksheet-based system for siblings and family.
- **Weekly updates AI can draft** — copy-paste prompts that turn your notes into family letters.
- **Respite and guilt management** — why breaks are maintenance, not weakness.
- **Worksheets** — ten blank, printable templates.
- **Glossary and disclaimer** — the words hospital staff use, translated; plus the promise
  that this is coordination help, **never medical advice**.

## How to build the site

Requirements: Python 3.8+ (standard library only — no installs).

```bash
./build.sh        # or: python3 build.py
```

Output lands in `site/`. Open `site/index.html` in a browser, or print any page — styles are
print-friendly by design. Worksheets live under `site/worksheets/…`.

## How to run the tests

```bash
./test.sh         # or: python3 tests/run_tests.py
```

Tests verify the build output, links, worksheet templates, disclaimer coverage on every
page, and scan for accidental secrets or personal-data patterns.

## Repository layout

| Path | What it is |
| --- | --- |
| `docs/` | The manual, chapter by chapter (markdown) |
| `worksheets/` | Blank fill-in templates (markdown) |
| `build.py` + `build.sh` | The build script (stdlib Python) |
| `tests/run_tests.py` | The test suite (stdlib Python) |
| `site/` | Generated static site (git-ignored; rebuild anytime) |

## Copyright & license

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Asdale Dynamics, LLC.

A project by **Asdale Dynamics, LLC** — beginner-friendly AI education, books, and practical
tools. Learn more at the [Asdale Dynamics hub on GitHub](https://dylanasdale.github.io).

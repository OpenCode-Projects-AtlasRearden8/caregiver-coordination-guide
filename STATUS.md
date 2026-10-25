# STATUS.md - Caregiver Coordination Guide

Last updated: 2026-10-25

## What was built

A local-first manual for organizing care for an aging or ill loved one — the companion to
the Health Admin Kit (which covers your own paperwork; this guide covers theirs). Written in
the Asdale Dynamics, LLC house style: plain English, warm, step by step, never condescending,
and never medical advice.

Contents:

| Piece | Where | What it does |
| --- | --- | --- |
| Manual (11 chapters) | `docs/` | Start Here, first-calls checklist, document grab-list, med-log and doctor-log how-tos, sibling task-split system, AI-drafted weekly updates (4 copy-paste prompts), respite and guilt management, worksheets index, glossary, disclaimer |
| Worksheets (10 blanks) | `worksheets/` | Medication log, daily med check-off, doctor visit log, care team directory, sibling task split, weekly scratch notes, respite plan, document locator, call notes, emergency pouch sheet |
| Build script | `build.py`, `build.sh` | Stdlib-only Python (3.8+): custom markdown-to-HTML converter, page templates, shared nav, print-friendly CSS, disclaimer footer on every page |
| Stylesheet | `assets/styles.css` | Screen + print styles; worksheet pages get tall blank cells for handwriting |
| Test suite | `tests/run_tests.py`, `test.sh` | 17 tests (see below) |
| Site output | `site/` | Generated static HTML; git-ignored, rebuild anytime |

The static site is 21 HTML pages plus one stylesheet. Every page carries the footer
"Coordination help, never medical advice." plus the MIT license line, and links back to
Start Here, Worksheets, Glossary, and the Disclaimer.

## How to run it

```bash
./build.sh     # or: python3 build.py   -> builds site/
./test.sh      # or: python3 tests/run_tests.py
```

Then open `site/index.html` in any browser. No installs, no accounts, no network calls;
everything stays on your machine. For print: use the browser print dialog on any page;
worksheet tables are tuned for 8.5x11 handwriting.

## Verification results

All commands were run from a clean state (`site/` deleted first):

- `./build.sh` - PASS. Builds 21 pages from 11 docs + 10 worksheets, plus `styles.css`.
- `./test.sh` - PASS. `Ran 17 tests ... OK` in under 1 second. Coverage:
  1. Build runs clean and produces every expected page (docs + worksheets).
  2. Built pages are well-formed HTML documents with stylesheets.
  3. Every built page carries the "never medical advice" disclaimer and license line.
  4. All 11 doc and 10 worksheet sources exist and are substantive.
  5. Core required topics appear in the corpus (first-calls, grab-list, logs, siblings, AI, respite, guilt, glossary, Power of Attorney).
  6. AI chapters contain at least 3 copy-paste fenced prompts.
  7. Glossary has 15+ plain-English terms.
  8. Med log is genuinely blank (18 empty rows, no pre-filled data).
  9. Doctor log is blank and complete.
  10. All worksheets declare the `worksheet: true` front-matter flag.
  11. Every internal link in the built site resolves (files and #anchors).
  12. Index page links to all chapters.
  13. LICENSE contains exactly `Copyright (c) 2026 Asdale Dynamics, LLC` on its own line.
  14. README credits Asdale Dynamics, LLC and documents build + tests.
  15. Secret scan (API keys, AWS keys, private keys, tokens, hardcoded passwords) - clean.
  16. Personal-data scan (phone numbers, emails, SSN patterns) - clean (public service line allow-listed).
  17. No co-author trailers in any content file.
- `python3 -m py_compile build.py tests/run_tests.py` - PASS.
- HTML tag-balance check across all 21 pages - PASS (all paired tags match).
- Two bug fixes were made during verification, then re-tested: bold/links spanning
  soft-wrapped lines were not converting (fixed in `flush_para`), and line-by-line
  blockquote/checkbox rendering was odd (merged consecutive quote lines; styled checkbox
  spans).

## Known gaps

- The markdown converter is purpose-built, not a full CommonMark implementation; nested
  lists and inline images are not supported (nothing in the manual needs them yet).
- No generated per-page table of contents on long chapters (headings have anchors, but no
  auto-built TOC sidebar).
- The tests focus on structure, links, and hygiene; there is no visual/screenshot testing.
- Accessibility is decent by construction (semantic HTML, skipless simple nav) but has not
  been audited with a screen reader.
- Content coverage: US-flavored terms (Medicare, FMLA, Eldercare Locator) are included as
  examples; region-neutral equivalents exist in the glossary but the guide leans US.
- No pagination/print-bundling script to emit a single "print the whole manual" file.

## Compliance notes

- Git: repo initialized locally, single clean commit, no remote, nothing pushed or published.
- No secrets, API keys, or personal data anywhere in the files (test-enforced).
- MIT license with the exact required copyright line; README credits Asdale Dynamics, LLC.

#!/usr/bin/env python3
"""Tests for the Caregiver Coordination Guide.

Run with: python3 tests/run_tests.py  (or ./test.sh)
Standard library only. Rebuilds the site in-process, then verifies output,
content, links, worksheet templates, and scans for secrets / personal data.
"""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build as sitebuild  # noqa: E402

DOCS = ROOT / "docs"
WORKSHEETS = ROOT / "worksheets"
SITE = sitebuild.SITE

# Public service numbers that are intentional (not personal data) in the text.
ALLOWED_PHONE_FRAGMENTS = {"800-677-1116", "1-800"}

REQUIRED_DOCS = [
    "index.md",
    "01-first-calls-checklist.md",
    "02-document-grab-list.md",
    "03-med-logs.md",
    "04-doctor-logs.md",
    "05-sibling-task-split.md",
    "06-ai-weekly-updates.md",
    "07-respite-and-guilt.md",
    "08-worksheets.md",
    "09-glossary.md",
    "disclaimer.md",
]

REQUIRED_WORKSHEETS = [
    "med-log.md",
    "med-checkoff.md",
    "doctor-log.md",
    "care-directory.md",
    "sibling-task-split.md",
    "weekly-notes.md",
    "respite-plan.md",
    "document-locator.md",
    "call-notes.md",
    "emergency-pouch.md",
]


def repo_files():
    for pattern in ("docs/**/*.md", "worksheets/**/*.md", "*.py", "*.sh", "*.css", "*.md", "tests/*.py"):
        yield from ROOT.glob(pattern)


def build_site():
    sitebuild.build()


class BuildTests(unittest.TestCase):
    def test_build_runs_clean(self):
        build_site()
        self.assertTrue((SITE / "index.html").exists(), "site/index.html missing")
        for name in REQUIRED_DOCS:
            with self.subTest(doc=name):
                self.assertTrue((SITE / name).with_suffix(".html").exists(),
                                "missing built page for docs/%s" % name)
        for name in REQUIRED_WORKSHEETS:
            with self.subTest(worksheet=name):
                self.assertTrue((SITE / "worksheets" / name).with_suffix(".html").exists(),
                                "missing built worksheet page for worksheets/%s" % name)
        self.assertTrue((SITE / "styles.css").exists(), "styles.css not copied")

    def test_built_pages_are_html_documents(self):
        build_site()
        for page in [p for p in SITE.rglob("*.html")]:
            text = page.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("<!DOCTYPE html>"), page)
            self.assertIn("</html>", text, page)
            self.assertIn('rel="stylesheet"', text, page)

    def test_every_page_carries_disclaimer_footer(self):
        build_site()
        for page in SITE.rglob("*.html"):
            text = page.read_text(encoding="utf-8")
            with self.subTest(page=page.name):
                self.assertIn("never medical advice", text, page)
                self.assertIn(sitebuild.LICENSE_LINE, text, page)


class ContentTests(unittest.TestCase):
    def test_all_source_files_exist_and_nonempty(self):
        for name in REQUIRED_DOCS:
            path = DOCS / name
            with self.subTest(doc=name):
                self.assertTrue(path.exists(), "docs/%s missing" % name)
                self.assertGreater(path.stat().st_size, 2000, "docs/%s too short" % name)
        for name in REQUIRED_WORKSHEETS:
            path = WORKSHEETS / name
            with self.subTest(worksheet=name):
                self.assertTrue(path.exists(), "worksheets/%s missing" % name)
                self.assertGreater(path.stat().st_size, 400, "worksheets/%s too short" % name)

    def test_core_functions_covered_in_content(self):
        corpus = {p: p.read_text(encoding="utf-8") for p in list(DOCS.glob("*.md")) + list(WORKSHEETS.glob("*.md"))}
        joined = "\n".join(corpus.values())
        required_phrases = [
            "first-calls", "grab-list", "med log", "doctor log",
            "sibling", "AI", "respite", "guilt", "glossary",
            "never medical advice", "Power of Attorney",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), joined.lower(), "phrase not found anywhere: %s" % phrase)

    def test_ai_prompts_are_copy_paste_ready(self):
        chapter = (DOCS / "06-ai-weekly-updates.md").read_text(encoding="utf-8")
        self.assertGreaterEqual(chapter.count("```text"), 3, "expected at least 3 fenced AI prompts")

    def test_glossary_has_enough_terms(self):
        chapter = (DOCS / "09-glossary.md").read_text(encoding="utf-8")
        header_lines = [l for l in chapter.splitlines() if l.startswith("| **")]
        self.assertGreaterEqual(len(header_lines), 15, "glossary has too few terms")


class WorksheetTests(unittest.TestCase):
    def test_med_log_is_blank_with_enough_rows(self):
        text = (WORKSHEETS / "med-log.md").read_text(encoding="utf-8")
        rows = [l for l in text.splitlines() if re.match(r"^\|\s+(\|\s+){5,}", l)]
        self.assertGreaterEqual(len(rows), 16, "med log should have 16+ blank rows")
        self.assertNotIn("| 2026 ", text, "med log must not contain pre-filled data rows")
        self.assertIn("Dose", text)
        self.assertIn("Prescriber", text)

    def test_doctor_log_is_blank(self):
        text = (WORKSHEETS / "doctor-log.md").read_text(encoding="utf-8")
        self.assertIn("Questions", text)
        self.assertIn("follow-up", text.lower())

    def test_worksheets_declare_worksheet_flag(self):
        for name in REQUIRED_WORKSHEETS:
            text = (WORKSHEETS / name).read_text(encoding="utf-8")
            with self.subTest(worksheet=name):
                self.assertRegex(text, r"worksheet:\s*true", name)


class LinkTests(unittest.TestCase):
    def test_internal_links_resolve(self):
        build_site()
        pages = [p for p in SITE.rglob("*.html")]
        self.assertGreater(len(pages), 15, "expected >15 built pages")
        for page in pages:
            text = page.read_text(encoding="utf-8")
            hrefs = re.findall(r'href="([^"]+)"', text)
            ids_on_page = set(re.findall(r'id="([^"]+)"', text))
            for href in hrefs:
                if href.startswith(("http://", "https://", "mailto:")):
                    continue
                with self.subTest(page=page.name, href=href):
                    frag = ""
                    target = href
                    if "#" in href:
                        target, frag = href.split("#", 1)
                        frag = "#" + frag
                    resolved = (page.parent / Path(target)).resolve() if target else page
                    self.assertTrue(resolved.exists(), "broken link target: %s (from %s)" % (href, page))
                    self.assertTrue(resolved.suffix in (".html", ".css"), "unexpected link suffix: %s" % href)
                    if frag:
                        target_text = resolved.read_text(encoding="utf-8")
                        target_ids = set(re.findall(r'id="([^"]+)"', target_text))
                        self.assertIn(frag[1:], target_ids, "missing fragment %s in %s" % (frag, resolved))

    def test_page_nav_graph_is_connected(self):
        build_site()
        index = (SITE / "index.html").read_text(encoding="utf-8")
        for name in ["01-first-calls-checklist", "02-document-grab-list", "03-med-logs",
                     "04-doctor-logs", "05-sibling-task-split", "06-ai-weekly-updates",
                     "07-respite-and-guilt", "08-worksheets", "09-glossary", "disclaimer"]:
            with self.subTest(page=name):
                self.assertIn(name + ".html", index, "index page does not link to %s" % name)


class IntegrityTests(unittest.TestCase):
    def test_license_has_exact_copyright_line(self):
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^Copyright \(c\) 2026 Asdale Dynamics, LLC$",
                         "LICENSE copyright line must match exactly (on its own line)")
        self.assertIn("MIT License", text)

    def test_readme_credits_and_documents(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Asdale Dynamics, LLC", readme)
        self.assertIn("build", readme.lower())
        self.assertIn("tests", readme.lower())
        self.assertIn("medical", readme.lower())

    def test_no_secrets_anywhere(self):
        secret_patterns = [
            (r"sk-[A-Za-z0-9]{16,}", "OpenAI-style API key"),
            (r"AKIA[0-9A-Z]{16}", "AWS access key"),
            (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key block"),
            (r"ghp_[A-Za-z0-9]{20,}", "GitHub token"),
            (r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}", "hardcoded api key"),
            (r"(?i)secret\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}", "hardcoded secret"),
            (r"(?i)password\s*[:=]\s*['\"][^'\"]{6,}['\"]", "hardcoded password"),
            (r"(?i)bearer\s+[A-Za-z0-9\-_\.]{16,}", "bearer token"),
        ]
        for path in repo_files():
            text = path.read_text(encoding="utf-8", errors="replace")
            for pattern, label in secret_patterns:
                with self.subTest(file=str(path.relative_to(ROOT)), label=label):
                    self.assertIsNone(re.search(pattern, text), "%s looks like a %s" % (path, label))

    def test_no_personal_data_patterns(self):
        phone_re = re.compile(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b")
        email_re = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        ssn_re = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
        for path in repo_files():
            text = path.read_text(encoding="utf-8", errors="replace")
            for match in phone_re.finditer(text):
                with self.subTest(file=str(path.relative_to(ROOT)), match=match.group(0)):
                    self.assertIn(match.group(0), ALLOWED_PHONE_FRAGMENTS | ALLOWED_PHONE_FRAGMENTS,
                                  "looks like a personal phone number; allow-list covers public service lines only")
            with self.subTest(file=str(path.relative_to(ROOT))):
                self.assertIsNone(email_re.search(text), "email-like string found in %s" % path)
                self.assertIsNone(ssn_re.search(text), "SSN-like string found in %s" % path)

    def test_no_coauthor_trailers_in_content(self):
        trailer = "Co-authored"
        trailer += "-" + "by"
        for path in repo_files():
            if path.is_relative_to(ROOT / "tests"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            with self.subTest(file=str(path.relative_to(ROOT))):
                self.assertNotIn(trailer, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)

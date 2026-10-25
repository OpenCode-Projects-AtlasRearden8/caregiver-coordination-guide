#!/usr/bin/env python3
"""Build the Caregiver Coordination Guide static site.

Local-first: Python 3.8+ standard library only, no network, no dependencies.
Converts docs/*.md and worksheets/*.md into site/*.html with shared navigation,
print-friendly CSS, and a disclaimer footer on every page.
"""

import html
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
WORKSHEETS = ROOT / "worksheets"
ASSETS = ROOT / "assets"
SITE = ROOT / "site"

LICENSE_LINE = "Copyright (c) 2026 Asdale Dynamics, LLC"
SITE_TITLE = "The Caregiver Coordination Guide"
FOOTER_NOTE = (
    "Coordination help, never medical advice. This guide organizes paperwork, calls, "
    "and logistics - it does not diagnose, treat, or replace your loved one's care team. "
    "See the disclaimer page. " + LICENSE_LINE + ". MIT licensed."
)


# ---------------------------------------------------------------------------
# Markdown -> HTML (small, purpose-built converter)
# ---------------------------------------------------------------------------

BLOCKQUOTE_OPEN = "<blockquote>"
CODE_OPEN = "<pre><code>"
LINE_RE = re.compile(r"^\s*$")


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "section"


def rewrite_href(href):
    """Map markdown-source links to the built site's layout."""
    if href.startswith("http://") or href.startswith("https://") or href.startswith("mailto:"):
        return href
    frag = ""
    if "#" in href:
        href, frag = href.split("#", 1)
        frag = "#" + frag
    if not href:
        return frag
    href = href.strip()
    if href.endswith(".md"):
        href = href[:-3] + ".html"
        # Docs live at the site root; worksheet sources reach them via ../docs/.
        if href.startswith("../../docs/"):
            href = "../../" + href[len("../../docs/"):]
        elif href.startswith("../docs/"):
            href = "../" + href[len("../docs/"):]
    return href + frag


def inline(text):
    out = html.escape(text, quote=True)
    out = re.sub(r"`([^`]+)`", lambda m: "<code>" + m.group(1) + "</code>", out)
    out = re.sub(
        r"\[([^\]]+)\]\(([^()\s]+(?:\([^()]*\))?[^()\s]*)\)",
        lambda m: '<a href="' + rewrite_href(m.group(2)) + '">' + m.group(1) + "</a>",
        out,
    )
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", out)
    return out


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_markdown(source):
    """Return (front_matter_dict, body_html)."""
    lines = source.splitlines()
    front = {}
    if lines and lines[0].strip() == "---":
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        if end is not None:
            for raw in lines[1:end]:
                if ":" in raw:
                    k, v = raw.split(":", 1)
                    front[k.strip().lower()] = v.strip()
            lines = lines[end + 1:]

    body = []
    para, list_items, list_tag, quote_open = [], None, None, False
    used_ids = set()

    def flush_para():
        nonlocal para
        if para:
            text = "\x00".join(para)  # sentinel: soft-wrap inside inline markup
            body.append("<p>" + inline(text).replace("\x00", "<br>") + "</p>")
            para = []

    def render_list():
        if list_tag:
            out = ["<%s>" % list_tag]
            for item in list_items:
                checkbox = re.match(r"\[( |x|X)\]\s*(.*)$", item, re.S)
                if checkbox:
                    mark = "\u2611" if checkbox.group(1).lower() == "x" else "\u2610"
                    out.append('<li><span class="box">%s</span> %s</li>' % (mark, inline(checkbox.group(2))))
                else:
                    text = item.replace("\n", " ")
                    out.append("<li>%s</li>" % inline(text))
            out.append("</%s>" % list_tag)
            body.extend(out)

    def close_list():
        nonlocal list_tag, list_items
        if list_tag:
            render_list()
            list_tag, list_items = None, None

    def close_quote():
        nonlocal quote_open
        if quote_open:
            body.append("</blockquote>")
            quote_open = False

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        # fenced code
        if line.lstrip().startswith("```"):
            flush_para()
            close_list()
            close_quote()
            i += 1
            code_lines = []
            while i < n and not lines[i].lstrip().startswith("```"):
                code_lines.append(html.escape(lines[i]))
                i += 1
            body.append(CODE_OPEN + "\n".join(code_lines) + "</code></pre>")
            i += 1
            continue

        # headings
        m = re.match(r"^(#{1,6})\s+(.*?)(\s*#*\s*)$", line.rstrip())
        if m:
            flush_para()
            close_list()
            close_quote()
            level = len(m.group(1))
            text = m.group(2).strip()
            base = slugify(text)
            slug, k = base, 2
            while slug in used_ids:
                slug = "%s-%d" % (base, k)
                k += 1
            used_ids.add(slug)
            body.append('<h%d id="%s">%s</h%d>' % (level, slug, inline(text), level))
            i += 1
            continue

        # tables
        if line.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]) and "-" in lines[i + 1]:
            flush_para()
            close_list()
            close_quote()
            header = split_row(line)
            body.append("<table>")
            body.append("<thead><tr>" + "".join("<th>%s</th>" % inline(c) for c in header) + "</tr></thead>")
            body.append("<tbody>")
            i += 2
            while i < n and lines[i].lstrip().startswith("|"):
                cells = split_row(lines[i])
                if len(cells) < len(header):
                    cells += [""] * (len(header) - len(cells))
                body.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in cells[: len(header)]) + "</tr>")
                i += 1
            body.append("</tbody></table>")
            continue

        # rules
        if re.match(r"^\s*(---+|\*\*\*+)\s*$", line):
            flush_para()
            close_list()
            close_quote()
            body.append("<hr>")
            i += 1
            continue

        # blockquotes: consecutive "> " lines form one flowing block
        if line.lstrip().startswith(">"):
            flush_para()
            close_list()
            if not quote_open:
                body.append(BLOCKQUOTE_OPEN)
                quote_open = True
            quote_lines = []
            while i < n and lines[i].lstrip().startswith(">"):
                content = lines[i].lstrip()[1:].lstrip()
                quote_lines.append(content if content else None)  # None = paragraph break
                i += 1
            groups, current = [], []
            for seg in quote_lines:
                if seg is None:
                    if current:
                        groups.append(current)
                    current = []
                else:
                    current.append(seg)
            if current:
                groups.append(current)
            for seg_list in groups:
                text = "\x00".join(seg_list)
                body.append("<p>" + inline(text).replace("\x00", "<br>") + "</p>")
            continue
        close_quote()

        # lists
        m_ul = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        m_ol = re.match(r"^(\s*)(\d+)[.)]\s+(.*)$", line)
        if m_ul or m_ol:
            flush_para()
            tag = "ul" if m_ul else "ol"
            item = (m_ul or m_ol).group(2 if m_ul else 3)
            if list_tag != tag:
                close_list()
                list_tag, list_items = tag, []
            list_items.append(item)
            i += 1
            continue

        # blank line
        if LINE_RE.match(line):
            flush_para()
            close_list()
            i += 1
            continue

        # list-item continuation / paragraph text
        if list_tag is not None:
            list_items[-1] = list_items[-1] + " " + line.strip()
            i += 1
            continue

        # plain paragraph text
        para.append(line.strip())
        i += 1

    flush_para()
    close_list()
    close_quote()
    return front, "\n".join(body)


# ---------------------------------------------------------------------------
# Page assembly
# ---------------------------------------------------------------------------

NAV = (
    '<nav class="site-nav">{nav}</nav>'
)


def page_html(title, rel_prefix, body, worksheet=False):
    nav_links = [
        (rel_prefix + "index.html", "Start Here"),
        (rel_prefix + "08-worksheets.html", "Worksheets"),
        (rel_prefix + "09-glossary.html", "Glossary"),
        (rel_prefix + "disclaimer.html", "Disclaimer"),
    ]
    nav = " \u00b7 ".join('<a href="%s">%s</a>' % (h, t) for h, t in nav_links)
    cls = "worksheet" if worksheet else "doc"
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s - %s</title>\n"
        '<link rel="stylesheet" href="%sstyles.css">\n'
        "</head>\n"
        '<body class="%s">\n'
        '<header class="site-header"><a class="site-title" href="%sindex.html">%s</a>%s</header>\n'
        "<main>\n%s\n</main>\n"
        '<footer class="site-footer"><p>%s</p></footer>\n'
        "</body>\n</html>\n"
    ) % (
        html.escape(title),
        html.escape(SITE_TITLE),
        rel_prefix,
        cls,
        rel_prefix,
        html.escape(SITE_TITLE),
        NAV.format(nav=nav),
        body,
        html.escape(FOOTER_NOTE),
    )


def rel_prefix_for(path):
    """Prefix for links from this page to site root ('' for root pages)."""
    return "" if path.parent == Path(".") else "../"


def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "worksheets").mkdir(parents=True)

    styles = ASSETS / "styles.css"
    shutil.copy(styles, SITE / "styles.css")

    pages = []
    for md_path in sorted(DOCS.glob("*.md")):
        pages.append(("docs", md_path, "index" if md_path.name == "index.md" else None))
    for md_path in sorted(WORKSHEETS.glob("*.md")):
        pages.append(("worksheets", md_path, None))

    for src, md_path, _ in pages:
        front, body = parse_markdown(md_path.read_text(encoding="utf-8"))
        out_path = Path(md_path.stem + ".html")
        if md_path.parent == DOCS:
            site_path = out_path
        else:
            site_path = Path("worksheets") / out_path
        title = md_path.stem
        h1 = re.search(r"^#\s+(.+)$", md_path.read_text(encoding="utf-8"), re.M)
        if h1:
            title = h1.group(1)
        prefix = rel_prefix_for(site_path)
        worksheet = front.get("worksheet", "").lower() == "true"
        rendered = page_html(title, prefix, body, worksheet=worksheet)
        (SITE / site_path).write_text(rendered, encoding="utf-8")

    print("Built %d pages into %s" % (len(pages), SITE))


def main(argv=None):
    try:
        build()
    except Exception as exc:  # pragma: no cover - surfaced via exit code
        print("BUILD FAILED: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

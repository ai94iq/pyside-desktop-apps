"""Checks the skill's own files. Run exactly: python scripts/check_skill.py

- SKILL.md: frontmatter name (<= 64 chars, lowercase, digits, hyphens) and description (<= 1024 chars);
  body under 500 lines.
- Every references/*.md is linked from SKILL.md (one level deep).
- Every markdown file over 100 lines has a "## Contents" list near its top.
- Every relative markdown link resolves.
- Text files are plain ASCII (no em/en dashes, arrows, emoji).
- No words from another domain or employer leak in (BANNED).
Exit code 0 when all pass; each failure is printed as "FAIL <file>: <problem>".
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "build", "dist", ".venv"}
TEXT = (".md", ".py", ".toml", ".yml", ".yaml", ".spec", ".txt", ".cfg", ".gitignore", ".gitattributes")
BODY_MAX = 500          # Anthropic's skill guidance: SKILL.md body under 500 lines
CONTENTS_OVER = 100     # docs longer than this open with a Contents list
CONTENTS_WITHIN = 25    # ... within this many lines of the top
# Stored scrambled so this file does not match itself when grepped.
BANNED = [w[::-1] for w in ("orteam", "tobor", "bda", "ypcrcs", "elibom", "dlcle", "dawor", "qihdr")]


def files():
    for top, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            yield os.path.join(top, name)


def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def check_skill_md(fail):
    path = os.path.join(ROOT, "SKILL.md")
    if not os.path.exists(path):
        return fail("SKILL.md", "missing")
    text = open(path, encoding="utf-8").read()
    match = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not match:
        return fail("SKILL.md", "no frontmatter")
    front, body = match.groups()
    name = re.search(r"^name: (.+)$", front, re.M)
    if not name or not re.fullmatch(r"[a-z0-9-]{1,64}", name.group(1).strip()):
        fail("SKILL.md", "name must be 1-64 lowercase letters, digits or hyphens")
    desc = re.search(r"^description: (.+?)(?=^\w+:|\Z)", front, re.M | re.S)
    if not desc or len(" ".join(desc.group(1).split())) > 1024:
        fail("SKILL.md", "description missing or over 1024 characters")
    lines = body.count("\n")
    if lines >= BODY_MAX:
        fail("SKILL.md", f"body has {lines} lines, budget {BODY_MAX}")
    for ref in sorted(os.listdir(os.path.join(ROOT, "references"))):
        if ref.endswith(".md") and f"references/{ref}" not in body:
            fail("SKILL.md", f"does not link references/{ref}")


def check_markdown(path, text, fail):
    lines = text.splitlines()
    if len(lines) > CONTENTS_OVER and "## Contents" not in lines[:CONTENTS_WITHIN]:
        fail(rel(path), f"{len(lines)} lines but no '## Contents' in the first {CONTENTS_WITHIN}")
    for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text):
        if "://" in target or target.startswith("mailto:"):
            continue
        if not os.path.exists(os.path.join(os.path.dirname(path), target)):
            fail(rel(path), f"broken link {target}")


def main():
    failures = []

    def fail(where, problem):
        failures.append(f"FAIL {where}: {problem}")

    check_skill_md(fail)
    banned = re.compile(r"\b(%s)\b" % "|".join(BANNED), re.I)
    for path in files():
        if not path.endswith(TEXT) and os.path.basename(path) not in ("LICENSE",):
            continue
        text = open(path, encoding="utf-8", errors="replace").read()
        for no, line in enumerate(text.splitlines(), 1):
            bad = [c for c in line if ord(c) > 126 or (ord(c) < 32 and c != "\t")]
            if bad:
                fail(f"{rel(path)}:{no}", f"non-ASCII {bad[0]!r}")
            hit = banned.search(line)
            if hit:
                fail(f"{rel(path)}:{no}", f"banned word {hit.group(0)!r}")
        if path.endswith(".md"):
            check_markdown(path, text, fail)
    for line in failures:
        print(line)
    print("ok" if not failures else f"{len(failures)} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

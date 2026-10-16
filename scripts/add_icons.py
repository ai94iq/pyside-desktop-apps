"""Adds Lucide icons to a project's vendored icon file. Run exactly:

    python scripts/add_icons.py NAME [NAME ...] [--file src/<package>/lucide.py]

NAME is a Lucide icon name as listed on https://lucide.dev/icons (for example list, settings, folder-open).
The newest lucide-static release is looked up live on jsDelivr; when it is newer than the file's
LUCIDE_VERSION, every icon already in the file is fetched again too, so the file holds one version only.
The license header at the top of the file is kept as it is. Standard library only.
"""
import argparse
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request

RESOLVE = "https://data.jsdelivr.com/v1/packages/npm/lucide-static/resolved?specifier=latest"
ICON_URL = "https://cdn.jsdelivr.net/npm/lucide-static@{version}/icons/{name}.svg"
TIMEOUT = 20            # seconds per request; jsDelivr answers in well under one


def fetch(url):
    with urllib.request.urlopen(url, timeout=TIMEOUT) as answer:
        return answer.read().decode("utf-8")


def svg_body(svg):
    """The shapes inside <svg ...>...</svg> on one line, which is how the file stores them."""
    match = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S)
    if not match:
        raise ValueError("no <svg> element")
    return " ".join(part.strip() for part in match.group(1).strip().splitlines() if part.strip())


def read_icons(text):
    block = re.search(r"^ICONS = \{\n(.*?)^\}", text, re.M | re.S)
    if not block:
        raise SystemExit("No 'ICONS = {' block in the file.")
    icons = dict(re.findall(r'^    "([a-z0-9-]+)": \(\'(.*)\'\),$', block.group(1), re.M))
    return block, icons


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("names", nargs="+")
    parser.add_argument("--file", help="the lucide.py to update (default: the only src/*/lucide.py here)")
    args = parser.parse_args(argv)
    path = args.file or next(iter(glob.glob(os.path.join("src", "*", "lucide.py"))), None)
    if not path or not os.path.exists(path):
        raise SystemExit("No lucide.py found: run from the project root or pass --file.")
    text = open(path, encoding="utf-8").read()
    old = re.search(r'^LUCIDE_VERSION = "([^"]+)"', text, re.M).group(1)
    block, icons = read_icons(text)
    try:
        version = json.loads(fetch(RESOLVE))["version"]
    except (urllib.error.URLError, KeyError, ValueError) as err:
        raise SystemExit(f"Could not look up the latest lucide-static on jsDelivr: {err}")
    wanted = sorted(set(args.names) | (set(icons) if version != old else set()))
    missing = []
    for name in wanted:
        if not re.fullmatch(r"[a-z0-9-]+", name):
            missing.append(name)
            continue
        try:
            icons[name] = svg_body(fetch(ICON_URL.format(version=version, name=name)))
        except (urllib.error.URLError, ValueError):
            missing.append(name)
    if missing:
        raise SystemExit(f"Not in lucide-static {version}: {', '.join(missing)} (nothing was written). "
                         "Check the names on https://lucide.dev/icons")
    lines = "".join(f"    \"{name}\": ('{body}'),\n" for name, body in sorted(icons.items()))
    text = text[:block.start()] + "ICONS = {\n" + lines + text[block.end() - 1:]
    text = re.sub(r'^LUCIDE_VERSION = "[^"]+"', f'LUCIDE_VERSION = "{version}"', text, flags=re.M)
    text = re.sub(r"lucide-static version [0-9.]+", f"lucide-static version {version}", text)
    with open(path, "w", encoding="utf-8", newline="\n") as out:
        out.write(text)
    note = f" (upgraded from {old}: every icon refetched)" if version != old else ""
    print(f"{path}: {len(icons)} icons at lucide-static {version}{note}; added {', '.join(sorted(args.names))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

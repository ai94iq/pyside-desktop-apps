"""Creates a new PySide6 desktop app from assets/template. Run exactly:

    python scripts/new_project.py "App Name" DEST [--package name] [--no-test]

"App Name" is what users see (window title, bundle name). The Python package defaults to the name in
lower case with underscores (App Name -> app_name); the bundle file name to its CamelCase (AppName).
DEST must not exist or must be empty. The script copies the template, fills the placeholders, runs
`git init -b main` and the tests offscreen, then prints the next steps. It makes no commit, so the
project's own git identity is used for the first one. Standard library only (the tests need PySide6).
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(SKILL, "assets", "template")
TEXT = (".py", ".md", ".toml", ".yml", ".spec", ".txt", ".gitignore", ".gitattributes", "LICENSE")


def names(display, package=None):
    words = re.findall(r"[A-Za-z0-9]+", display)
    if not words:
        raise SystemExit("The app name needs at least one letter or digit.")
    package = package or "_".join(w.lower() for w in words)
    if not package.isidentifier() or package[0].isdigit():
        raise SystemExit(f"{package!r} is not a valid Python package name; pass --package.")
    camel = "".join(w[:1].upper() + w[1:] for w in words)
    # Longest placeholder first: "__App Name__" and "__App__" both start with "__App".
    return [("__App Name__", display), ("__App__", camel), ("__app__", package)]


def fill(text, pairs):
    for old, new in pairs:
        text = text.replace(old, new)
    return text


def copy(dest, pairs):
    for top, dirs, files in os.walk(TEMPLATE):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".pytest_cache")]
        target_dir = os.path.join(dest, fill(os.path.relpath(top, TEMPLATE), pairs))
        os.makedirs(target_dir, exist_ok=True)
        for name in files:
            source, target = os.path.join(top, name), os.path.join(target_dir, fill(name, pairs))
            if name.endswith(TEXT):
                with open(source, encoding="utf-8") as src, open(target, "w", encoding="utf-8", newline="\n") as out:
                    out.write(fill(src.read(), pairs))
            else:
                shutil.copy2(source, target)


def run_tests(dest):
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONPATH=os.path.join(dest, "src"))
    return subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"], cwd=dest,
                          env=env).returncode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name")
    parser.add_argument("dest")
    parser.add_argument("--package")
    parser.add_argument("--no-test", action="store_true", help="skip the test run (no PySide6 here)")
    args = parser.parse_args(argv)
    dest = os.path.abspath(args.dest)
    if os.path.exists(dest) and os.listdir(dest):
        raise SystemExit(f"{dest} exists and is not empty; nothing was written.")
    pairs = names(args.name, args.package)
    copy(dest, pairs)
    if shutil.which("git"):
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=dest, check=True)
    package = pairs[2][1]
    if not args.no_test and run_tests(dest):
        print(f"\nCreated {dest}, but its tests FAILED (output above).", file=sys.stderr)
        return 1
    print(f"\nCreated {dest} (package {package}).\nNext:\n  cd \"{dest}\"\n  python -m pip install -e .[dev]\n"
          f"  python -m {package}\n  python -m {package} --screenshots tmp/screens   (light and dark for review)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

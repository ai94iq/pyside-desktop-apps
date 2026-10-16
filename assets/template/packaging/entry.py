"""Entry point of the desktop bundles (PyInstaller): the same as python -m __app__."""
import sys

from __app__.__main__ import main

if __name__ == "__main__":
    sys.exit(main())

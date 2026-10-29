#!/usr/bin/env python3
"""
Wine Tasting Notes - GNOME Application Entry Point.

Note: The experimental Flask web app and terminal CLI scripts have been
safely backed up under the `legacy/` directory:
- `legacy/flask_app.py`
- `legacy/simple_cli.py`
- `legacy/templates/`
"""

import sys
from winenotes.app import main

if __name__ == "__main__":
    sys.exit(main())
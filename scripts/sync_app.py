"""Sync source modules into the app/ deployment bundle.

Copies the modules the Gradio Space actually imports from src/ into app/,
prepending a generated-file header so nobody edits the copies by hand.

Run this before every push to Hugging Face Spaces:

    python scripts/sync_app.py
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
APP_DIR = REPO_ROOT / "app"

# Only the modules the rules path actually needs. Adding the transformer or
# LLM lanes to app/ would also pull their heavy dependencies into the Space.
MODULES = ["sectionizer.py", "rules_extractor.py"]

HEADER = """# ---------------------------------------------------------------------------
# GENERATED FILE — do not edit here.
# This module is copied from ../src/{name} by scripts/sync_app.py so the
# Hugging Face Space bundle in app/ stays a flat, self-contained deployment.
# Edit the original in src/ and re-run: python scripts/sync_app.py
# ---------------------------------------------------------------------------
"""


def sync() -> list[str]:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in MODULES:
        src = SRC_DIR / name
        if not src.exists():
            raise FileNotFoundError(f"missing source module: {src}")
        dst = APP_DIR / name
        dst.write_text(HEADER.format(name=name) + src.read_text())
        copied.append(str(dst.relative_to(REPO_ROOT)))
    return copied


if __name__ == "__main__":
    copied = sync()
    print(f"Synced {len(copied)} module(s) from src/ into app/:")
    for path in copied:
        print(f"  {path}")

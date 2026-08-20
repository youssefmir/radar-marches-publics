"""Vérifie que tous les liens et images relatifs des fichiers Markdown pointent vers un fichier existant.

Usage : python scripts/check_links.py  (code de sortie 1 si un lien est cassé)
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SKIP = ("http://", "https://", "mailto:")


def slug(title: str) -> str:
    """Ancre à la manière de GitHub : minuscules, sans ponctuation, espaces -> tirets."""
    t = title.strip().lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return t.replace(" ", "-")


def anchors(md: Path) -> set[str]:
    text = md.read_text(encoding="utf-8")
    titres = {slug(m.group(1)) for m in re.finditer(r"^#{1,6}\s+(.+)$", text, re.M)}
    return titres | set(re.findall(r'<a id="([^"]+)"', text))


def main() -> int:
    errors = []
    files = [p for p in ROOT.rglob("*.md") if not any(x in p.parts for x in ("node_modules", ".venv", "dbt_packages", "target"))]
    for md in files:
        text = re.sub(r"```.*?```", "", md.read_text(encoding="utf-8"), flags=re.S)
        for target in LINK.findall(text):
            if target.startswith(SKIP):
                continue
            path, _, anchor = target.partition("#")
            dest = (md.parent / path).resolve() if path else md
            if not dest.exists():
                errors.append(f"{md.relative_to(ROOT)} -> {target} (fichier absent)")
            elif anchor and dest.suffix == ".md" and unicodedata.normalize("NFC", anchor) not in anchors(dest):
                errors.append(f"{md.relative_to(ROOT)} -> {target} (ancre absente)")
    for e in errors:
        print("LIEN CASSÉ :", e)
    print(f"{len(files)} fichiers Markdown vérifiés, {len(errors)} lien(s) cassé(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

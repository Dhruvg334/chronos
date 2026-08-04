from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PATTERNS = [
    re.compile(r"gsk_[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)(service[_-]?role[_-]?key|client[_-]?secret)\s*[:=]\s*['\"][^'\"]{12,}"),
]
ALLOW = {".env.example", "secret_scan.py"}

files = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard"], text=True).splitlines()
findings = []
for name in files:
    path = Path(name)
    if path.name in ALLOW or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".pdf", ".ico"}:
        continue
    try: text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError): continue
    if any(pattern.search(text) for pattern in PATTERNS): findings.append(name)
if findings:
    print("Potential committed secrets:", ", ".join(findings))
    sys.exit(1)
print(f"Secret scan passed ({len(files)} repository files checked).")

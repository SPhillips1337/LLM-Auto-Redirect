#!/usr/bin/env python3
# bootstrap-validate.py
# Validate an initialized project's local coordination scripts.
#
# Usage:
#   python3 bootstrap-validate.py
#
# Expected files relative to the project root:
#   scripts/tasks.py
#   scripts/lock.py
#   scripts/unlock.py
#   scripts/heartbeat.py
#   scripts/force-unlock.py
#   scripts/cleanup.py
#   scripts/update-status.py
#   scripts/init.py

from pathlib import Path

REQUIRED = [
    "tasks.py",
    "lock.py",
    "unlock.py",
    "heartbeat.py",
    "force-unlock.py",
    "cleanup.py",
    "update-status.py",
    "init.py",
]

SCRIPTS = Path("scripts")
missing = [name for name in REQUIRED if not (SCRIPTS / name).exists()]

if missing:
    print("❌ Missing coordination scripts:")
    for name in missing:
        print(f"   scripts/{name}")
    raise SystemExit(1)

print("✅ Local coordination scripts present:")
for name in REQUIRED:
    print(f"   scripts/{name}")
print("\nNext: use python3 scripts/tasks.py to manage work.")

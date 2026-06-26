#!/usr/bin/env python3
# Initialize multi-agent coordination in current directory
# Usage: python3 init.py

import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

MANIFEST = ".agent-manifest.json"
STATUS = ".agent-status.md"

SOURCE_DIR = Path(__file__).resolve().parent


def main() -> None:
    if Path(MANIFEST).exists():
        print(f"Manifest already exists at {MANIFEST}")
        with open(MANIFEST) as f:
            print(f.read())
        return

    manifest = {"version": "1.0", "locks": {}, "agents": {}}
    Path(MANIFEST).write_text(json.dumps(manifest, indent=2))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    status_content = f"""# Agent Coordination Status

*Initialized: {now}*

## Active Locks

*No active locks*

## Registered Agents

*No agents registered*

---

*This file is auto-generated. Do not edit manually — use the lock/unlock scripts.*
"""
    Path(STATUS).write_text(status_content)

    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)

    local_scripts = [
        "tasks.py",
        "lock.py",
        "unlock.py",
        "heartbeat.py",
        "force-unlock.py",
        "cleanup.py",
        "update-status.py",
        "bootstrap-validate.py",
    ]
    for name in local_scripts:
        src = SOURCE_DIR / name
        dst = scripts_dir / name
        if src.exists():
            shutil.copy2(src, dst)

    print("Initialized coordination system:")
    print(f"  {MANIFEST} (machine-readable)")
    print(f"  {STATUS} (human-readable)")
    print(f"  {scripts_dir}/ (local coordination scripts)")
    print()
    print("Add this to your AGENTS.md:")
    print("  cat /home/stephen/.hermes/skills/devops/multi-agent-coordination/templates/AGENTS.md.coordination >> AGENTS.md")


if __name__ == "__main__":
    main()

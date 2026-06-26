#!/usr/bin/env python3
# Clean up all stale locks
# Usage: ./cleanup.py [threshold_seconds]

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

MANIFEST = ".agent-manifest.json"
SESSION_FILE = ".agent-session.json"

def load_manifest():
    if not Path(MANIFEST).exists():
        return {"version": "1.0", "locks": {}, "agents": {}}
    with open(MANIFEST) as f:
        return json.load(f)

def save_manifest(data):
    with open(MANIFEST + ".tmp", "w") as f:
        json.dump(data, f, indent=2)
    os.replace(MANIFEST + ".tmp", MANIFEST)

def parse_iso(ts):
    if ts.endswith('Z'):
        ts = ts[:-1] + '+00:00'
    return datetime.fromisoformat(ts)

def main():
    threshold = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    manifest = load_manifest()
    now = datetime.now(timezone.utc)

    # Remove stale locks
    stale_files = []
    for file, lock in list(manifest.get("locks", {}).items()):
        hb_str = lock.get("heartbeat")
        if not hb_str:
            stale_files.append((file, "no heartbeat"))
            continue
        hb = parse_iso(hb_str)
        age = (now - hb).total_seconds()
        if age > threshold:
            stale_files.append((file, f"{int(age)}s old"))

    for file, reason in stale_files:
        print(f"🧹 Removing stale lock: {file} ({reason})")
        del manifest["locks"][file]

    # Remove agents with no locks
    active_agents = set(lock["agent_id"] for lock in manifest.get("locks", {}).values())
    for agent_id in list(manifest.get("agents", {}).keys()):
        if agent_id not in active_agents:
            print(f"🧹 Removing inactive agent: {agent_id}")
            del manifest["agents"][agent_id]

    save_manifest(manifest)
    # Update human-readable status
    import subprocess
    script_dir = Path(__file__).parent
    subprocess.run([sys.executable, script_dir / "update-status.py"], capture_output=True)
    print(f"Cleanup complete. Threshold: {threshold}s")

if __name__ == "__main__":
    main()
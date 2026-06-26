#!/usr/bin/env python3
# Force-release a stale lock (use with caution!)
# Usage: ./force-unlock.py <file1> [file2...]

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

MANIFEST = ".agent-manifest.json"
SESSION_FILE = ".agent-session.json"
STALE_THRESHOLD = 600  # 10 minutes

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
    # Handle both with and without Z
    if ts.endswith('Z'):
        ts = ts[:-1] + '+00:00'
    return datetime.fromisoformat(ts)

def main():
    if len(sys.argv) < 2:
        print("Usage: force-unlock.py <file1> [file2...]")
        sys.exit(1)

    files = [os.path.relpath(f) for f in sys.argv[1:]]
    manifest = load_manifest()
    now = datetime.now(timezone.utc)

    for file in files:
        if file not in manifest["locks"]:
            print(f"⚠️  Not locked: {file}")
            continue

        lock = manifest["locks"][file]
        hb_str = lock.get("heartbeat")
        if not hb_str:
            print(f"⚠️  No heartbeat data for {file}, forcing unlock")
            del manifest["locks"][file]
            print(f"🔓 Force-unlocked: {file} (no heartbeat)")
            continue

        hb = parse_iso(hb_str)
        age = (now - hb).total_seconds()

        if age < STALE_THRESHOLD:
            print(f"❌ Lock not stale: {file} (last heartbeat {int(age)}s ago, threshold {STALE_THRESHOLD}s)")
            print(f"   Owner: {lock['agent_id']}")
            sys.exit(1)

        print(f"⚠️  Stale lock detected: {file} ({int(age)}s since heartbeat)")
        print(f"   Owner: {lock['agent_id']}")
        del manifest["locks"][file]
        print(f"🔓 Force-unlocked: {file} (stale)")

    save_manifest(manifest)
    # Update human-readable status
    import subprocess
    script_dir = Path(__file__).parent
    subprocess.run([sys.executable, script_dir / "update-status.py"], capture_output=True)

if __name__ == "__main__":
    main()
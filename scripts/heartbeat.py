#!/usr/bin/env python3
# Update heartbeat for active lock
# Usage: ./heartbeat.py <file1> [file2...]

import json
import sys
import os
import socket
import random
from datetime import datetime, timezone
from pathlib import Path

MANIFEST = ".agent-manifest.json"
SESSION_FILE = ".agent-session.json"

def get_agent_id():
    if "AGENT_ID" in os.environ:
        return os.environ["AGENT_ID"]
    if Path(SESSION_FILE).exists():
        try:
            with open(SESSION_FILE) as f:
                data = json.load(f)
                return data.get("agent_id")
        except Exception:
            pass
    agent_id = get_agent_id()
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump({"agent_id": agent_id}, f)
    except Exception:
        pass
    return agent_id

def load_manifest():
    if not Path(MANIFEST).exists():
        return {"version": "1.0", "locks": {}, "agents": {}}
    with open(MANIFEST) as f:
        return json.load(f)

def save_manifest(data):
    with open(MANIFEST + ".tmp", "w") as f:
        json.dump(data, f, indent=2)
    os.replace(MANIFEST + ".tmp", MANIFEST)

def main():
    if len(sys.argv) < 2:
        print("Usage: heartbeat.py <file1> [file2...]")
        sys.exit(1)

    files = [os.path.relpath(f) for f in sys.argv[1:]]
    agent_id = get_agent_id()
    heartbeat = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    manifest = load_manifest()

    for file in files:
        if file not in manifest["locks"]:
            print(f"❌ Not locked: {file}")
            sys.exit(1)

        locked_by = manifest["locks"][file]["agent_id"]
        if locked_by != agent_id:
            print(f"❌ Not your lock: {file} (owned by {locked_by})")
            sys.exit(1)

        manifest["locks"][file]["heartbeat"] = heartbeat
        manifest["agents"][agent_id]["last_heartbeat"] = heartbeat
        print(f"💓 Heartbeat: {file}")

    save_manifest(manifest)
    # Update human-readable status
    import subprocess
    script_dir = Path(__file__).parent
    subprocess.run([sys.executable, script_dir / "update-status.py"], capture_output=True)

if __name__ == "__main__":
    main()